# FVjobs

A job board for **formal verification**: proof assistants, automated reasoning,
verified compilation, hardware verification, and the growing set of roles where
AI writes proofs and something has to check them.

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

<!-- BEGIN JOBS -->
*17 open roles, most recently verified 2026-10-26. Table generated from `data/jobs.yml`.*

| Company | Role | Location | Remote | Proof stack | Domain | Seniority | Last verified |
|---|---|---|---|---|---|---|---|
| Access Softek Toolchains | [Compiler Developer (LLVM, C++)](https://jobs.lever.co/accesssoftek/55497b30-5fbc-4fda-81ce-91752ae1599a) | Anywhere | Remote (worldwide) | LLVM, Clang, C++ | compilers, toolchains | Engineer | 2026-10-26 |
| Amazon Web Services | [Applied Scientist, Automated Reasoning](https://www.amazon.jobs/en/jobs/10502706/applied-scientist-automated-reasoning) | Multiple US cities | On-site | Lean, Rocq, Dafny, Isabelle, SMT | cloud, cryptography, AI safety | Research scientist | 2026-10-26 |
| Beneficial AI Foundation | [AI Safety Research Scientist / Research Engineer (formal verification)](https://www.beneficialaifoundation.org/jobs) | Anywhere | Remote (worldwide) | Lean, Verus, Rust | AI safety, cryptography | Various | 2026-10-26 |
| CertiK | [Software Engineer (III to Principal), Formal Methods](https://jobs.lever.co/certik/f8fbe497-34d2-49fa-9308-879f0ffd8fa8) | New York / Seattle / SF Bay Area / Remote | Remote | SMT, model checking, OCaml, Haskell | blockchain, smart contracts | Engineer | 2026-10-26 |
| Code Metal | [Research Engineer — Formal Methods](https://jobs.ashbyhq.com/code-metal/550aed7b-86d2-48c3-af27-e61671e2d493) | Boston, MA | Hybrid | theorem proving, SMT, program synthesis, static analysis | compilers, embedded | Research engineer | 2026-10-26 |
| Cryspen | [Open applications (Rust verification, hax)](https://cryspen.com/jobs) | France / Germany | Hybrid | hax, Rust, F* | cryptography | Various | 2026-10-26 |
| eleQtron | [Compiler Engineer (m/w/d)](https://eleqtron.com/en/jobs/compiler-engineer-m-w-d/) | Hamburg or Siegen, Germany | On-site | LLVM, MLIR, QIR, C++, Rust | quantum, compilers | Engineer | 2026-10-26 |
| Harmonic | [Formal Verification Engineer (Aristotle)](https://jobs.ashbyhq.com/harmonic/5e759f93-e90c-43a9-8c88-af25428237ca) | Palo Alto, CA | On-site | Lean | AI for mathematics, hardware, software verification | Engineer | 2026-10-26 |
| Harmonic | [Research Engineer, Formal Methods](https://jobs.ashbyhq.com/harmonic/74f2ed85-b1cc-40b1-825d-fefd2fcf557c) | Palo Alto, CA | On-site | Lean, Rocq, Isabelle, Agda, Python | AI for mathematics, theorem proving | Research engineer | 2026-10-26 |
| Imandra | [Open applications — R&D (automated reasoning)](https://apply.workable.com/imandra/) | Edinburgh / London / Bristol / Austin | Remote | OCaml, SMT, automated reasoning | finance, automated reasoning | Various | 2026-10-26 |
| Jane Street | [Formal Methods Engineer](https://www.janestreet.com/join-jane-street/apply/8588405002) | London, UK (also New York) | On-site | proof assistants, static analysis, refinement types, property-based testing | finance, AI-assisted programming | Engineer | 2026-10-26 |
| Oath Technologies | [Formal Methods Research Engineer](https://jobs.lever.co/convergentresearch/87a70993-3dbd-480a-9fe2-221628639f07) | Berkeley, CA | On-site | Lean, Coq, Isabelle, SMT | AI safety, AI oversight | Research engineer | 2026-10-26 |
| Oath Technologies | [Research Engineer, Tools & Infrastructure](https://jobs.lever.co/convergentresearch/a2e56f3e-09b0-402e-9566-6c7b235759d0) | Berkeley, CA | On-site | developer tooling, language servers, agent scaffolding | AI safety, developer tools | Research engineer | 2026-10-26 |
| Quantinuum | [Advanced Quantum Compiler Engineer (925)](https://jobs.eu.lever.co/quantinuum/1e52f038-a161-4276-ab8f-5c0b9c2fc28e) | Broomfield, CO | Hybrid | LLVM, MLIR, QIR, Rust, C++ | quantum, compilers | Engineer | 2026-10-26 |
| Runtime Verification | [Open applications — verification engineering (K framework)](https://runtimeverification.com/careers) | Urbana, IL — remote friendly | Remote | K framework, executable semantics | blockchain, language semantics | Various | 2026-10-26 |
| Theorem (Theorem Labs) | [ML research engineer / research scientist / SWE / research fellow](https://theorem.dev/careers/) | San Francisco, CA | On-site | Lean, Rocq | AI for program verification | Various | 2026-10-26 |
| Veridise | [Formal Methods Researcher for ZK](https://veridise.com/careers/formal-methods-researcher-for-zk/) | Flexible | Remote | Lean, Rocq, ACL2, SMT, Rust, C++ | zero-knowledge, blockchain security | Research scientist | 2026-10-26 |
<!-- END JOBS -->

## Legend

| Column | Meaning |
|---|---|
| **Remote** | `On-site`, `Hybrid`, `Remote` (within a stated region), `Remote (worldwide)` |
| **Proof stack** | Verification tools the posting names |
| **Seniority** | `Intern`, `PhD`, `Postdoc`, `Engineer`, `Research engineer`, `Research scientist`, `Senior`, `Principal`, `Lead`, `Various` |
| **Last verified** | When a human last confirmed the posting was live |

Some entries also record work authorization, published pay, and a short note.
Those live in [`data/jobs.yml`](data/jobs.yml), which is the source of truth —
the table above is generated from it.

Closed roles move to [`data/archive.yml`](data/archive.yml) rather than being
deleted: knowing that a company was hiring for Lean work six months ago is
useful even when the posting is gone.

## Adding a job

Open a [new job issue](../../issues/new?template=new-job.yml) — it is a short
form, and no Git required. If you would rather send a pull request, add an entry
to `data/jobs.yml` and run:

```bash
pip install pyyaml jsonschema
python3 scripts/validate.py
python3 scripts/render.py
```

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
