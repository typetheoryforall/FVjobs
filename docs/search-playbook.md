# Search playbook

How we look for open formal verification roles, and what we learned doing it.
Read this before a search run and update it after one. Each run's audit list
lives in [`docs/search-runs/`](search-runs/). In Claude Code, the
[`fv-deep-search`](../.claude/skills/fv-deep-search/SKILL.md) skill runs the
whole method.

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
candidates in steps 1–3.

A search run looks for roles the board doesn't have. Re-verifying the roles
already on it is a separate job: the `recheck-jobs` skill
(`.claude/skills/recheck-jobs/`), which the maintainer runs on its own
schedule. Before searching, list what is already triaged (the board, the
archive, the watchlist and every earlier run file in
[`search-runs/`](search-runs/)), so the run spends its time elsewhere.

1. **Sweep the watchlist.** `scripts/check.py watchlist` queries every
   employer in [`scripts/watchlist.yml`](../scripts/watchlist.yml) and greps
   descriptions with the [FV regex](#keyword-filters). Its `[NEW]` lines are
   keyword hits to read, not candidates.
2. **Big-company careers search.** NVIDIA, Intel, SiFive, Samsung, Cadence and
   Marvell (Workday); AMD (Jibe); Qualcomm, then Microsoft, slowly (Eightfold);
   Arm and Synopsys (TalentBrew); Apple, Google and Amazon (search pages).
3. **Discovery, for roles and employers nobody thought of.** The watchlist
   only knows employers we have already seen, so give this step the most
   time.
   - Open boards: LinkedIn guest search with exact phrases, the Getro VC
     boards, YC's Work at a Startup, Wellfound and aisafety.com/jobs.
   - Employer rosters: sponsors and industry papers at CAV, FMCAD, ITP, POPL,
     CPP, DVCon and Lean Together; performers on FV research programmes
     (ARIA Safeguarded AI, DARPA); companies whose public repositories use
     Lean, Rocq, Isabelle, Dafny, Verus, TLA+ or SymbiYosys.
   - Web searches pairing the FV phrases with ATS domains (Ashby, Lever,
     Greenhouse, Workable, Personio, Teamtailor).
   - Each new employer found here: find its ATS slug and add it to the
     watchlist, even if it has nothing open today.
4. **Academic channels.**
   - TYPES-announce, Rocq Discourse jobs, ILLC positions, Logic List.
   - Then jobs.ac.uk, Inria, EPFL / TU Delft and AcademicTransfer.
5. **Hacker News "Who is hiring".** Low yield (0 in October 2026), but takes 30
   seconds with the items API.
6. **Triage.** Merge, de-duplicate by URL, drop candidates an earlier run file
   already lists unless something material changed, re-check each candidate
   independently, sort into recommend / your call / skip, give each one a
   [category and, where it applies, the big-company tag](#categories-and-tags),
   record the employer's posting date as `posted` (Ashby `publishedAt`, Lever
   `createdAt`, Greenhouse `first_published`, Workday `startDate`, Eightfold
   `postedTs`, Personio `createdAt`, amazon.jobs `posted_date`, or the date on
   the page; never an "updated" date or a "~2 weeks ago" estimate), and write
   the run file.
7. **Apply, after approval.** Add the approved roles without an `id` and run
   `python3 scripts/validate.py --assign-ids`. Archived roles keep the ID
   they have. A `[stale] FV-…` issue names the role by that ID.

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
| SmartRecruiters | `https://api.smartrecruiters.com/v1/companies/{company}/postings?q=...` (Bosch `BoschGroup`, `ServiceNow`, `AFRY`, Renesas `RenesasElectronics`) | `.../postings/{id}` returns `active`. `q` is fuzzy, so grep the postings. No lister in `check.py` yet. |
| PageUp | `https://careers.pageuppeople.com/{instance}/cw/en/listing/?page=1&page-items=100` (Imagination: 774) | Postings show "Apply now" while open. |
| BambooHR | `https://{org}.bamboohr.com/careers/list` with `Accept: application/json` (Codasip) | |
| Comeet | `https://www.comeet.co/careers-api/2.0/company/{uid}/positions?token={token}&details=true` (Ceva: uid `76.005`; the token is in the careers page) | Postings at `ceva-ip.com/career/position/{id}/`. Only `time_updated`, no posted date. |
| JOIN public API | `https://join.com/api/public/companies/{id}/jobs?page=1&pageSize=5` (YosysHQ: 166044) | `pageSize` must be 5 or less. Archived jobs return 410. |
| Workable public search | `https://jobs.workable.com/api/v1/jobs?query=...` (paged with `pageToken`) | Searches every Workable employer at once and returns full descriptions; 16 calls at 6 s spacing drew no 429 on 2026-11-13. Find an employer's slug with `apply.workable.com/api/v1/widget/accounts/{slug}`. |
| Gem | `https://api.gem.com/job_board/v0/{slug}/job_posts/` | Public JSON. |
| Rippling detail | `https://api.rippling.com/platform/api/ats/v1/board/{slug}/jobs/{uuid}` | Gives the pay range and created date (Positron, Bronco AI). |
| Phenom | BAE Systems `jobs.baesystems.com/global/en/search-results?keywords=...` | Search and job pages embed their data as `phApp.ddo` JSON. Fuzzy; read each job. |
| SenseHQ | L&T Technology Services `ltts.sensehq.com/careers/iframe/jobs?pageSize=250` | Jobs in `__NEXT_DATA__`. |

Slugs are not always the company name: `mistral.ai` (with the dot),
`pramaana-labs`, `convergentresearch` (Oath, and historically Lean FRO),
`asteralabs`, `axiommath`. Several obvious slugs belong to unrelated companies.
Ashby `cantina`, `formal`, `inference`, `compound`, `moonshot` and `theorem`,
Greenhouse `nexus` and `axiom`, and Lever `intersect`, `basis` and `mistral` are
all wrong or stale.

### Big-company careers systems

| System | Employers | How |
|---|---|---|
| Workday CXS | NVIDIA `nvidia.wd5` / `NVIDIAExternalCareerSite`; Intel `intel.wd1` / `External`; Samsung US `sec.wd3` / `Samsung_Careers`; Cadence `cadence.wd1` / `External_Careers`; SiFive `sifive.wd1` / `sifivecareers`; Marvell `marvell.wd1` / `MarvellCareers`; RTX/BBN `globalhr.wd5` / `REC_RTX_Ext_Gateway`; Thales `thales.wd3` / `Careers`; Airbus `ag.wd3` / `Airbus`; since 2026-11-05 also NXP `nxp.wd3` / `careers`, HPE `hpe.wd5` / `Jobsathpe`, Analog Devices `analogdevices.wd1` / `External`, Cisco `cisco.wd5` / `Cisco_Careers`, Broadcom `broadcom.wd1` / `External_Career`, Micron `micron.wd1` / `External`, GlobalFoundries `globalfoundries.wd1` / `External`, Altera `altera.wd1` / `Altera`; since 2026-11-09 also Microchip `microchiphr.wd5` / `External` (its public links use `wd5.myworkdaysite.com/recruiting/microchiphr/External/...`) and Axis `axis.wd3` / `External_Career_Site`; since 2026-11-13 also Ciena `ciena.wd5` / `Careers`, Draper `draper.wd5` / `Draper_Careers`, The Aerospace Corporation `aero.wd5` / `external`, RAND `rand.wd5` / `External_Career_Site` (works although rand.org is 403), Palo Alto Networks `paloaltonetworks.wd5` / `panwexternalcareers` and Boeing `boeing.wd1` / `EXTERNAL_CAREERS`. Wrong tenants (422): `renesas.wd1/wd3/wd5`, `infineon.wd3`, `lattice.wd1`, `ericsson.wd3`, and on 2026-11-13 `nokia.wd3`, `ti.wd5`, `amperecomputing.wd1`, `ampere.wd1`, `sandisk.wd1`, `wd.wd1`, `synaptics.wd5`, `lightmatter.wd1`, `llnl.wd1`, `pnnl.wd5`, `ornl.wd1`, `sri.wd1`, `honeywell.wd5`, `baesystems.wd3`. NXP's tenant was down for maintenance (500, then 422) all of 2026-11-09 | `POST https://{host}/wday/cxs/{tenant}/{site}/jobs` with `{"searchText":"formal verification","limit":20,"offset":0,"appliedFacets":{}}`. Detail: `GET https://{host}/wday/cxs/{tenant}/{site}{externalPath}` → `jobPostingInfo.canApply`, `startDate`, pay. Search is word-level and fuzzy ("formal" alone matches), so filter on the description. HTTP 422 = wrong tenant; S21 404 = right tenant, wrong site. |
| Eightfold PCSX | Qualcomm `careers.qualcomm.com`, Microsoft `apply.careers.microsoft.com`, Infineon `jobs.infineon.com` (domain `infineon.com`), since 2026-11-13 Ericsson `jobs.ericsson.com` (domain `ericsson.com`). STMicroelectronics `stmicroelectronics.eightfold.ai` answers 403 to PCSX: use the older v2 API, `/api/apply/v2/jobs?domain=stmicroelectronics.com&query=...` and `/api/apply/v2/jobs/{id}?domain=stmicroelectronics.com` (no lister in `check.py` yet) | `GET /api/pcsx/search?domain={domain}&query=...&start=0&sort_by=relevance` with a `Referer: https://{host}/careers?...` header; detail `/api/pcsx/position_details?position_id={id}&domain={domain}&hl=en`; public URL `/careers/job/{id}`. Microsoft rate-limits hard: on 2026-11-05 it answered 429 about every third call at 6 s spacing, and 12 s spacing with a 90 s back-off on 429 worked; on 2026-11-13 it answered 429 about every second call even at 12–15 s (17 429s in one lane), and the automated sweep failed on it, as it did on Qualcomm. Qualcomm answered 429 on page 2 and recovered after about 15 minutes; on 2026-11-09 14–15 s spacing worked with one 429. Ignore Microsoft postings whose only match is the boilerplate "formal validation of security invariants"; `Coq`, `Isabelle`, `Lean` and `F*` match hundreds of unrelated Microsoft jobs. |
| Jibe | AMD `careers.amd.com/api/jobs?keywords=formal&limit=100`; JHU APL `careers.jhuapl.edu/api/jobs?keywords=...` | Full descriptions. AMD pay is in `tags2`/`tags3`. |
| TalentBrew | Arm (org 33099, careers.arm.com), Synopsys (org 44408, careers.synopsys.com) | `GET /search-jobs/results?...&Keywords=formal&RecordsPerPage=100&SearchType=5` with `X-Requested-With: XMLHttpRequest`. Since 2026-11-09 the short form returns an empty `results` string; send the full parameter set (ActiveFacetID, Distance, OrganizationIds, SearchResultsModuleName, …) copied from the page. On 2026-11-13 the full form worked with `RecordsPerPage=100` and `CurrentPage` paging. Arm's ACL2 role only showed up for `theorem` or `ACL2`; both return 0 since it closed. Closed jobs 404 (Arm) or redirect home (Synopsys). Arm has reused a job ID for an unrelated role, so check the title. |
| Apple | `https://jobs.apple.com/en-us/search?search=%22formal%20verification%22&sort=newest&page=N` | Parse `window.__staticRouterHydrationData`; pay is in `postingFooters`. |
| Google | `https://www.google.com/about/careers/applications/jobs/results?q=...` | Grep `jobs/results/{id}-{slug}`. Unquoted `theorem proving`, `proof assistant` and `verified code` find DeepMind roles. `formal verification` returns mostly TPU/SoC hardware. |
| Amazon | `https://www.amazon.jobs/en/search.json?base_query=...&result_limit=100&sort=recent` | Best queries: `automated reasoning`, `formal methods`, `"formal verification"` (hardware), `Isabelle`, `Dafny`, `Lean theorem`, `neuro-symbolic`, `Zelkova`. Pay is only on the HTML page. Many twin requisitions share the same text under different IDs. |
| IBM | `POST https://www-api.ibm.com/search/api/v2` (appId `careers`, scope `careers2`) | Posting pages sit behind a bot challenge; the search API returns the full text. |
| Oracle Recruiting Cloud | Oracle OCI `eeho.fa.us2.oraclecloud.com/...recruitingCEJobRequisitions` (site `CX_45001`); SDU (site `CX_1001`); JPMorganChase `jpmc.fa.oraclecloud.com` (site `CX_1001`); University of Alberta `iaejup.fa.ocs.oraclecloud.com` | OCI: `keyword="formal methods"` returns more reqs than `TLA+`. JPMC: `Isabelle` or `TLA` isolates the AI Research reqs; `formal verification` is fuzzy. Detail: `recruitingCEJobRequisitionDetails` (`ExternalPostedStartDate`, `ExternalPostedEndDate`). |
| AdaCore | `https://www.adacore.com/api/careers` with `X-Requested-With: XMLHttpRequest` | Postings link to HelloTalent. |
| Meta | metacareers.com, in a browser | Plain fetches return only the page shell. LinkedIn guest search finds Meta's FV roles; confirm them in the browser pane (2 ASIC FV reqs on 2026-11-02). |
| iCIMS | Riverside Research `careers-riversideresearch.icims.com`, Peraton `careers-peraton.icims.com`, General Dynamics Mission Systems `careers-gdms.icims.com`, Stirling Dynamics `stirlingdynamics-jobs-expleo.icims.com` | No lister in `check.py` yet; read the posting page. |
| Avature | Siemens `jobs.siemens.com/.../SearchJobs/{query}` | Pages of 6 via `folderOffset`; Siemens, Bloomberg and Two Sigma take `?search=`, not `?keyword=`. |

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
| MathJobs | `https://www.mathjobs.org/jobs?action=joblist&id=fulltext:{query}` (fetch with `--compressed`) | Faculty and postdoc ads in AI for maths and formal reasoning (Alberta, CMU ICARM, CU Boulder in November 2026). |
| Varbi (Swedish universities) | `https://{uu,lu,kth}.varbi.com/en/` | Job lists for Uppsala, Lund and KTH; found the Uppsala numerical-verification postdoc. |
| Interfolio | `https://logic.interfolio.com/dossier-api/positions/{id}` | Returns `is_open` without a browser, for JS-only Interfolio postings. |
| Columbia | `https://academic.careers.columbia.edu/` | Replaced `academicjobs.columbia.edu` (no DNS since 2026-11-02). Angular; curl gets a Cloudflare 403, the browser works. Each result's `legacy_position_id` is its Interfolio id, which the Interfolio row above checks. |
| Institute pages | ISTA group pages, MPI-SWS research careers | Standing PhD and postdoc calls that never reach the lists. |
| IACR jobs board | `https://iacr.org/jobs/` (one page) | Cryptography posts, some asking for formal verification. The best new academic source on 2026-11-05 (found CWI's PhD). |
| ReachMee (Chalmers) | `web103.reachmee.com/ext/I003/304/main?site=5&lang=UK&validator=a72aeedd63ec10de71e46f8d91d0d57c` | The list returned 404 on 2026-11-09 without the `validator` parameter; with it, a plain GET works again (2026-11-13). Posting URLs work too. |

### Discovery sources

| Source | How | Notes |
|---|---|---|
| LinkedIn guest search | `https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=...&location=Worldwide&start=0` | No login. 429 after ~3 quick pages; wait 8–10 s between pages. Each call returns 10 cards, so step `start` by 10. `f_TPR=r1209600` limits to the last 14 days; descriptions come from `jobs-guest/jobs/api/jobPosting/{id}` (52 searches and 71 descriptions at 9–10 s drew no 429 on 2026-11-13). Stops at 100 results a query. Use exact phrases: `formal verification`, `formal methods`, `theorem proving`, `formal methods researcher` (15/15 relevant). Quotes are ignored on single tokens, so `Lean`, `Lean 4`, `Coq`, `Rocq`, `Isabelle`, `Dafny`, `TLA+` and `proof engineer` are noise. |
| Getro VC boards | `https://{board}/jobs?q=formal%20verification`, then parse `__NEXT_DATA__`. Since 2026-11-05 curl gets 403; WebFetch still works. | Working boards: jobs.accel.com, jobs.generalcatalyst.com, jobs.khoslaventures.com, jobs.electriccapital.com, careers.rainfall.com, jobs.luxcapital.com, jobs.dcvc.com, jobs.8vc.com. Found Pramaana, Bedrock Robotics, Mistral. |
| aisafety.com/jobs | WebFetch in chunks (~227k chars) | Found Resolution's Lean Engineer. |
| 80,000 Hours job board | `jobs.80000hours.org/?query=formal%20verification` in the browser (JS-only); `&jobPk=` exposes the employer's apply link | Found Sequent and Cogent Security on 2026-11-13. |
| HN Who is hiring | `curl https://hn.algolia.com/api/v1/items/{story_id}` and grep locally | Algolia keyword search is too fuzzy. Find the story id with `search_by_date?tags=story,author_whoishiring`. |
| Mercor / Alignerr | `work.mercor.com/jobs/list_{id}` (`"status":"active"`, and `disableApplications` must be false), `alignerr.com/jobs/{uuid}` (`isActive`); search with `alignerr.com/api/jobs?search=…` | Contract AI-training gigs; see scope calls. Alignerr's ~160 active Lean pages are city and retitled copies of a few listings. |
| CLEARSY | `POST https://clearsy.nos-recrutements.fr/api/job/list` with `{"page":N,"size":10}`; `GET /api/job/{id}` | Reads the board without a browser. Several roles are posted once per city. |
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

The watchlist lives in [`scripts/watchlist.yml`](../scripts/watchlist.yml),
where `scripts/check.py watchlist` reads it. Each employer is listed with its ATS and slug, or
with `ats: manual` and a note on how to check it by hand. It includes
employers with nothing open that have posted Lean, Rocq or FV roles in the
past year. Add every employer a run discovers.

On 2026-10-27, the in-scope roles were spread like this:

- Several each at Harmonic, Pramaana Labs, Astera Labs, Axiomise, LUBIS EDA,
  AWS and Microsoft.
- The most hardware roles at NVIDIA, about 13, and 2–10 each at Apple, Arm,
  AMD, Qualcomm, Intel, SiFive, Samsung, Synopsys, Cadence, Marvell and IBM.

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
- **No signal on 2026-11-02:**
  - Getro boards: 12 queries across 8 boards found only roles already on the
    board or FV as a nice-to-have, which the 2026-11-02 rule now includes, so
    search them again. Getro renders only the first 20 results, and its
    search API answers 406, so use narrow keywords.
  - aisafety.com/jobs: its FV roles were all on the board already.
  - Rail, automotive and defence: Siemens, Alstom, Hitachi Rail, Volvo,
    Zenseact, Peraton Labs, GrammaTech, JPL and NASA.
  - French and German firms: OCamlPro, AbsInt and Hensoldt.
  - Quant firms: HRT, DRW, Optiver, IMC, Jump, Tower, Two Sigma, Citadel and
    Bloomberg. FV is at most a bonus bullet there. The nice-to-have rule now
    includes those roles (Jump's Bristol verification engineer was added on
    2026-11-02), so read these boards again next run.
  - Teams with nothing open: Tarides, zkSecurity, Formal Land, Nomadic Labs,
    Reilabs and Bluerock. Ethereum Foundation's board is empty. Lean FRO has no
    jobs page.
- **Unreachable on 2026-11-02:**
  - Kestrel (connection refused again).
  - Informal Systems (server error in a browser).
  - Brevis (its careers link points to a missing Ashby board).
  - Ceva (`ceva-ip.com` doesn't resolve).
  - Columbia's `academicjobs.columbia.edu` doesn't resolve. It carries a Lean
    postdoc on agentic AI verification; check it by hand.
- **On 2026-11-05:**
  - Blocked or JS-only: Citadel 403, Two Sigma (TLS failure), Cognichip's
    Octopyd API 403, AdaCore's `/api/careers` now 400 to curl (read it in the
    browser), KU Leuven and DTU (JS-only), cra.org/ads 403, CNRS emploi and TU
    Wien (search only by submitting a form), DAMO Academy's API 403,
    ByteDance's 405.
  - Still unreachable: Kestrel (timeout), Ceva (DNS), Columbia's PeopleAdmin
    host (no A record), Siemens EDA's Avature search (timeout).
  - No FV today, so don't search them again soon: xAI, Poolside, Reflection
    AI, Thinking Machines, Magic, Cursor, Cognition, Imbue, Shield AI, Zoox,
    Skydio, Wayve, Databricks, Cloudflare, Stripe, SambaNova, d-Matrix,
    Cerebras, Quadric, Axelera AI, PsiQuantum, IonQ, PQShield, Consensys,
    Matter Labs, Aztec Labs, Offchain Labs, Uniswap Labs, Leidos, Northrop
    Grumman, Boeing and MITRE (V&V in the systems-engineering sense only).
  - The quant firms (HRT, DRW, Optiver, IMC, Tower, Bloomberg) have no FV in
    any description; they are on the watchlist so the sweep catches a change.
  - Chipstack now redirects to Cadence, which acquired it.
- **On 2026-11-09:**
  - Reachable again: Ceva (`ceva-ip.com/career/`, Comeet) and Kestrel (careers page says "Coming soon…").
  - Still unreachable: Columbia's PeopleAdmin host (no DNS), Qualitest's careers site (expired TLS certificate), rand.org (403).
  - NXP's Workday tenant was down for maintenance all day, so NXP was neither swept nor re-checked.
  - No FV today: Hashberg, GLAIVE, Entropy42, Proofinity (parked), Oraclizer, Portofino, Paradigm, Eigen Labs, TTTech (TTTech Auto is now Trustmotion, on NXP's Workday), Ferrous Systems (its January post is 404), QEDIT, Predictable Machines, Tarides, Reilabs, Informal Systems, IOG.
  - The HN November thread (story 50338728) had one FV hit, ChainSecurity, already on the board.
  - Recruiter posts (Spectrum IT, Mulya, PERSOL, Actalent) name no client; they are leads, never candidates.
  - LinkedIn: `proof assistant` returns paralegal jobs; `theorem proving` and `formally verified` match loosely.
  - Getro files acquired companies under the old name (Chronosphere = Palo Alto Networks, Swiftkey = Microsoft, Instana = IBM).
- **On 2026-11-13:**
  - The automated sweep failed on Microsoft and Qualcomm (429) and on NXP (Workday maintenance, again all day). Microsoft and Qualcomm finished by hand at 13–15 s spacing; NXP was neither swept nor re-checked.
  - Still blocked: Qualitest (expired certificate; the browser refuses it too), Siemens EDA's Avature search (timeout), academicjobs.com and scholarshipdb.net (403), Cognichip's job API (403 "authorized domains only"; read posting pages in the browser), Qubika (Cloudflare on 5 of 11 postings), YC Work at a Startup (blank without login), Wellfound (404), Zellic's Notion job subpages (do not render).
  - No FV today: about 90 Ashby, Greenhouse and Lever boards probed by lane 4 (among them MongoDB, PingCAP, CockroachLabs, Ripple, Coinbase, Cantina, Cerebras, Cohere, Scale AI, JetBrains, Thinking Machines), Groq, NextSilicon, StarkWare, SRI, Boeing (its El Segundo DV pair has no FV), UNSW Trustworthy Systems, ETH PLF, Radboud, Twente, TU/e, ILLC, the Logic List, cstheory-jobs, DBWorld (stale since 2021).
  - FV companies with no careers page: Asymptotic, Axiomat, Proofcraft, CE Labs, Atlas Computing, Hodge Labs, Grothendieck Labs, Pi Squared, Tau Ceti, Project Numina, Corca.
  - Rosters: ARIA Safeguarded AI lists only TA1.1 teams (TA2 and TA3 Phase 2 were cancelled in November 2025); DARPA expMath's teams are university-led, PROVERS names only BAE FAST Labs. FLoC 2026's sponsors add only Ndea.
  - The keyword sweep's four biggest groups are pure noise: Anduril (134, Lean manufacturing), Code Metal (37, company blurb), Relativity Space (18) and Zipline (10). CertiK, Harmonic and Pramaana match only on their company blurb.
  - URL de-duplication misses earlier candidates that run files cite only by requisition ID or title (36 of the 566 sweep leads). Match requisition IDs too.
  - The HN November thread had 28 new top-level comments since 2026-11-09, none FV.
- **Google DeepMind's Greenhouse board is gone (404).** DeepMind roles are now
  only on Google Careers.
- **The HN "Who is hiring" thread** appears around 15:00–16:00 UTC on the
  first weekday of the month. A run earlier that day has to come back for it.
- **`site:` filters are ignored by the search tool.** Query ATS APIs directly
  instead.

## Scope calls

How borderline cases were sorted on 2026-10-27. These follow the README scope.
Reuse them so triage stays consistent.

- **Include nice-to-have FV.** A role counts when the posting names formal
  verification, formal methods or a proof tool in its duties or among its
  preferred, desired or bonus qualifications, even if the rest of the job is
  general DV, SWE, ML, cryptography or protocol work. Say in `notes` that FV
  is a nice-to-have. On 2026-11-02 the maintainer asked for this more
  permissive rule. It replaces the 2026-10-27 rule, which skipped these
  roles (OpenAI chip design, Anthropic RL, Oracle OCI TLA+, most crypto
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
- **Skip** duplicate requisitions, posts closing within about a week, stale
  pages, and roles where FV is incidental: named only in the company blurb or
  a team description, not in the job's duties or qualifications. A
  nice-to-have bullet is not incidental (see above). The maintainer dropped
  every "recommended skip" on 2026-10-27, which confirms the other rules.
- **Hardware FV is in scope.** It dominates by volume, so the search caps it
  at 5 roles per employer: the board's open hardware roles plus the run's
  additions. Count by parent company (Amazon Leo and Annapurna Labs are both
  Amazon). Record the rest as counts with the search that finds them. The
  maintainer raised the cap from about 3 to 5 on 2026-11-02.
- **Open-application entries** stay only while the employer's page still
  invites applications. Empty boards (Imandra's Workable, Cryspen's JOIN)
  mean archive.
- **Over the cap means counted, not listed.** The cap covers roles found on
  employers' own sites as well as in the sweep. Give over-the-cap roles IDs
  in the audit list so the maintainer can pull one in. To fill an employer
  up to the cap, prefer core FV roles, then locations and levels the board
  doesn't have yet, and fold twin requisitions into one entry.
- **Evergreen postings** (Prover's 2023 rail role, Huawei Dresden's 2023
  intern ad) are live but old. Flag the first-published date in `notes`.
- **Core or nice-to-have** (used to split the audit list from 2026-11-05):
  core when FV, formal methods or a proof tool is in the duties or the
  required qualifications, even as one DV bullet; nice-to-have when it is
  only preferred or a bonus. FV as one of about five or more alternatives,
  or only as context, goes to "your call".
- **AI for hardware design** roles (AMD's AI-for-RTL roles, FV-173, FV-190)
  are `hardware`, so they count toward the employer's cap.
- **Filling a cap when several lanes found roles:** recommended core first,
  then recommended nice-to-have, then "your call"; within each, prefer
  locations and levels the board doesn't have.
- **Reposted or re-dated postings** keep their first `posted` date (Systerel,
  2026-11-05).
- **A freed cap slot is a material change.** When a re-check archives an
  employer's hardware role, the strongest role an earlier run held back only
  for the cap becomes eligible again (Apple, Arm and Microsoft on 2026-11-13).
- **Labour-certification (PERM) postings** ("Multiple openings", "existing
  vacancy", "various unanticipated locations") go to "your call", however
  strong (Apple and Samsung on 2026-11-05, AMD on 2026-11-13).
- **A repost of an archived role** (same SmartRecruiters uuid, new ID) is
  restores the archived entry with its ID, new URL and title (Bosch FV-249
  and FV-250, approved 2026-11-13).

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
NVIDIA, Qualcomm, RTX BBN, Samsung, Snowflake, Synopsys and Thales. The
2026-11-05 run added Oracle, NXP, HPE, Bosch, Analog Devices, Cisco, Micron,
GlobalFoundries, Altera, Broadcom, AFRY and ServiceNow, and the maintainer added
Anthropic, OpenAI and Anduril. The 2026-11-09 run added Microchip, Renesas,
Infineon, General Dynamics Mission Systems, JPMorganChase and Axis
Communications (about 5,000 staff, the borderline). The 2026-11-13 run added
STMicroelectronics, Ciena, Ericsson, Palo Alto Networks and BAE Systems. Not tagged: Draper, Semidynamics,
Positron AI, Codasip, OLIX, Fidus Systems, Cirrus Logic, Ceva,
Neurophos, Baya Systems, Architect Labs and Stirling Dynamics, and also not: Jane
Street (about 3,000 staff), Astera Labs, SiFive, Tenstorrent, Mistral,
Imagination, Graphcore, Codasip, Mirafra, Riverlane, and the national labs and
universities.

## Ideas for the next run

- **Extend `check.py watchlist`** to the TalentBrew (Arm, Synopsys), Apple, Google and
  IBM search pages, which are still done by hand, and give Microsoft and
  Qualcomm a slower schedule (13–15 s, with a 90 s back-off), since the sweep
  fails on them.
- **Add listers** for the sources still read by hand: iCIMS (Riverside Research,
  Peraton, GDMS), Avature (Siemens), SuccessFactors (EPFL, TU Delft),
  SmartRecruiters (Bosch, Renesas, AFRY, ServiceNow), PageUp (Imagination),
  Oracle Recruiting Cloud, Comeet (Ceva), Rippling (Positron, Bronco AI), the
  Eightfold v2 API (STMicroelectronics), the CLEARSY JSON API and LinkedIn guest
  search. Teach `check.py board` the `wd5.myworkdaysite.com/recruiting/...` URL
  form (Microchip).
- **Match requisition IDs, not just URLs,** when building the already-triaged list.
- **Re-check NXP** (FV-340 to FV-344) once its Workday is back; left unchanged on
  2026-11-09 and 2026-11-13.
- **Follow up these leads:** Ericsson's Silicon Front End CAD Engineer (Austin,
  JasperGold), Tenstorrent's Bangalore FV Engineer (LinkedIn 4487457793, not on
  its Greenhouse board), Zellic's job pages, Qubika, Spectrum IT's Oxfordshire
  Formal Methods Engineer pair (client still unidentified), and Aarhus GSNS's PhD
  call, which opens 2026-12-01.
- **Kry10 (FV-183):** its careers page no longer lists the role, though the PDF
  still loads.

## Run log

| Date | Candidates | Recommended | Added to the board | Run file |
|---|---|---|---|---|
| 2026-10-27 | 149 | 100 (+25 your call) | 125 (all recommended and your call; 2 archived) | [2026-10-27](search-runs/2026-10-27.md) |
| 2026-11-02 | 73 | 25 (+17 your call, 12 over the cap) | 61 (all recommended and your call, 17 filling the new cap of 5, 2 under the nice-to-have rule; 1 archived) | [2026-11-02](search-runs/2026-11-02.md) |
| 2026-11-05 | 297 | 179: 88 core FV, 91 FV as a nice-to-have (+43 your call, 51 over the cap) | 179 (all recommended; FV-213 to FV-391) | [2026-11-05](search-runs/2026-11-05.md) |
| 2026-11-09 | 116 (57 + 27 your call + 23 over the cap + 9 skip) | 57: 37 core FV, 20 FV as a nice-to-have (+27 your call, 23 over the cap) | 57 (all recommended; FV-392 to FV-448) | [2026-11-09](search-runs/2026-11-09.md) |
| 2026-11-13 | 114 (58 + 33 your call + 23 skip; over-the-cap roles counted) | 58: 40 core FV, 18 FV as a nice-to-have (+33 your call) | 58 (all recommended; FV-451 to FV-506, and FV-249 and FV-250 restored) | [2026-11-13](search-runs/2026-11-13.md) |
