#!/usr/bin/env python3
"""Record how the board has grown, in data/history.csv.

    python3 scripts/stats.py            # rebuild data/history.csv
    python3 scripts/stats.py --check    # fail if data/history.csv is out of date

The history is rebuilt from scratch every time, so it is always the same for
the same repository. It walks every commit on the current branch's
first-parent line that changed data/jobs.yml or data/archive.yml, loads the
two files as they were, and keeps one row per day: the board as it stood at
the end of that day. If the working tree's data differs from HEAD, today's
row comes from the working tree, so a deep search or re-check can record
itself before it is committed.

Each row counts:

- open, archived: roles in data/jobs.yml and data/archive.yml;
- tracked: open + archived, every role the board has ever listed;
- companies: distinct employers among the open roles;
- added: roles on the board or in the archive that the previous row did not
  have, so a role found and closed between two rows still counts once;
- closed: roles that moved to the archive since the previous row;
- one column per category: open roles of that kind.

The site's analytics page (scripts/site.py) draws its graphs from this file,
so the deep-search and recheck-jobs skills run this script before they
commit.
"""
import argparse
import csv
import datetime as dt
import io
import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
HISTORY = ROOT / "data" / "history.csv"
FILES = ("data/jobs.yml", "data/archive.yml")
CATEGORIES = ("hardware", "software", "ai-for-proof", "academic", "cryptocurrency")
FIELDS = ["date", "open", "archived", "tracked", "companies", "added", "closed",
          *(c.replace("-", "_") for c in CATEGORIES)]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def parse(text):
    return yaml.safe_load(text or "") or []


def at(commit, path):
    """A data file as it was at a commit, or an empty list if it did not exist yet."""
    try:
        return parse(git("show", f"{commit}:{path}"))
    except subprocess.CalledProcessError:
        return []


def key(entry):
    """Roles are matched by ID; the first commits had none, so fall back to the URL."""
    return entry.get("id") or entry["url"]


def snapshot(jobs, archive):
    return {
        "open": {key(e) for e in jobs},
        "archived": {key(e) for e in archive},
        "by_url": {e["url"]: key(e) for e in [*jobs, *archive]},
        "row": {
            "open": len(jobs),
            "archived": len(archive),
            "tracked": len(jobs) + len(archive),
            "companies": len({e["company"] for e in jobs}),
            **{c.replace("-", "_"): sum(e.get("category") == c for e in jobs) for c in CATEGORIES},
        },
    }


def rows():
    """One row per day, in date order, ending with the working tree if it has changed."""
    log = git("log", "--first-parent", "--reverse", "--format=%H %ad", "--date=short", "HEAD", "--", *FILES)
    days = {}
    for line in log.splitlines():
        commit, day = line.split()
        days[day] = snapshot(*(at(commit, f) for f in FILES))
    if git("status", "--porcelain", "--", *FILES).strip():
        current = [parse((ROOT / f).read_text(encoding="utf-8")) if (ROOT / f).exists() else [] for f in FILES]
        days[dt.date.today().isoformat()] = snapshot(*current)

    out, previous = [], None
    for day in sorted(days):
        snap = days[day]
        seen = snap["open"] | snap["archived"]
        if previous is None:
            added, closed = len(seen), len(snap["archived"])
        else:
            # IDs arrived on 2026-10-27; map the previous day's URLs onto them.
            before = {snap["by_url"].get(k, k) for k in previous["open"] | previous["archived"]}
            was_archived = {snap["by_url"].get(k, k) for k in previous["archived"]}
            added = len(seen - before)
            closed = len(snap["archived"] - was_archived)
        out.append({"date": day, **snap["row"], "added": added, "closed": closed})
        previous = snap
    return out


def render(table):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(table)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if data/history.csv is out of date")
    args = ap.parse_args()
    text = render(rows())
    old = HISTORY.read_text(encoding="utf-8") if HISTORY.exists() else ""
    if args.check:
        if old != text:
            print("data/history.csv is out of date: run python3 scripts/stats.py", file=sys.stderr)
            sys.exit(1)
        print("data/history.csv is up to date")
        return
    HISTORY.write_text(text, encoding="utf-8")
    last = text.strip().splitlines()[-1].split(",")
    print(f"wrote {HISTORY.relative_to(ROOT)}: {text.count(chr(10)) - 1} days, "
          f"latest {last[0]} with {last[1]} open and {last[3]} tracked")


if __name__ == "__main__":
    main()
