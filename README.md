# FVjobs

A job board for **formal verification**: proof assistants, automated reasoning,
verified compilation, hardware verification, and the growing set of roles where
AI writes proofs and something has to check them.

**Browse the board at [typetheoryforall.github.io/FVjobs](https://typetheoryforall.github.io/FVjobs/)**,
with search and filters for the kind of verification (hardware, software, AI for
proof and autoformalization, academic, cryptocurrency), proof stack, remote work
and employer size.

Maintained alongside [Type Theory Forall](https://typetheoryforall.com).

## Why this exists

Formal verification roles are scattered across company career pages, academic
mailing lists and general job boards that have no idea what "Lean" means. This
board collects them in one place and records the two things those boards never
tell you up front:

- **which proof stack the job actually uses** — Lean, Rocq, Isabelle, SMT,
  SystemVerilog, F\*, K;
- **whether you can take the job** — some roles are closed to anyone who is not
  a US person, some sponsor visas, and some are open worldwide.

Every entry carries the date someone last checked that the posting was live.

## The data

[`data/jobs.yml`](data/jobs.yml) is the source of truth; the site and its
[`jobs.json`](https://typetheoryforall.github.io/FVjobs/jobs.json) are built
from it. Besides the proof stack and work authorization, each entry records the
kind of verification, location and remote policy, seniority, published pay, the
date the employer posted it, and the date someone last checked it was live.

Closed roles move to [`data/archive.yml`](data/archive.yml) rather than being
deleted: knowing that a company was hiring for Lean work six months ago is
useful even when the posting is gone.

## Adding a job

Open a [new job issue](../../issues/new?template=new-job.yml) — it is a short
form, and no Git required. If you would rather send a pull request, add an entry
to `data/jobs.yml` and run:

```bash
pip install pyyaml jsonschema
python3 scripts/validate.py --assign-ids
```

Leave `id` out of the new entry; `--assign-ids` gives it the next `FV-` number.

To preview the site locally, run `python3 scripts/site.py` and serve `_site/`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for what belongs here and what does not.

## Scope

In scope: roles whose core work is formal verification or closely supports it —
proof engineering, automated reasoning, verified compilation, hardware formal
verification, program analysis built on formal semantics, and AI-for-proof work.

Out of scope: general compiler and systems roles with no verification content,
"security engineer" roles that are really appsec, and anything where the
connection to formal methods is aspirational.

## Licence

Code (the scripts) is MIT, see [LICENSE](LICENSE). The job data in `data/` is
released under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) —
take it, mirror it, build on it. See [DATA-LICENSE.md](DATA-LICENSE.md).
