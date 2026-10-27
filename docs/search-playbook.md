# Search playbook

How we look for open formal verification roles, and what we learned doing it.
Read this before a search run and update it after one. Each run's audit list
lives in [`docs/search-runs/`](search-runs/).

## Ground rules

- **Live means the employer's own posting.** Confirm every role on the
  employer's page or ATS API on the day you record it. A search snippet, a
  LinkedIn card, an HN comment or an aggregator copy is a lead, not evidence.
- **A 200 is not proof.** Google Careers, Workday and several SPA boards return
  200 for removed jobs. Check that the job body comes back: the Workday detail
  JSON (`canApply`), the Ashby or Lever API listing, or the "Minimum
  qualifications" block on Google.
- **Academic posts:** the deadline must be on or after the day you verify, or
  the post must be rolling with no sign it has been filled. Put the deadline in
  `notes`.
- **Prefer the APIs.** ATS JSON endpoints are exact and cheap, and they give
  posting dates. Scrape HTML only when there is no API.
- **Respect rate limits and bot checks.** If a site serves a challenge (IBM,
  metacareers) or HTTP 429 (Workable, Microsoft, LinkedIn), slow down or check
  the page by hand in a browser. Do not try to get around the challenge.
- **Read-only.** Never apply, sign in or submit forms while searching.
- **Audit before merge.** A run produces a candidate list with confidence and
  FV relevance. A maintainer approves it before anything goes into
  `data/jobs.yml`.

## Run order

Best yield per minute first. The 2026-10-27 run found about 80% of its
candidates in steps 2–4.

1. **Re-verify the board.** For every `jobs.yml` entry, query its ATS API (see
   the cookbook). Note changed locations, titles and redirects. Move closed
   roles to `archive.yml`.
