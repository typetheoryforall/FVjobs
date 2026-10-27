#!/usr/bin/env python3
"""Check that every URL in data/jobs.yml still resolves.

Prints a Markdown report on failure, which the weekly workflow turns into an
issue. Note that single-page application job boards (Google Careers, Workday)
return 200 even for a closed role, so a clean run is necessary, not sufficient.
"""
import pathlib
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (compatible; FVjobs link checker)"}
TIMEOUT = 25

def check(entry):
    req = urllib.request.Request(entry["url"], headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return entry, r.status, None
    except urllib.error.HTTPError as e:
        return entry, e.code, None
    except Exception as e:  # noqa: BLE001 - report whatever went wrong
        return entry, None, str(e)[:120]

def main():
    entries = yaml.safe_load((ROOT / "data" / "jobs.yml").read_text(encoding="utf-8")) or []
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(check, entries))

    bad = [(e, s, err) for e, s, err in results if err or (s and s >= 400)]
    for e, status, err in results:
        print(f"{status or 'ERR':>4}  {e['id']}  {e['company']} — {e['role']}")

    if bad:
        print("\n## Links needing attention\n")
        for e, status, err in bad:
            print(f"- **{e['id']} {e['company']} — {e['role']}**: {err or f'HTTP {status}'}  \n  {e['url']}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
