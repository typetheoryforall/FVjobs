#!/usr/bin/env python3
"""Build the static GitHub Pages site from data/jobs.yml and data/archive.yml.

Writes _site/index.html (every role pre-rendered, so the page works without
JavaScript), copies the assets from site/, and publishes the data as
_site/jobs.json. The Pages workflow runs this; locally:

    python3 scripts/site.py && python3 -m http.server -d _site
"""
import datetime as dt
import html
import json
import pathlib
import shutil

import yaml

REMOTE_LABEL = {
    "onsite": "On-site",
    "hybrid": "Hybrid",
    "remote": "Remote",
    "remote-worldwide": "Remote (worldwide)",
}
SENIORITY_LABEL = {
    "intern": "Intern",
    "phd": "PhD",
    "postdoc": "Postdoc",
    "engineer": "Engineer",
    "research-engineer": "Research engineer",
    "research-scientist": "Research scientist",
    "senior": "Senior",
    "principal": "Principal",
    "lead": "Lead",
    "any": "Various",
}
# In the order the filter offers them.
CATEGORY_LABEL = {
    "academic": "Academic",
    "ai-for-proof": "AI for proof & autoformalization",
    "software": "Software",
    "hardware": "Hardware",
    "cryptocurrency": "Cryptocurrency",
}
# Postings name the same tool in different ways. Cards keep the posting's
# wording; the proof-stack filter files each spelling under one name.
STACK_ALIAS = {
    "Coq": "Rocq",
    "Isabelle/HOL": "Isabelle",
    "Jasper": "JasperGold",
    "Lean 4": "Lean",
    "mathlib": "Mathlib",
    "model checkers": "model checking",
    "SystemVerilog Assertions": "SVA",
    "theorem provers": "theorem proving",
}

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "site"
OUT = ROOT / "_site"
REPO = "https://github.com/typetheoryforall/FVjobs"


def load(name):
    """Load a data file, normalising YAML dates to ISO strings (see validate.py)."""
    path = ROOT / "data" / name
    if not path.exists():
        return []
    entries = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    for entry in entries:
        for key in ("posted", "last_verified", "closed"):
            if isinstance(entry.get(key), dt.date):
                entry[key] = entry[key].isoformat()
    return sorted(entries, key=lambda e: (e["company"].lower(), e["role"].lower()))


def esc(text):
    return html.escape(str(text), quote=True)


def chips(items, cls):
    return "".join(f'<li class="{cls}">{esc(i)}</li>' for i in items)


def details(e):
    rows = [
        ("Pay", e.get("compensation")),
        ("Work authorization", e.get("work_authorization")),
        ("Notes", e.get("notes")),
    ]
    rows = [(k, v) for k, v in rows if v]
    if not rows:
        return ""
    body = "".join(f"<dt>{k}</dt><dd>{esc(v)}</dd>" for k, v in rows)
    return f'<details><summary>Pay, eligibility and notes</summary><dl>{body}</dl></details>'


def job(e, closed=False):
    kind = CATEGORY_LABEL.get(e["category"], e["category"])
    data = {
        "stack": "|".join(dict.fromkeys(STACK_ALIAS.get(s, s) for s in e["stack"])),
        "remote": e["remote"],
        "seniority": e["seniority"],
        "category": e["category"],
        "big": "1" if "big-company" in e.get("tags", []) else "0",
        "posted": e.get("posted", ""),
        "text": " ".join([e["company"], e["role"], kind, e["location"], *e["stack"], *e["domain"]]).lower(),
    }
    attrs = " ".join(f'data-{k}="{esc(v)}"' for k, v in data.items())
    when = (
        f'Closed <time datetime="{e["closed"]}">{e["closed"]}</time>'
        if closed
        else f'Checked <time datetime="{e["last_verified"]}">{e["last_verified"]}</time>'
    )
    if e.get("posted"):
        when = f'Posted <time datetime="{e["posted"]}">{e["posted"]}</time><br>{when}'
    return f"""
<li class="job" {attrs}>
  <div class="job-head">
    <p class="company">{esc(e["company"])} <span class="kind kind-{esc(e["category"])}">{esc(kind)}</span></p>
    <h3><a href="{esc(e["url"])}" rel="noopener">{esc(e["role"])}</a></h3>
  </div>
  <p class="where"><span class="remote remote-{esc(e["remote"])}">{esc(REMOTE_LABEL.get(e["remote"], e["remote"]))}</span>
    {esc(e["location"])}</p>
  <p class="level">{esc(SENIORITY_LABEL.get(e["seniority"], e["seniority"]))}</p>
  <ul class="stack" aria-label="Proof stack">{chips(e["stack"], "tool")}</ul>
  <ul class="domain" aria-label="Domain">{chips(e["domain"], "area")}</ul>
  <p class="checked">{when}</p>
  {details(e)}
</li>"""


def categories(jobs):
    """The kind-of-verification radios, with how many open roles each has."""
    def option(value, label, n, checked=""):
        return (f'<label><input type="radio" name="category" value="{value}"{checked}>'
                f'<span>{esc(label)}<small>{n}</small></span></label>')
    counts = {c: sum(e["category"] == c for e in jobs) for c in CATEGORY_LABEL}
    return option("", "All", len(jobs), " checked") + "".join(
        option(c, label, counts[c]) for c, label in CATEGORY_LABEL.items() if counts[c]
    )


def main():
    jobs, archive = load("jobs.yml"), load("archive.yml")
    latest = max((e["last_verified"] for e in jobs), default="")
    template = (SRC / "index.html").read_text(encoding="utf-8")
    page = (
        template.replace("{{count}}", str(len(jobs)))
        .replace("{{companies}}", str(len({e["company"] for e in jobs})))
        .replace("{{latest}}", latest)
        .replace("{{categories}}", categories(jobs))
        .replace("{{repo}}", REPO)
        .replace("{{jobs}}", "".join(job(e) for e in jobs))
        .replace("{{archive_count}}", str(len(archive)))
        .replace("{{archive}}", "".join(job(e, closed=True) for e in archive))
    )
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT, ignore=shutil.ignore_patterns("index.html"))
    (OUT / "index.html").write_text(page, encoding="utf-8")
    (OUT / "jobs.json").write_text(
        json.dumps({"jobs": jobs, "archive": archive}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"wrote {OUT.relative_to(ROOT)}/ with {len(jobs)} roles and {len(archive)} archived")


if __name__ == "__main__":
    main()
