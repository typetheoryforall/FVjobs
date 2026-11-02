---
name: fv-deep-search
description: Run the FVjobs deep search for open formal verification roles. Re-verify every role on the board, sweep the watchlist employers' job APIs, search big-company careers sites, discovery boards and academic lists, then write an audit list for the maintainer to approve before anything reaches data/jobs.yml. Use this whenever someone in the FVjobs repo asks to run or re-run the job search, look for new formal verification, formal methods, Lean, Rocq, Isabelle, theorem-proving or hardware FV roles, refresh or re-check the board, find stale or closed postings, or "do the deep search again", even if they don't say "deep search".
---

# FVjobs deep search

A run ends in two things, in this order:

1. An audit list, `docs/search-runs/YYYY-MM-DD.md`, that the maintainer reviews.
2. Only after they approve it, a pull request that applies their decisions.

The maintainer curates the board by hand and approves every addition, so
nothing goes into `data/jobs.yml` or `data/archive.yml` before step 2. A full
run takes a few hours of web requests. Say so at the start, and give a
one-line update at the end of each phase.

## Before you start

- Read `docs/search-playbook.md` in full. It is the method: the ground rules,
  the run order, the endpoint for each ATS, the scope calls and the
  categories. This skill only says how to run that method. When the playbook
  and this file disagree, the playbook wins, and you should fix this file.
- Skim the newest file in `docs/search-runs/`. It shows the audit format and
  the maintainer's last decisions.
- If `triage-decisions.md` exists at the repo root, read it. It holds the
  maintainer's settled calls on submitted jobs, and it is gitignored, so not
  every checkout has it.
- Start from an up-to-date main on a new branch:
  `git checkout main && git pull && git checkout -b search-YYYY-MM-DD`.
- Rules every helper must follow:
  - **Read-only:** never apply, sign in or submit a form.
  - **Live** means the employer's own page or ATS API, checked today. A search
    snippet or an aggregator copy is only a lead.
  - **Bot checks and rate limits:** back off. Never try to get around them.

## Phase 1: scripted sweep (minutes)

`scripts/check.py` is shared with the `recheck-jobs` skill. Run its two
read-only checks, in the background, keeping the JSON in your scratch space:

```bash
python3 scripts/check.py board --json <scratch>/board.json
python3 scripts/check.py watchlist --json <scratch>/watchlist.json
```

`board` reports each role on the board as `OPEN`, `CLOSED` or `CHECK`.
Treat it exactly as section 2 of `.claude/skills/recheck-jobs/SKILL.md`
says:
- Trust `OPEN` and `CLOSED`.
- If most of one employer's roles close at once, look at its careers page
  first.
- Every `CHECK` role needs someone to read its page; lane 1 below does that.

In this run you only collect the outcomes for the audit list. You apply them
in phase 5.

`watchlist` lists the postings on each watchlist employer's board that match
the playbook's FV regex.
- `[FV-…]` means the posting is already on the board.
- `[NEW]` is only a keyword hit. "Lean" also matches lean manufacturing and
  "formal" matches formal reviews, so read each one before calling it a
  candidate.
- Results are sorted by how often "formal" appears. Three or more mentions,
  or a named tool, is worth a look.
- Workable blocks after about 60 requests, for hours, so run the watchlist
  once per run.

## Phase 2: search agents in parallel

Spawn these agents in a single message so they run at the same time. Each
brief must state:
- today's date;
- the playbook sections to read;
- the read-only rule;
- that the agent must not edit repository files (you write the run file);
- the candidate format below.

1. **Board, by hand.** Every `CHECK` role from `board`, settled by the rules
   in recheck-jobs' section 2, and every `ats: manual` employer in
   `scripts/watchlist.yml`. Use a browser for the JS-only pages.
2. **Watchlist leads.** Read each `[NEW]` match from `watchlist` and keep
   the in-scope ones. Hardware FV dominates by volume, so keep about three per
   employer and count the rest.
3. **Big-company search pages.** Apple, Google and DeepMind, Arm, Synopsys,
   and IBM, using the playbook's cookbook queries. Run extra queries for
   Amazon, Microsoft and NVIDIA where the sweep's queries may have missed
   roles.
4. **Discovery.**
   - LinkedIn guest search with exact phrases.
   - The Getro VC boards.
   - aisafety.com/jobs.
   - This month's Hacker News "Who is hiring" thread.
   - The employers listed under "Ideas for the next run" in the playbook.

   For each new employer, find its ATS slug.
