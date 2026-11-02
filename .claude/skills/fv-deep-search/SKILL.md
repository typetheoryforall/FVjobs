---
name: fv-deep-search
description: Run the FVjobs deep search for new open formal verification roles. Sweep the watchlist employers' job APIs, then actively hunt for roles and employers that earlier runs never triaged (big-company careers sites, discovery boards, conference and research-programme rosters, academic lists), and write an audit list for the maintainer to approve before anything reaches data/jobs.yml. It does not re-verify the roles already on the board; the recheck-jobs skill does that. Use this whenever someone in the FVjobs repo asks to run or re-run the job search, look for new formal verification, formal methods, Lean, Rocq, Isabelle, theorem-proving or hardware FV roles, find new employers hiring for FV, or "do the deep search again", even if they don't say "deep search".
---

# FVjobs deep search

A run ends in two things, in this order:

1. An audit list, `docs/search-runs/YYYY-MM-DD.md`, that the maintainer reviews.
2. Only after they approve it, a pull request that applies their decisions.

The maintainer curates the board by hand and approves every addition, so
nothing goes into `data/jobs.yml` before step 2. A full run takes a few hours
of web requests. Say so at the start, and give a one-line update at the end of
each phase.

The point of a run is to find what the board doesn't have yet. Don't
re-verify the roles already on it; that is the `recheck-jobs` skill's job,
and the maintainer runs it separately. Spend the time on new roles, and above
all on employers nobody has triaged before.

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
- Build the **already-triaged list** in your scratch space. It has every URL
  and employer in `data/jobs.yml` and `data/archive.yml`, every employer in
  `scripts/watchlist.yml`, and every candidate URL in the earlier files in
  `docs/search-runs/`, including the skipped ones. Give it to every agent:
  it says where they don't need to look, and the triage uses it to keep old
  candidates off the new audit list.
- Start from an up-to-date main on a new branch:
  `git checkout main && git pull && git checkout -b search-YYYY-MM-DD`.
- Rules every helper must follow:
  - **Read-only:** never apply, sign in or submit a form.
  - **Live** means the employer's own page or ATS API, checked today. A search
    snippet or an aggregator copy is only a lead.
  - **Bot checks and rate limits:** back off. Never try to get around them,
    for example with spoofed headers.

## Phase 1: watchlist sweep (minutes)

Run the sweep in the background, keeping the JSON in your scratch space:

```bash
python3 scripts/check.py watchlist --json <scratch>/watchlist.json
```

It lists the postings on each watchlist employer's board that match the
playbook's FV regex.
- `[FV-…]` means the posting is already on the board. Skip it.
- `[NEW]` is only a keyword hit. "Lean" also matches lean manufacturing and
  "formal" matches formal reviews, so read each one before calling it a
  candidate.
- Results are sorted by how often "formal" appears. Three or more mentions,
  or a named tool, is worth a look.
- Workable blocks after about 60 requests, for hours, so run the watchlist
  once per run.

The watchlist only covers employers we already know. Most of the run's effort
goes to phase 2's discovery lanes.

## Phase 2: search agents in parallel

Spawn these agents in a single message so they run at the same time. Each
brief must state:
- today's date;
- the playbook sections to read;
- the already-triaged list, and that a candidate on it only counts if
  something material changed (it reopened, has a new deadline, or a scope
  rule now covers it);
- the read-only rule;
- that the agent must not edit repository files (you write the run file);
- the candidate format below.

1. **Watchlist leads.** Read each `[NEW]` match from `watchlist`, and check
   every `ats: manual` employer in `scripts/watchlist.yml` by hand. Use a
   browser for the JS-only pages. Keep hardware roles within the playbook's
   per-employer cap and count the rest.
2. **Big-company search pages.** Apple, Google and DeepMind, Arm, Synopsys,
   and IBM, using the playbook's cookbook queries. Run extra queries for
   Amazon, Microsoft and NVIDIA where the sweep's queries may have missed
   roles.
3. **Discovery: new roles.** The open boards, searched for roles at any
   employer:
   - LinkedIn guest search with exact phrases;
   - the Getro VC boards, YC's Work at a Startup and Wellfound;
   - aisafety.com/jobs;
   - this month's Hacker News "Who is hiring" thread;
   - the employers under "Ideas for the next run" in the playbook.
4. **Discovery: new employers.** Find organisations doing FV that aren't on
   the already-triaged list, then look at their careers pages:
   - sponsors and industry papers at CAV, FMCAD, ITP, POPL, CPP, DVCon and
     Lean Together;
   - performers on research programmes that fund FV, such as ARIA's
     Safeguarded AI and DARPA's verification programmes;
   - companies whose public repositories use Lean, Rocq, Isabelle, Dafny,
     Verus, TLA+ or SymbiYosys;
   - FV tool vendors and consultancies, and startups announced in AI-for-math
     and AI-for-verification news.

   Search the web for the playbook's FV phrases together with the ATS
   domains (Ashby, Lever, Greenhouse, Workable, Personio, Teamtailor). Every
   employer found here goes back with its ATS and slug, even if it has
   nothing open today, so the watchlist grows.
5. **Academic.**
   - TYPES-announce, Rocq Discourse jobs, ILLC and the Logic List.
   - jobs.ac.uk, Inria, EPFL and TU Delft, AcademicTransfer, and the latest
     AAR newsletter.
   - Groups whose recent papers are in FV but who aren't on the
     already-triaged list.
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
- **Drop what earlier runs triaged.** A candidate whose URL is in an earlier
  run file stays off this audit list unless something material changed. If
  one is back, say what changed. Count the rest in the summary.
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
   could not be. Say how many candidates and employers are new to the board,
   the watchlist and earlier runs, and how many earlier-run candidates were
   dropped.
3. **Recommended additions.** Group them by category, in tables with ID,
   company, role, location, posted, evidence and FV relevance.
4. **Your call.**
5. **Recommended skip.** Give the reason for each.
6. **Leads not verified this run.**
7. **Recently closed.** List leads you saw that turned out to be gone.
8. **Noticed on the board**, only if a lane happened to see that a role on
   the board has closed or changed. Don't go looking; suggest a
   `recheck-jobs` run instead.

Then update the method so the next run starts ahead:
- add every new employer to `scripts/watchlist.yml`;
- in `docs/search-playbook.md`, add new endpoints, sources, dead ends and
  scope calls, and a row in the run log.

Stop here. Tell the maintainer:
- the counts, including how many employers are new;
- the file path;
- that they can approve or drop candidates by ID, or by group ("all
  recommended plus HW-12").

Commit nothing yet.

## Phase 5: apply what the maintainer approved

1. Add the approved roles to `data/jobs.yml`, keeping the file sorted by
   company. Leave out `id`. Every entry needs `category`, `posted` when known,
   and `last_verified` set to today. Quote a value that starts with `&` or `*`.
2. If the maintainer approved anything under "Noticed on the board", make
   those changes. Leave the rest of the board to `recheck-jobs`.
3. Run `python3 scripts/validate.py --assign-ids`, then
   `python3 scripts/site.py`. Spot-check a few new cards on the local site
   (`python3 -m http.server -d _site`).
4. Fill in the run file's Decision section, and the run-log row's "Added to
   the board" count.
5. Commit everything on the branch: data, run file, playbook and watchlist.
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
