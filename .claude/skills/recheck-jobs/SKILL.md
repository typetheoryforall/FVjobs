---
name: recheck-jobs
description: Re-check every role on the FVjobs board (data/jobs.yml, which the GitHub Pages site is built from) to see whether it is still open; move closed roles to data/archive.yml with a `closed` date and set `last_verified` to today on the ones still open. Use when asked to re-verify the board, check which jobs are still open, clean out stale or expired postings, bump verification dates, or handle `[stale] FV-…` issues in bulk.
---

# Re-check the board

The board promises readers that every role was checked recently, so this sweep
has to be right more than it has to be fast. Mark a role closed or open only on
evidence; anything you can't settle stays as it is and goes in the report.

## 1. Run the checker

```bash
git switch main && git pull --ff-only
python3 scripts/check.py board --json <scratchpad>/board.json
```

It takes a few minutes, because it pauses between requests to the same host.
Run it in the background. Each role comes back as one of:

- **OPEN**: a reliable source says the posting is live. That is either an ATS
  API (Ashby, Lever, Greenhouse, Workday `canApply`, Personio, Workable,
  Eightfold for Microsoft and Qualcomm, Jibe for AMD and JHU APL, Mercor,
  Alignerr), or a page marker that has proved reliable (Google's Apply button,
  Apple's posting data, amazon.jobs "Apply now", the role title on an Arm or
  Synopsys page). Trust it.
- **CLOSED**: the same sources say the posting is gone: API 404, a `null`
  Ashby posting, Google's "Job not found", or amazon.jobs, Arm or Synopsys
  returning 404 or redirecting home. Trust it, with one exception. If most of
  one employer's roles close at once, the employer probably moved boards or
  renamed its slug, not stopped hiring. Open its careers page before archiving
  them.
- **CHECK**: there is no API, or the answer was inconclusive. The `evidence`
  field gives a hint:
  - HTTP 404/410, a redirect, or a "no longer accepting" phrase in the
    visible text;
  - a deadline, marked `PASSED` or `ahead`;
  - "loads, title on the page, no closing signs";
  - "title not found on the page". This is common for open-application
    entries, whose role text is ours, not the employer's;
  - an unlisted Ashby posting;
  - HTTP 403/429 from an API. Microsoft's API returns 429 if it was queried
    recently, so re-run `--only` those IDs later.

## 2. Settle every CHECK by reading the posting

Use WebFetch for static pages. Use the built-in browser for pages that need
JavaScript (Google, Apple, Amazon, SuccessFactors boards like EPFL and TU
Delft, Arm, Synopsys) and for anything that returned 403 or 429.

**Closed** when any of these holds:
- The page says the role is closed, filled, expired or not found.
- The URL now redirects to a search page, the careers home page or another
  role. Arm reuses job IDs, so check that the title still matches.
- HTTP 404 or 410.
- The application deadline is before today. Academic posts and mailing-list
  announcements (TYPES-announce, Logic List) usually state one.

**Open** when the page shows the posting with an apply route, and any stated
deadline is today or later. "Loads, title on the page, no closing signs" and a
deadline marked `ahead` are strong signs, but skim the page anyway. Some boards
keep a closed ad up and only drop the Apply button. An Ashby posting that is
unlisted but still accepts applications counts as open.

**Leave unchanged** when you can't tell:
- A bot check or rate limit you can't get past in the browser. Never try to
  get around it.
- A mailing-list post with no deadline.
- An open-application page whose wording is ambiguous.

Don't bump `last_verified` for these. List them in the report.

While a posting is open, compare it with the entry: title, location, pay, work
authorization. If the employer changed something, update the entry to match
the posting and say so in the report. Facts come from the posting, as in
`triage-decisions.md`.

## 3. Show the user the result before writing anything

Give the user a short report:
- the roles to archive, each with ID, company, role and the evidence;
- how many roles are confirmed open;
- the roles left unchanged and why;
- any facts you corrected.

The sweep was asked for, so you don't need approval for closures that rest on
clear evidence. If a closure is a judgement call, ask first: for example, an
open-application page that just went quiet.

## 4. Apply, check, publish

```bash
python3 scripts/check.py apply --open FV-001,FV-002,... --closed FV-010,...
python3 scripts/validate.py
python3 scripts/site.py
```

`apply` edits the files as text. Open roles get today's `last_verified`.
Closed roles move to `archive.yml`, keeping their ID, sorted by company, with
`closed:` set to today. Make your fact corrections with Edit after `apply`.

Look for open `[stale] FV-…` issues (`gh issue list --label stale`). Every one
whose role you archived gets a `Closes #N` line in the commit. A stale report
about a role you confirmed open is worth a reply on that issue, not a closure.

Commit as `Re-check the board: archive N closed roles, verify M`, listing the
archived IDs in the body. Push straight to `main` if the user asked for that
this time; otherwise open a PR.

## Notes

- **Workable rate limits.** Workable blocks after about 60 requests, and the
  block lasts hours. The script pauses 6 seconds per request. If it still
  returns 429, check those roles in the browser later, not in a loop.
- **Microsoft's API** wants about 5 seconds between calls, which the script
  already does.
- **New employers or ATS types.** If one keeps landing in CHECK, add a checker
  to `scripts/check.py`, following the existing ones, and note the endpoint in
  the cookbook in `docs/search-playbook.md`.
