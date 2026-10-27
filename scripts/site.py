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

from render import REMOTE_LABEL, SENIORITY_LABEL

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
        for key in ("last_verified", "closed"):
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
    data = {
        "stack": "|".join(e["stack"]),
        "remote": e["remote"],
        "seniority": e["seniority"],
        "text": " ".join([e["company"], e["role"], e["location"], *e["stack"], *e["domain"]]).lower(),
    }
    attrs = " ".join(f'data-{k}="{esc(v)}"' for k, v in data.items())
    when = (
        f'Closed <time datetime="{e["closed"]}">{e["closed"]}</time>'
        if closed
        else f'Checked <time datetime="{e["last_verified"]}">{e["last_verified"]}</time>'
    )
    return f"""
<li class="job" {attrs}>
  <div class="job-head">
    <p class="company">{esc(e["company"])}</p>
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


def main():
    jobs, archive = load("jobs.yml"), load("archive.yml")
    latest = max((e["last_verified"] for e in jobs), default="")
    template = (SRC / "index.html").read_text(encoding="utf-8")
    page = (
        template.replace("{{count}}", str(len(jobs)))
        .replace("{{companies}}", str(len({e["company"] for e in jobs})))
        .replace("{{latest}}", latest)
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
