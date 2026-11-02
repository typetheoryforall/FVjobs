#!/usr/bin/env python3
"""Re-check whether every role in data/jobs.yml is still open.

    python3 scripts/recheck.py check [--json report.json] [--only FV-001,FV-002]

asks each posting's ATS API where there is one (Ashby, Lever, Greenhouse,
Workday, Personio, Workable, Eightfold, Jibe, Mercor, Alignerr) and reports
OPEN or CLOSED. Everything else, and any API answer that is not conclusive, is
CHECK: a person (or Claude) has to read the page, so the report carries a hint
(HTTP status, redirect, "no longer accepting", a deadline) to start from.

    python3 scripts/recheck.py apply --open FV-001,FV-002 --closed FV-003

then sets `last_verified` to today on the open roles and moves the closed ones
to data/archive.yml with a `closed` date, keeping their IDs. Both files are
edited as text, so comments and formatting are left alone.
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
JOBS = ROOT / "data" / "jobs.yml"
ARCHIVE = ROOT / "data" / "archive.yml"
UA = "Mozilla/5.0 (compatible; FVjobs link checker)"
TIMEOUT = 25
# Seconds between requests to the same host. Workable and Microsoft rate-limit
# hard (see docs/search-playbook.md); everyone else gets a polite pause.
DELAY = {"apply.workable.com": 6, "apply.careers.microsoft.com": 5}
DEFAULT_DELAY = 1

# Searched in the visible text only: Apple and JOIN ship "no longer available"
# in translation strings on every page, and "until the position is filled" is
# how many open academic posts describe their deadline.
CLOSED_PHRASES = re.compile(
    r"no longer (?:accepting|available|open|active)|(?<!until the )position (?:has been|is) (?:filled|closed)"
    r"|job (?:not found|is closed|has expired|has been closed)|this (?:job|role|vacancy|posting) "
    r"(?:is|has) (?:closed|expired)|applications? (?:are|is) (?:now )?closed|vacancy (?:is )?closed",
    re.I)
DEADLINE = re.compile(
    r"(?:deadline|closing date|apply by|applications? (?:close|due)|until)[^.\n]{0,60}?"
    r"(\d{1,2}(?:st|nd|rd|th)? (?:of )?[A-Z][a-z]+,? \d{4}|[A-Z][a-z]+ \d{1,2},? \d{4}|\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}[./]\d{1,2}[./]\d{4})", re.I)

OPEN, CLOSED, CHECK = "OPEN", "CLOSED", "CHECK"


class Fetcher:
    """HTTP with a per-host pause, so one slow board doesn't trip a rate limit."""

    def __init__(self):
        self.last = defaultdict(float)

    def get(self, url, data=None, headers=None):
        host = urllib.parse.urlsplit(url).netloc
        wait = self.last[host] + DELAY.get(host, DEFAULT_DELAY) - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self.last[host] = time.monotonic()
        body = json.dumps(data).encode() if data is not None else None
        req = urllib.request.Request(url, data=body, headers={"User-Agent": UA, **(headers or {})})
        if body is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.status, r.geturl(), r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, url, e.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001 - report whatever went wrong
            return None, url, str(e)[:120]


def ashby(f, u):
    org, job = u.path.strip("/").split("/")[:2]
    s, _, body = f.get(f"https://api.ashbyhq.com/posting-api/job-board/{org}")
    if s != 200:
        return CHECK, f"Ashby board {org}: HTTP {s}"
    if job in {j.get("id") for j in json.loads(body).get("jobs", [])}:
        return OPEN, "listed on the Ashby board"
    # Unlisted postings drop off the board but stay reachable; only a null
    # jobPosting proves the role is gone.
    query = ("query ApiJobPosting($organizationHostedJobsPageName: String!, $jobPostingId: String!) "
             "{ jobPosting(organizationHostedJobsPageName: $organizationHostedJobsPageName, "
             "jobPostingId: $jobPostingId) { id } }")
    s, _, body = f.get("https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobPosting", data={
        "operationName": "ApiJobPosting", "query": query,
        "variables": {"organizationHostedJobsPageName": org, "jobPostingId": job}})
    if s == 200 and json.loads(body).get("data", {}).get("jobPosting") is None:
        return CLOSED, f"not on Ashby board {org}, and the posting API returns null"
    return CHECK, f"not on Ashby board {org} but the posting still resolves (unlisted?)"


