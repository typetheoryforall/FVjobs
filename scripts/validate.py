#!/usr/bin/env python3
"""Validate data/jobs.yml and data/archive.yml against data/schema.json.

Also checks for duplicate URLs and IDs, implausible dates, and entries that
have not been verified recently. Exits non-zero on error.

    python3 scripts/validate.py --assign-ids

first numbers every entry that has no `id`, continuing from the highest in use.
"""
import argparse
import datetime as dt
import pathlib
import re
import sys

import yaml
from jsonschema import Draft202012Validator

ROOT = pathlib.Path(__file__).resolve().parent.parent
STALE_DAYS = 60
FILES = ("jobs.yml", "archive.yml")
ID = re.compile(r"^FV-(\d+)$")
ASSIGN = "python3 scripts/validate.py --assign-ids"

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

def assign_ids():
    """Give every entry without an id the next free FV- number, in file order.

    Edits the files as text, putting an `id:` line at the top of each new entry,
    so comments and formatting are left alone. Numbers are never reused: the
    next one is above every ID in either file.
    """
    used = [int(m[1]) for name in FILES for e in load(name)
            if isinstance(e, dict) and (m := ID.match(str(e.get("id", ""))))]
    n = max(used, default=0)
    for name in FILES:
        path = ROOT / "data" / name
        if not path.exists():
            continue
        entries = load(name)
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        if sum(line.startswith("- ") for line in lines) != len(entries):
            sys.exit(f"{name}: cannot tell where each entry starts; add the ids by hand")
        out, k = [], 0
        for line in lines:
            if line.startswith("- "):
                e = entries[k]
                k += 1
                if isinstance(e, dict) and not e.get("id"):
                    n += 1
                    out.append(f"- id: FV-{n:03d}\n")
                    line = "  " + line[2:]
                    print(f"{name}: FV-{n:03d} {e.get('company')} — {e.get('role')}")
            out.append(line)
        path.write_text("".join(out), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--assign-ids", action="store_true",
                        help="number entries that have no id before validating")
    if parser.parse_args().assign_ids:
        assign_ids()

    schema = yaml.safe_load((ROOT / "data" / "schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors, warnings = [], []
    today = dt.date.today()
    ids = {}

    for name in FILES:
        entries = load(name)
        for err in validator.iter_errors(entries):
            if err.validator == "required" and "'id'" in err.message:
                continue  # reported below, with the command that fixes it
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

            what = f"{e.get('company')} — {e.get('role')}"
            ident = e.get("id")
            if not ident:
                errors.append(f"{name}: {what}: no id; run `{ASSIGN}`")
            elif ident in ids:
                errors.append(f"{name}: duplicate id {ident} ({ids[ident]} and {what})")
            else:
                ids[ident] = what

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