5. **Academic.**
   - TYPES-announce, Rocq Discourse jobs, ILLC and the Logic List.
   - jobs.ac.uk, Inria, EPFL and TU Delft, AcademicTransfer, and the latest
     AAR newsletter.
   - A post must not close within about a week of today.

Each agent returns candidates in this shape:

```
company | role (as posted) | url (clean, no tracking parameters)
location | remote | category | seniority | stack | domain
posted (ATS date, never "2 weeks ago") | deadline (academic) | pay | work authorization
evidence: how and when you confirmed it is live
FV relevance: one line on why the core work is formal verification
recommendation: recommend / your call / skip, with the reason
```

Agents also return:
- **new watchlist employers**, with ATS and slug;
- **dead ends**: sources that were blocked, empty or stale.

## Phase 3: triage

- **Merge and de-duplicate.** Merge everything, then drop duplicates by URL.
  Also drop roles already on the board: use the sweep's `on_board` field, and
  grep `data/jobs.yml` and `data/archive.yml` for the company. Fold twin
  requisitions into a single entry that lists several locations.
- **Check again.** Re-check every candidate you recommend, independently of
  the agent that found it. A verification agent can do this. List the ones
  that could not be re-checked, and say why.
- **Sort.** Put each candidate in recommend, your call or skip, using the
  playbook's scope calls and `triage-decisions.md`. The maintainer has
  accepted every kind of case those files list, so reserve "your call" for
  borderline cases of a kind they don't cover.
- **Fill in the fields.** Give each candidate an ID by category, numbered
  from 01: `HW-` (hardware), `SW-` (software), `AI-` (AI for proof), `AC-`
  (academic), `CR-` (cryptocurrency). Then set its `category`, its
  `big-company` tag where it applies, and its `posted` date, following the
  playbook's "Categories and tags" section.

## Phase 4: write the audit list, then stop

Write `docs/search-runs/YYYY-MM-DD.md` with the sections of the last run file:

1. **Decision.** Leave this empty for the maintainer.
2. **Summary.** Give the counts, what was re-checked a second time, and what
   could not be.
3. **Proposed changes to existing entries.** Cover archives, retitles,
   location and URL changes, and missing posted dates.
4. **Recommended additions.** Group them by category, in tables with ID,
   company, role, location, posted, evidence and FV relevance.
5. **Your call.**
6. **Recommended skip.** Give the reason for each.
7. **Leads not verified this run.**
8. **Recently closed.** List leads you saw that turned out to be gone.

Then update the method so the next run starts ahead:
- add new employers to `scripts/watchlist.yml`;
- in `docs/search-playbook.md`, add new endpoints, dead ends and scope calls,
  and a row in the run log.

Stop here. Tell the maintainer:
- the counts;
- the file path;
- that they can approve or drop candidates by ID, or by group ("all
  recommended plus HW-12").

Commit nothing yet.

## Phase 5: apply what the maintainer approved

1. Add the approved roles to `data/jobs.yml`, keeping the file sorted by
   company. Leave out `id`. Every entry needs `category`, `posted` when known,
   and `last_verified` set to today. Quote a value that starts with `&` or `*`.
2. Record the re-verification:
   `python3 scripts/check.py apply --open FV-…,… --closed FV-…,…`.
   This sets `last_verified` to today on the open roles, and moves the closed
   ones to `data/archive.yml` with a `closed` date, keeping their IDs. Close
   any matching `[stale]` issues in the commit, as recheck-jobs describes.
3. Correct any facts that changed on still-open postings (title, location,
   pay), following the posting.
4. Run `python3 scripts/validate.py --assign-ids`, then
   `python3 scripts/site.py`. Spot-check a few new cards on the local site
   (`python3 -m http.server -d _site`).
5. Fill in the run file's Decision section, and the run-log row's "Added to
   the board" count.
6. Commit everything on the branch: data, run file, playbook and watchlist.
   Open a PR that summarises the decision, and merge only when the
   maintainer says so.

An entry looks like this:

```yaml
- company: Example Labs
  role: Formal Verification Engineer   # the posting's own title
  category: software
  url: https://jobs.ashbyhq.com/example/0000-…
  location: London, UK
  remote: hybrid
  stack: [Lean, SMT]
  domain: [compilers]
  seniority: engineer
  work_authorization: Right to work in the UK required   # only when stated
  compensation: GBP 90,000–120,000                       # only employer figures
  notes: >-
    One or two factual sentences.
  posted: '2026-10-20'
  last_verified: 2026-11-02
```