def lever(f, u):
    org, job = u.path.strip("/").split("/")[:2]
    api = "api.eu.lever.co" if u.netloc.startswith("jobs.eu.") else "api.lever.co"
    s, _, _ = f.get(f"https://{api}/v0/postings/{org}/{job}")
    return {200: (OPEN, "Lever posting API 200"), 404: (CLOSED, "Lever posting API 404")}.get(
        s, (CHECK, f"Lever posting API: HTTP {s}"))


# Careers sites that front a Greenhouse board with ?gh_jid=.
GREENHOUSE_BOARDS = {"careers.withwaymo.com": "waymo"}


def greenhouse(f, u):
    if u.netloc in GREENHOUSE_BOARDS:
        org, job = GREENHOUSE_BOARDS[u.netloc], urllib.parse.parse_qs(u.query)["gh_jid"][0]
    else:
        parts = u.path.strip("/").split("/")
        org, job = parts[0], parts[-1]
    s, _, _ = f.get(f"https://boards-api.greenhouse.io/v1/boards/{org}/jobs/{job}")
    return {200: (OPEN, "Greenhouse job API 200"), 404: (CLOSED, "Greenhouse job API 404")}.get(
        s, (CHECK, f"Greenhouse job API: HTTP {s}"))


def workday(f, u):
    tenant = u.netloc.split(".")[0]
    parts = [p for p in u.path.split("/") if p]
    if parts and re.fullmatch(r"[a-z]{2}-[A-Z]{2}", parts[0]):
        parts = parts[1:]
    if "job" not in parts:
        return CHECK, "unrecognised Workday URL"
    site, path = parts[0], "/".join(parts[parts.index("job"):])
    s, _, body = f.get(f"https://{u.netloc}/wday/cxs/{tenant}/{site}/{path}")
    if s == 404:
        return CLOSED, "Workday job API 404"
    if s != 200:
        return CHECK, f"Workday job API: HTTP {s}"
    info = json.loads(body).get("jobPostingInfo", {})
    if info.get("canApply") is False:
        return CLOSED, "Workday canApply is false"
    return OPEN, "Workday canApply is true"


def personio(f, u):
    job = u.path.rstrip("/").split("/")[-1]
    s, _, body = f.get(f"https://{u.netloc}/xml?language=en")
    if s != 200:
        return CHECK, f"Personio feed: HTTP {s}"
    found = re.search(rf"<id>{re.escape(job)}</id>", body)
    return (OPEN, "listed in the Personio feed") if found else (CLOSED, "not in the Personio feed")


def workable(f, u):
    parts = u.path.strip("/").split("/")
    if len(parts) < 3 or parts[1] != "j":
        return CHECK, "Workable board page, not a single posting"
    s, _, _ = f.get(f"https://apply.workable.com/api/v2/accounts/{parts[0]}/jobs/{parts[2]}")
    return {200: (OPEN, "Workable job API 200"), 404: (CLOSED, "Workable job API 404")}.get(
        s, (CHECK, f"Workable job API: HTTP {s} (rate limit? check by hand)"))


def eightfold(f, u):
    job = re.search(r"/job/(\d+)", u.path)
    if not job:
        return CHECK, "unrecognised Eightfold URL"
    domain = "microsoft.com" if "microsoft" in u.netloc else "qualcomm.com"
    s, _, _ = f.get(
        f"https://{u.netloc}/api/pcsx/position_details?position_id={job[1]}&domain={domain}&hl=en",
        headers={"Referer": f"https://{u.netloc}/careers?domain={domain}"})
    return {200: (OPEN, "Eightfold position found"), 404: (CLOSED, "Eightfold: position not found")}.get(
        s, (CHECK, f"Eightfold API: HTTP {s}"))


def jibe(f, u):
    job = re.search(r"/jobs/(\d+)", u.path)
    if not job:
        return CHECK, "unrecognised Jibe URL"
    s, _, body = f.get(f"https://{u.netloc}/api/jobs?keywords={job[1]}&limit=20")
    if s != 200:
        return CHECK, f"Jibe search: HTTP {s}"
    found = json.loads(body).get("jobs", [])
    if job[1] in {j["data"].get("slug") for j in found}:
        return OPEN, "found by Jibe search"
    return (CLOSED, "Jibe search no longer finds it") if not found else (CHECK, "Jibe search ambiguous")


def mercor(f, u):
    s, _, body = f.get(u.geturl())
    m = re.search(r'\\?"status\\?":\\?"(\w+)', body)
    if s != 200 or not m:
        return CHECK, f"Mercor page: HTTP {s}, no status field"
    return (OPEN, "Mercor status active") if m[1] == "active" else (CLOSED, f"Mercor status {m[1]}")


