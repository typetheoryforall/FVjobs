#!/usr/bin/env python3
"""Regenerate the job table in README.md from data/jobs.yml.

Everything between the BEGIN and END markers is replaced. Pass --check to fail
instead of writing, which is what CI uses to catch a stale README.
"""
import datetime as dt
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
BEGIN = "<!-- BEGIN JOBS -->"
END = "<!-- END JOBS -->"

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

def esc(text):
    return str(text).replace("|", "\\|")

def row(e):
    role = f"[{esc(e['role'])}]({e['url']})"
    cells = [
        esc(e["company"]),
        role,
        esc(e["location"]),
        REMOTE_LABEL.get(e["remote"], e["remote"]),
        ", ".join(esc(s) for s in e["stack"]),
        ", ".join(esc(d) for d in e["domain"]),
        SENIORITY_LABEL.get(e["seniority"], e["seniority"]),
        e["last_verified"],
    ]
    return "| " + " | ".join(cells) + " |"

def table(entries):
    entries = sorted(entries, key=lambda e: (e["company"].lower(), e["role"].lower()))
    head = (
        "| Company | Role | Location | Remote | Proof stack | Domain | Seniority | Last verified |\n"
        "|---|---|---|---|---|---|---|---|"
    )
    lines = [head] + [row(e) for e in entries]
    count = len(entries)
    # Stamp with the newest last_verified date rather than today, so the output
    # depends only on the data and --check doesn't go stale overnight.
    stamp = max((e["last_verified"] for e in entries), default="never")
    return (
        f"\n*{count} open roles, most recently verified {stamp}. "
        "Table generated from `data/jobs.yml`.*\n\n"
        + "\n".join(lines)
        + "\n"
    )

def load_jobs():
    """Load jobs.yml, normalising YAML dates to ISO strings (see validate.py)."""
    entries = yaml.safe_load((ROOT / "data" / "jobs.yml").read_text(encoding="utf-8")) or []
    for entry in entries:
        for key in ("last_verified", "closed"):
            if isinstance(entry.get(key), dt.date):
                entry[key] = entry[key].isoformat()
    return entries

def main():
    entries = load_jobs()
    text = README.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        print(f"error: README.md is missing the {BEGIN} / {END} markers", file=sys.stderr)
        return 1
    before = text.split(BEGIN)[0]
    after = text.split(END)[1]
    new = before + BEGIN + table(entries) + END + after

    if "--check" in sys.argv:
        if new != text:
            print("error: README.md is out of date — run python3 scripts/render.py", file=sys.stderr)
            return 1
        print("ok: README.md is up to date")
        return 0

    README.write_text(new, encoding="utf-8")
    print(f"wrote README.md with {len(entries)} roles")
    return 0

if __name__ == "__main__":
    sys.exit(main())