2. **Sweep the watchlist.** Query every employer in the [watchlist](#watchlist)
   through its endpoint and grep descriptions with the [FV regex](#keyword-filters).
3. **Big-company careers search.** NVIDIA, Intel, SiFive, Samsung, Cadence and
   Marvell (Workday); AMD (Jibe); Qualcomm, then Microsoft, slowly (Eightfold);
   Arm and Synopsys (TalentBrew); Apple, Google and Amazon (search pages).
4. **Discovery, for employers nobody thought of.**
   - LinkedIn guest search with exact phrases.
   - Getro VC boards.
   - aisafety.com/jobs.
   - Each new employer found here: find its ATS slug and add it to the watchlist.
5. **Academic channels.**
   - TYPES-announce, Rocq Discourse jobs, ILLC positions, Logic List.
   - Then jobs.ac.uk, Inria, EPFL / TU Delft and AcademicTransfer.
6. **Hacker News "Who is hiring".** Low yield (0 in October 2026), but takes 30
   seconds with the items API.
7. **Triage.** Merge, de-duplicate by URL, re-check each candidate
   independently, sort into recommend / your call / skip, give each one a
   [category and, where it applies, the big-company tag](#categories-and-tags),
   record the employer's posting date as `posted` (Ashby `publishedAt`, Lever
   `createdAt`, Greenhouse `first_published`, Workday `startDate`, Eightfold
   `postedTs`, Personio `createdAt`, amazon.jobs `posted_date`, or the date on
   the page; never an "updated" date or a "~2 weeks ago" estimate), and write
   the run file.

## Endpoint cookbook

### ATS boards (most startups and mid-size firms)

| ATS | List | One posting / notes |
|---|---|---|
| Ashby | `https://api.ashbyhq.com/posting-api/job-board/{org}` (add `?includeCompensation=true` for pay) | Match `jobUrl`. `secondaryLocations` is often the only place extra cities appear. `{"jobs":[]}` (28 bytes) means the org exists but is empty; `Not Found` means a wrong slug. |
| Ashby GraphQL (fallback when the posting API is off, e.g. Chainlink) | `POST https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams` with `organizationHostedJobsPageName` | `op=ApiJobPosting` returning `null` proves a posting is closed. |
| Lever | `https://api.lever.co/v0/postings/{org}?mode=json` (EU: `api.eu.lever.co`) | `.../postings/{org}/{id}`: 200 = live, 404 = closed. `createdAt` is in ms. |
| Greenhouse | `https://boards-api.greenhouse.io/v1/boards/{org}/jobs?content=true` (works for EU boards too) | `.../jobs/{id}`: 200 = live. Custom domains carry `?gh_jid=` (Waymo → board `waymo`). |
| Workable | `https://apply.workable.com/api/v1/widget/accounts/{org}`; `POST https://apply.workable.com/api/v3/accounts/{org}/jobs` with `{"query":"","location":[],"department":[],"worktype":[],"remote":[]}` | `.../api/v2/accounts/{org}/jobs/{shortcode}`. **Rate-limits (429, Cloudflare 1015) after ~60 requests, and the block lasts hours.** Query Workable once, early, and space calls. |
| Personio | `https://{org}.jobs.personio.de/xml?language=en` | Posting `https://{org}.jobs.personio.de/job/{id}`. |
| Teamtailor | `https://{host}/jobs.rss` (e.g. careers.certora.com) | Full list with `pubDate`. |
| JOIN | `https://join.com/companies/{slug}` | "No available jobs" when empty; archived jobs return 410. |
| Rippling | `https://api.rippling.com/platform/api/ats/v1/board/{slug}/jobs` | Slug is in the careers HTML as `data-job-board-id`. |

Slugs are not always the company name: `mistral.ai` (with the dot),
`pramaana-labs`, `convergentresearch` (Oath, and historically Lean FRO),
`asteralabs`, `axiommath`. Several obvious slugs belong to unrelated companies.
Ashby `cantina`, `formal`, `inference`, `compound`, `moonshot` and `theorem`,
Greenhouse `nexus` and `axiom`, and Lever `intersect`, `basis` and `mistral` are
all wrong or stale.

### Big-company careers systems

| System | Employers | How |
|---|---|---|
| Workday CXS | NVIDIA `nvidia.wd5` / `NVIDIAExternalCareerSite`; Intel `intel.wd1` / `External`; Samsung US `sec.wd3` / `Samsung_Careers`; Cadence `cadence.wd1` / `External_Careers`; SiFive `sifive.wd1` / `sifivecareers`; Marvell `marvell.wd1` / `MarvellCareers`; RTX/BBN `globalhr.wd5` / `REC_RTX_Ext_Gateway`; Thales `thales.wd3` / `Careers`; Airbus `ag.wd3` / `Airbus` | `POST https://{host}/wday/cxs/{tenant}/{site}/jobs` with `{"searchText":"formal verification","limit":20,"offset":0,"appliedFacets":{}}`. Detail: `GET https://{host}/wday/cxs/{tenant}/{site}{externalPath}` → `jobPostingInfo.canApply`, `startDate`, pay. Search is word-level and fuzzy ("formal" alone matches), so filter on the description. HTTP 422 = wrong tenant; S21 404 = right tenant, wrong site. |
| Eightfold PCSX | Qualcomm `careers.qualcomm.com`, Microsoft `apply.careers.microsoft.com` | `GET /api/pcsx/search?domain={domain}&query=...&start=0&sort_by=relevance` with a `Referer: https://{host}/careers?...` header; detail `/api/pcsx/position_details?position_id={id}&domain={domain}&hl=en`; public URL `/careers/job/{id}`. Microsoft rate-limits hard, so space calls 5 s or more. Ignore Microsoft postings whose only match is the boilerplate "formal validation of security invariants". |
| Jibe | AMD `careers.amd.com/api/jobs?keywords=formal&limit=100`; JHU APL `careers.jhuapl.edu/api/jobs?keywords=...` | Full descriptions. AMD pay is in `tags2`/`tags3`. |
| TalentBrew | Arm (org 33099, careers.arm.com), Synopsys (org 44408, careers.synopsys.com) | `GET /search-jobs/results?...&Keywords=formal&RecordsPerPage=100&SearchType=5` with `X-Requested-With: XMLHttpRequest`. Arm's ACL2 role only shows up for `theorem` or `ACL2`. Closed jobs 404 (Arm) or redirect home (Synopsys). Arm has reused a job ID for an unrelated role, so check the title. |
| Apple | `https://jobs.apple.com/en-us/search?search=%22formal%20verification%22&sort=newest&page=N` | Parse `window.__staticRouterHydrationData`; pay is in `postingFooters`. |
| Google | `https://www.google.com/about/careers/applications/jobs/results?q=...` | Grep `jobs/results/{id}-{slug}`. Unquoted `theorem proving`, `proof assistant` and `verified code` find DeepMind roles. `formal verification` returns mostly TPU/SoC hardware. |
| Amazon | `https://www.amazon.jobs/en/search.json?base_query=...&result_limit=100&sort=recent` | Best queries: `automated reasoning`, `formal methods`, `"formal verification"` (hardware), `Isabelle`, `Dafny`, `Lean theorem`, `neuro-symbolic`, `Zelkova`. Pay is only on the HTML page. Many twin requisitions share the same text under different IDs. |
| IBM | `POST https://www-api.ibm.com/search/api/v2` (appId `careers`, scope `careers2`) | Posting pages sit behind a bot challenge; the search API returns the full text. |
| Oracle Recruiting Cloud | Oracle OCI `eeho.fa.us2.oraclecloud.com/...recruitingCEJobRequisitions` (site `CX_45001`); SDU (site `CX_1001`) | OCI's hits are distributed-systems roles with a single TLA+ bullet, so all were skipped. |
| AdaCore | `https://www.adacore.com/api/careers` with `X-Requested-With: XMLHttpRequest` | Postings link to HelloTalent. |

### Academic sources

| Source | How |
|---|---|
| TYPES-announce | `https://lists.seas.upenn.edu/pipermail/types-announce/{year}/date.html`. Links are wrapped in urldefense. **The single best academic source.** |
| Rocq Discourse jobs | `https://discourse.rocq-prover.org/c/announcements/jobs/26.json` (subcategory 26, hidden from `/categories.json`); topics via `/t/{id}.json`. |
| ILLC open positions | `https://www.illc.uva.nl/NewsandEvents/News/Positions/`. Logic/FM jobs with explicit deadlines. |
| Logic List | `https://resources.illc.uva.nl/LogicList/` (`newsitem.php?id=N`, jobs prefixed "CfA:"). |
| jobs.ac.uk | `https://www.jobs.ac.uk/search/?keywords=...&pageSize=100`. Queries: `Isabelle`, `formal+verification`, `formalisation`, `Lean+4`, `verification+PhD`. Ads appear the same day. |
| Inria | `https://jobs.inria.fr/public/classic/en/offres` lists every offer on one page; the keyword parameter is ignored, so filter titles locally. |
| EPFL, TU Delft (SuccessFactors) | `https://careers.epfl.ch/search/?q=...&searchResultView=LIST` (same for `careers.tudelft.nl`). Queries: verification, proof, Lean, Rocq, theorem. |
| AcademicTransfer (NL) | `https://www.academictransfer.com/en/jobs/?q=proof%20assistant` |
| AAR newsletter | Latest issue linked from `https://aarinc.org/` (13 job ads in September 2026). |
| Terence Tao's blog | Carries AI-plus-Lean academic adverts (found the EPFL numerical-analysis postdoc). |

### Discovery sources

| Source | How | Notes |
|---|---|---|
| LinkedIn guest search | `https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=...&location=Worldwide&start=0` | No login. 429 after ~3 quick pages; wait 8–10 s between pages. Use exact phrases: `formal verification`, `formal methods`, `theorem proving`, `formal methods researcher` (15/15 relevant). Single tokens (`Lean`, `Coq`, `TLA+`, `proof engineer`) are noise. |
| Getro VC boards | `https://{board}/jobs?q=formal%20verification`, then parse `__NEXT_DATA__` | Working boards: jobs.accel.com, jobs.generalcatalyst.com, jobs.khoslaventures.com, jobs.electriccapital.com, careers.rainfall.com, jobs.luxcapital.com, jobs.dcvc.com, jobs.8vc.com. Found Pramaana, Bedrock Robotics, Mistral. |
| aisafety.com/jobs | WebFetch in chunks (~227k chars) | Found Resolution's Lean Engineer. |
| HN Who is hiring | `curl https://hn.algolia.com/api/v1/items/{story_id}` and grep locally | Algolia keyword search is too fuzzy. Find the story id with `search_by_date?tags=story,author_whoishiring`. |
| Mercor / Alignerr | `work.mercor.com/jobs/list_{id}` (`"status":"active"`), `alignerr.com/jobs/{uuid}` (`isActive`) | Contract AI-training gigs; see scope calls. |
| Lean Zulip archive | `https://leanprover-community.github.io/archive/stream/284757-job-postings/index.html` | **Stale since 2026-02-28.** Still a good roster of employers to add to the watchlist. |

## Keyword filters

Grep job descriptions, not titles. This regex works across ATS dumps:

```
\bLean ?4\b|\bLean\b|\bCoq\b|\bRocq\b|Isabelle|formal verification|formal method|theorem prov|proof assistant|autoformali|formal proof|formal math|mathlib|\bDafny\b|\bVerus\b|TLA\+|JasperGold|VC Formal|SymbiYosys|ACL2|Frama-C|SPARK|Atelier B
```

Then read the context. "Lean" hits lean manufacturing and "lean team", "SMT"
hits surface-mount technology, and "Cedar" hits Cedar Rapids. For hardware,
title filters (`Formal`, `Theorem`, `Equivalence`, `LEC`) plus counting
"formal" in the body (three or more mentions triggers a manual look) catch
mis-titled roles such as Cadence's "Software Engineer II" on Conformal LEC.

## Watchlist

Employers that had in-scope roles on 2026-10-27, or have posted them recently,
and where to look. "FV now" counts in-scope roles open on that date.

| Employer | Where | FV now |
|---|---|---|
| Harmonic | Ashby `harmonic` | 3 |
| Pramaana Labs | Ashby `pramaana-labs` | 4 |
| Mistral AI | Ashby `mistral.ai` | 1 |
| Axiom Math | Ashby `axiommath` | 1 |
| Resolution | Ashby `resolution` | 1 |
| Code Metal | Ashby `code-metal` | 1 |
| MatX, Etched | Ashby `matx`, `etched` | 1 each |
| SF Tensor, Snowflake, Bedrock Robotics | Ashby `sf-tensor`, `snowflake`, `bedrock-robotics` | 1 each |
| Oath Technologies (Convergent Research) | Lever `convergentresearch` | 2 |
| CertiK | Lever `certik` | 2 |
| Nuvacore, Velaura | Lever `nuvacore`, `velaura` | 1 each |
| Quantinuum | Lever EU `quantinuum` | 1 |
| Jane Street | Greenhouse `janestreet` | 1 (London and NY reqs) |
| Tenstorrent, Astera Labs, Waymo | Greenhouse `tenstorrent`, `asteralabs`, `waymo` | 1, 4, 1 |
| Galois, Trail of Bits | Workable `galois`, `trailofbits` | 2, 1 |
| Axiomise, LUBIS EDA | Personio `axiomise`, `lubis-eda` | 4, 3 |
| AWS (Automated Reasoning, Crypto Libraries, Annapurna, Leo) | amazon.jobs search.json | ~10 software, ~5 hardware |
| Microsoft (MSR software verification, silicon) | Eightfold PCSX | 4 software, 2 hardware |
| Google / DeepMind | Google Careers search | 1 Lean, ~4 hardware |
| NVIDIA | Workday | 3 software/compiler, ~13 hardware |
| Apple, Arm, AMD, Qualcomm, Intel, SiFive, Samsung, Synopsys, Cadence, Marvell, IBM | see cookbook | 2–10 each, hardware |
| RTX BBN, Thales, Airbus | Workday (see cookbook) | 2, 2, 1 |
| JHU APL | Jibe API | 1 |
| Sandia | sandia.jobs (JS only; browser) | 1 |
| CLEARSY | clearsy.nos-recrutements.fr (JS only; browser) | 2–3 |
| AdaCore | AdaCore careers API | 1 |
| TrustInSoft | trust-in-soft.com/careers | 1 |
| Mobileye | careers.mobileye.com | 1 |
| Cognichip | cognichip.ai/careers (list), Octopyd (detail, JS) | 1 |
| General Diffusion | generaldiffusion.com/careers | 1 |
| YosysHQ | join.com `yosyshqcom` | 1 |
| Beneficial AI Foundation, Theorem, Runtime Verification, Veridise | their careers pages | open applications or single pages |

Watch these even though they had nothing open. They have posted Lean, Rocq or FV
roles in the past year:

- Ashby `ethereum-foundation` and `category-labs`.
- Certora's Teamtailor RSS.
- Greenhouse `logicalintelligence`.
- Lean FRO (historically via Convergent's Lever).
- ARIA's Pinpoint feed (`aria.pinpointhq.com/postings.json`).
- Huawei UK Teamtailor RSS (`huaweiuk.teamtailor.com/jobs.rss`).
- Renaissance Philanthropy careers.
- MAISI.
- Tarides, Bluerock, Nomadic Labs, Formal Land, zkSecurity, Reilabs.

## Dead ends and blocked sources

Skip these, or handle them differently, next time.

- **Blocked or JS-only:**
  - metacareers.com: needs a browser.
  - tesla.com: 403.
  - IBM posting pages: bot challenge, but the search API works.
  - Interfolio: use the Chronicle mirror.
  - findaphd, academicpositions and Imperial jobs: 403.
  - EURAXESS ignores its keyword parameter.
  - Welcome to the Jungle: no anonymous search.
  - YC Work at a Startup, Wellfound and Indeed: 406, 404 and 403.
- **Behind anti-harvest gates** (needs a subscribed human): the Isabelle users
  list, coq-club and the Agda list.
- **Lean Zulip `#job postings`:** the public archive stopped on 2026-02-28 and
  the live API needs login. **The biggest gap in coverage.** Ask someone with a
  Zulip account to export the stream.
- **No signal this run:** web3.career tag pages, cryptocurrencyjobs.co,
  cryptojobslist, useweb3 (defunct), EuroProofNet jobs (stale since May 2025),
  ocaml.org/jobs, and the HN October 2026 thread.
- **`site:` filters are ignored by the search tool.** Query ATS APIs directly
  instead.

## Scope calls

How borderline cases were sorted on 2026-10-27. These follow the README scope.
Reuse them so triage stays consistent.

- **Skip** when FV is a "nice to have" bullet in a general SWE, DV, ML or
  protocol role (OpenAI chip design, Anthropic RL, Oracle OCI TLA+, most crypto
  auditor roles).
- **Fold** twin requisitions of the same role into one entry with several
  locations (Jane Street London/NY, Cognichip, Velaura, AWS twin reqs).
- **Skip** academic posts closing within about a week of the run; they will
  have closed by the time readers see them.
- **Include** contract AI-training gigs (Mercor, Alignerr), management roles
  on FV teams, roles that build tooling *for* FV, posts evidenced only by a
  mailing-list message, and faculty calls. These were "your call" on
  2026-10-27 and the maintainer took all of them, so recommend them from now
  on. Keep "your call" for kinds of borderline case not listed here.
- **Skip** duplicate requisitions, posts closing within about a week, roles
  where FV is incidental, and stale pages. The maintainer dropped every
  "recommended skip" on 2026-10-27, which confirms these rules.
- **Hardware FV is in scope.** It dominates by volume, so the search caps at
  about 3 roles per employer and records the rest as counts with the search
  that finds them.
- **Open-application entries** stay only while the employer's page still
  invites applications. Empty boards (Imandra's Workable, Cryspen's JOIN)
  mean archive.

## Categories and tags

Every entry needs a `category`; CONTRIBUTING.md defines the values. How the
2026-10-27 run assigned them:

- `hardware`: RTL and SoC formal (SVA, JasperGold, VC Formal, equivalence
  checking), and theorem proving about ISAs and microarchitecture (Arm's ACL2
  role).
- `software`: program verification, automated reasoning, verified compilers
  and crypto libraries, and industry labs (AWS, MSR, Galois) and government
  labs (Sandia, JHU APL, RTX BBN).
- `ai-for-proof`: the product is AI that writes or checks proofs, or
  autoformalization (Harmonic, Axiom, DeepMind's Lean role, Pramaana, Math
  Inc, Mathlib Initiative, and the Lean training-data gigs).
- `academic`: university and research-institute posts (PhD, postdoc, faculty,
  research engineer at EPFL, Inria).
- `cryptocurrency`: blockchain, smart contracts and ZK (CertiK, Runtime
  Verification, Veridise). Cryptography that is not about blockchains stays in
  `software`.

Tag `big-company` on big tech, the major chip, EDA and aerospace groups, and
their subsidiaries (roughly 5,000 staff or more). On 2026-10-27: Airbus,
Amazon/AWS (including Annapurna and Leo), AMD, Apple, Arm, Cadence, Google
(including DeepMind and Waymo), IBM, Intel, Marvell, Microsoft, Mobileye,
NVIDIA, Qualcomm, RTX BBN, Samsung, Snowflake, Synopsys and Thales. Not
tagged: Jane Street (about 3,000 staff), Astera Labs, SiFive, Tenstorrent,
Mistral, and the national labs and universities.

## Ideas for the next run

- **Script the watchlist sweep.** Most of steps 1–3 is deterministic API calls.
  A `scripts/sweep.py` that reads the watchlist and prints FV-matching postings
  with dates would cut a run from hours to minutes, leaving people for
  discovery and triage.
- **Cover employers skipped this run for time:**
  - Rail and automotive: Siemens (jobs.siemens.com), Alstom, Hitachi Rail,
    Volvo / Zenseact.
  - French and German formal-methods firms: Systerel, Prover Technology,
    OCamlPro, AbsInt, Hensoldt Cyber.
  - US defence research: Riverside Research, Peraton Labs, GrammaTech.
  - Huawei (Edinburgh, Paris, Munich).
  - NASA / JPL.
  - Quant firms.
- **Try Lagrange and Brevis in a browser**, and retry Informal Systems and
  Kestrel (connection refused all day).

## Run log

| Date | Candidates | Recommended | Added to the board | Run file |
|---|---|---|---|---|
| 2026-10-27 | 149 | 100 (+25 your call) | 125 (all recommended and your call; 2 archived) | [2026-10-27](search-runs/2026-10-27.md) |