def alignerr(f, u):
    s, _, body = f.get(u.geturl())
    m = re.search(r'\\?"isActive\\?":(true|false)', body)
    if s != 200 or not m:
        return CHECK, f"Alignerr page: HTTP {s}, no isActive field"
    return (OPEN, "Alignerr isActive") if m[1] == "true" else (CLOSED, "Alignerr isActive is false")


def visible(body):
    body = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", body)
    return " ".join(re.sub(r"<[^>]+>", " ", body).split())


def moved(u, final):
    v = urllib.parse.urlsplit(final)
    return v.netloc != u.netloc or v.path.rstrip("/") != u.path.rstrip("/")


def google(f, u):
    s, _, body = f.get(u.geturl())
    if s == 200 and "Job not found" in body:
        return CLOSED, 'Google: "Job not found"'
    if s == 200 and ">Apply<" in body:
        return OPEN, "Google posting shows Apply"
    return CHECK, f"Google page: HTTP {s}, neither Apply nor not-found"


def apple(f, u):
    s, _, body = f.get(u.geturl())
    if s == 200 and '\\"postingTitle\\"' in body:
        return OPEN, "Apple posting data present"
    return CHECK, f"Apple page: HTTP {s}, no posting data (probably closed)"


def amazon(f, u):
    s, final, body = f.get(u.geturl())
    if s == 404:
        return CLOSED, "amazon.jobs 404"
    if s == 200 and not moved(u, final) and "Apply now" in body:
        return OPEN, "amazon.jobs posting shows Apply now"
    return CHECK, f"amazon.jobs: HTTP {s}" + (f", redirected to {final}" if moved(u, final) else "")


def talentbrew(f, u, role):
    """Arm and Synopsys: closed jobs 404 or redirect home, and Arm reuses IDs."""
    s, final, body = f.get(u.geturl())
    if s == 404 or (s == 200 and urllib.parse.urlsplit(final).path in ("", "/")):
        return CLOSED, f"HTTP {s}, {'redirected home' if s == 200 else 'not found'}"
    if s == 200 and role.lower() in visible(body).lower():
        return OPEN, "posting page shows the role title"
    return CHECK, f"HTTP {s}, title not on the page (Arm reuses job IDs)"


def deadline_hint(text, today):
    m = DEADLINE.search(text)
    if not m:
        return None
    raw = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", m[1]).replace(" of ", " ").replace(",", "")
    for fmt in ("%d %B %Y", "%d %b %Y", "%B %d %Y", "%b %d %Y", "%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y"):
        try:
            when = dt.datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
        state = "PASSED" if when < today else "ahead"
        return f'deadline {when} {state} ("{" ".join(m[0].split())}")'
    return f'deadline? "{" ".join(m[0].split())}"'


def page(f, u, role):
    """No API: fetch the page and collect hints for whoever reads it."""
    s, final, body = f.get(u.geturl())
    if s is None:
        return CHECK, f"fetch failed: {body}"
    if s in (404, 410):
        return CHECK, f"HTTP {s}, probably closed"
    if s >= 400:
        return CHECK, f"HTTP {s} (bot check or rate limit?), read it in a browser"
    hints = []
    if moved(u, final):
        hints.append(f"redirected to {final}")
    text = visible(body)
    if m := CLOSED_PHRASES.search(text):
        hints.append(f'page says "{m[0]}"')
    if d := deadline_hint(text, dt.date.today()):
        hints.append(d)
    if not hints:
        hints.append("loads, title on the page, no closing signs" if role.lower() in text.lower()
                     else f"HTTP {s}, title not found on the page")
    return CHECK, "; ".join(hints)


def checker(host):
    if host == "jobs.ashbyhq.com":
        return ashby
    if host.endswith("lever.co"):
        return lever
    if host in ("job-boards.greenhouse.io", "boards.greenhouse.io", "job-boards.eu.greenhouse.io",
                *GREENHOUSE_BOARDS):
        return greenhouse
    if host == "www.google.com":
        return google
    if host == "jobs.apple.com":
        return apple
    if host == "www.amazon.jobs":
        return amazon
    if host in ("careers.arm.com", "careers.synopsys.com"):
        return talentbrew
    if ".myworkdayjobs.com" in host:
        return workday
    if host.endswith(".jobs.personio.de"):
        return personio
    if host == "apply.workable.com":
        return workable
    if host in ("apply.careers.microsoft.com", "careers.qualcomm.com"):
        return eightfold
    if host in ("careers.amd.com", "careers.jhuapl.edu"):
        return jibe
    if host == "work.mercor.com":
        return mercor
    if host.endswith("alignerr.com"):
        return alignerr
    return page


