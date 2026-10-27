# Contributing

Thank you for adding to the board. The aim is a list that someone looking for
formal verification work can trust: current, specific, and honest about who can
actually take each job.

## The fastest way

Open a [new job issue](../../issues/new?template=new-job.yml). It is a form, it
takes two minutes, and a maintainer moves it into the data file.

## Sending a pull request

1. Add an entry to `data/jobs.yml`, keeping the file sorted by company.
2. Install the two dependencies: `pip install pyyaml jsonschema`.
3. Run `python3 scripts/validate.py` and fix anything it reports.

CI runs the same validator and builds a preview of the site for every PR.

## The fields

| Field | Required | Notes |
|---|---|---|
| `company` | yes | The employer, not the recruiting agency |
| `role` | yes | The posting's own title |
| `category` | yes | The kind of verification: `hardware`, `software`, `ai-for-proof` (AI for proof and autoformalization), `academic` (university and research-institute posts), or `cryptocurrency` (blockchain, smart contracts, ZK). Industry labs such as Microsoft Research go under the kind of work they do |
| `url` | yes | Link to the posting itself where one exists; a careers page is acceptable for speculative or open applications |
| `location` | yes | As the posting states it. "Anywhere" for genuinely unrestricted roles |
| `remote` | yes | `onsite`, `hybrid`, `remote` (within a stated region) or `remote-worldwide` |
| `stack` | yes | Verification tools the posting names: Lean, Rocq, Isabelle, Agda, SMT, TLA+, F\*, K, SystemVerilog, hax, Verus, … |
| `domain` | yes | Where the work lands: hardware, cryptography, compilers, blockchain, AI safety, aerospace, finance, … |
| `seniority` | yes | One of the values in `data/schema.json` |
| `tags` | no | `[big-company]` for big tech, the major chip, EDA and aerospace groups, and their subsidiaries (roughly 5,000 staff or more). Used only by the site's employer filter; it is not shown on the board |
| `posted` | no | ISO date the employer published the posting, as the posting or its job board states it. Leave it out when no date is shown rather than guessing. The site's "newest first" order uses it |
| `last_verified` | yes | ISO date on which you confirmed the posting was live |
| `work_authorization` | no | **Please fill this in when the posting restricts it.** Export-control clauses ("US Person required"), visa sponsorship, and region limits are the single most useful thing here |
| `compensation` | no | Only what the employer published. Do not add third-party estimates |
| `notes` | no | One or two sentences of genuinely useful context |

## What belongs here

Roles whose core work is formal verification or directly supports it: proof
engineering, automated reasoning, verified compilation, hardware formal
verification, program analysis grounded in formal semantics, and AI-for-proof
work.

Please do not add:

- general compiler, systems or security roles with no verification content;
- roles you have not checked are open;
- third-party salary estimates presented as employer figures;
- anyone's private contact details. Published addresses and application links
  only — no personal emails shared with you in confidence;
- editorial commentary about an employer. Keep `notes` factual.

## Keeping it honest

- Update `last_verified` whenever you re-check a posting. The validator warns
  about anything older than 60 days.
- When a role closes, move it to `data/archive.yml` with a `closed` date rather
  than deleting it.
- A weekly workflow checks every link and opens an issue listing failures. Note
  that single-page job boards (Google Careers, Workday) return a 200 even for a
  role that has been taken down, so a passing link check is necessary but not
  sufficient — a human still has to look.
