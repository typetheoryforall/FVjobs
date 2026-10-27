#!/usr/bin/env python3
"""Validate data/jobs.yml and data/archive.yml against data/schema.json.

Also checks for duplicate URLs, implausible dates, and entries that have not
been verified recently. Exits non-zero on error.
"""
import datetime as dt
import pathlib
import sys

import yaml
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parent.parent
STALE_DAYS = 60

def load(name):
    """Load a data file, normalising YAML dates to ISO strings.

    PyYAML turns an unquoted 2026-10-26 into a datetime.date. Contributors
    should not have to remember quotes, so normalise here instead.
    """
    path = ROOT / "data" / name
    if not path.exists():
        return []
    entries = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for key in ("posted", "last_verified", "closed"):
            if isinstance(entry.get(key), dt.date):
                entry[key] = entry[key].isoformat()
    return entries

def main():
    schema = yaml.safe_load((ROOT / "data" / "schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors, warnings = [], []
    today = dt.date.today()

    for name in ("jobs.yml", "archive.yml"):
        entries = load(name)
        for err in validator.iter_errors(entries):
            where = " -> ".join(str(p) for p in err.absolute_path) or "(root)"
            errors.append(f"{name}: {where}: {err.message}")

        seen = {}
        for i, e in enumerate(entries):
            if not isinstance(e, dict):
                continue
            url = e.get("url")
            if url in seen:
                errors.append(f"{name}: duplicate url {url} (entries {seen[url]} and {i})")
            seen[url] = i

            posted = e.get("posted")
            if posted:
                try:
                    if dt.date.fromisoformat(posted) > today:
                        errors.append(f"{name}: {e.get('company')}: posted is in the future")
                except ValueError:
                    errors.append(f"{name}: {e.get('company')}: bad posted {posted!r}")

            verified = e.get("last_verified")
            if verified:
                try:
                    d = dt.date.fromisoformat(verified)
                except ValueError:
                    errors.append(f"{name}: {e.get('company')}: bad last_verified {verified!r}")
                    continue
                if d > today:
                    errors.append(f"{name}: {e.get('company')}: last_verified is in the future")
                elif name == "jobs.yml" and (today - d).days > STALE_DAYS:
                    warnings.append(
                        f"{e.get('company')} — {e.get('role')}: not verified for "
                        f"{(today - d).days} days"
                    )

    archived = {e.get("url") for e in load("archive.yml") if isinstance(e, dict)}
    for e in load("jobs.yml"):
        if isinstance(e, dict) and e.get("url") in archived:
            errors.append(f"{e.get('url')} appears in both jobs.yml and archive.yml")

    for w in warnings:
        print(f"warning: {w}")
    for err in errors:
        print(f"error: {err}", file=sys.stderr)

    if errors:
        return 1
    print(f"ok: {len(load('jobs.yml'))} open, {len(load('archive.yml'))} archived")
    return 0

if __name__ == "__main__":
    sys.exit(main())