def check(entries):
    f = Fetcher()
    by_host = defaultdict(list)
    for e in entries:
        by_host[urllib.parse.urlsplit(e["url"]).netloc].append(e)

    def run_host(group):
        out = []
        for e in group:
            u = urllib.parse.urlsplit(e["url"])
            fn = checker(u.netloc)
            try:
                status, why = fn(f, u, e["role"]) if fn in (page, talentbrew) else fn(f, u)
            except Exception as ex:  # noqa: BLE001 - a broken answer means read it by hand
                status, why = CHECK, f"checker error: {ex}"[:160]
            out.append({"id": e["id"], "company": e["company"], "role": e["role"],
                        "url": e["url"], "last_verified": str(e["last_verified"]),
                        "status": status, "evidence": why})
        return out

    with ThreadPoolExecutor(8) as pool:
        results = [r for group in pool.map(run_host, by_host.values()) for r in group]
    order = {e["id"]: i for i, e in enumerate(entries)}
    return sorted(results, key=lambda r: order[r["id"]])


def blocks(text):
    """Split a data file into its header and one text block per entry, keyed by id."""
    parts = re.split(r"(?m)^(?=- id: )", text)
    head, out = parts[0], {}
    for part in parts[1:]:
        out[re.match(r"- id: (\S+)", part)[1]] = part
    return head, out


def apply(open_ids, closed_ids, today):
    head, jobs = blocks(JOBS.read_text(encoding="utf-8"))
    missing = [i for i in open_ids + closed_ids if i not in jobs]
    if missing:
        sys.exit(f"error: not in jobs.yml: {', '.join(missing)}")

    for i in open_ids:
        jobs[i] = re.sub(r"(?m)^  last_verified: .*$", f"  last_verified: {today}", jobs[i])

    ahead, archive = blocks(ARCHIVE.read_text(encoding="utf-8"))
    for i in closed_ids:
        block = jobs.pop(i).rstrip("\n")
        archive[i] = block + f"\n  closed: {today}\n\n"

    def company(block):
        return re.search(r"(?m)^  company: (.*)$", block)[1].strip("'\"").lower()

    def role(block):
        return re.search(r"(?m)^  role: (.*)$", block)[1].strip("'\"").lower()

    def dump(head, entries):
        text = head + "".join(b.rstrip("\n") + "\n\n" for b in entries)
        return text.rstrip("\n") + "\n"

    # jobs.yml keeps its order; archived roles slot into the archive by company.
    JOBS.write_text(dump(head, jobs.values()), encoding="utf-8")
    ARCHIVE.write_text(dump(ahead, sorted(archive.values(), key=lambda b: (company(b), role(b)))),
                       encoding="utf-8")
    print(f"verified {len(open_ids)} on {today}, archived {len(closed_ids)}")


def ids(arg):
    return [i for i in re.split(r"[,\s]+", arg or "") if i]


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="ask every posting whether it is still open")
    c.add_argument("--json", help="also write the results to this file")
    c.add_argument("--only", help="comma-separated IDs to check instead of all")
    a = sub.add_parser("apply", help="record the outcome in the data files")
    a.add_argument("--open", default="", help="IDs confirmed open: last_verified becomes today")
    a.add_argument("--closed", default="", help="IDs confirmed closed: moved to archive.yml")
    a.add_argument("--date", default=dt.date.today().isoformat(), help="date to record (default today)")
    args = p.parse_args()

    if args.cmd == "apply":
        o, c = ids(args.open), ids(args.closed)
        if set(o) & set(c):
            sys.exit(f"error: both open and closed: {', '.join(sorted(set(o) & set(c)))}")
        apply(o, c, args.date)
        return 0

    entries = yaml.safe_load(JOBS.read_text(encoding="utf-8")) or []
    if args.only:
        wanted = set(ids(args.only))
        entries = [e for e in entries if e["id"] in wanted]
    results = check(entries)
    for status in (CLOSED, CHECK, OPEN):
        rows = [r for r in results if r["status"] == status]
        print(f"\n## {status} ({len(rows)})\n")
        for r in rows:
            print(f"- {r['id']} {r['company']} — {r['role']}: {r['evidence']}\n  {r['url']}")
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
