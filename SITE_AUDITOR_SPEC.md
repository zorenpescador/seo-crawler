# WEM SEO Crawler — Site Auditor Specification

**Feature:** SEMrush-style Site Auditor (Full Parity)
**Extends:** `wem-seo-crawler` (existing `seo_crawler/core.py` + `streamlit_app.py` + `cli.py`)
**Author:** Claude, for WEM No-Code B.V.
**Status:** Draft for review
**Date:** July 23, 2026

---

## 1. Problem Statement

The current crawler does solid single-page, on-page SEO scraping (titles, metas,
H1s, word count, schema, alt text) plus WEM-specific keyword/brand checks. It
cannot answer the questions a real site audit tool answers: *Is the site
structurally healthy? Are there broken links, redirect chains, duplicate
content, or crawlability blockers site-wide? How does overall site health
compare over time?*

Today, answering those questions means paying for SEMrush's Site Audit tool or
manually spot-checking pages. WEM's SEO/marketing team needs an internal,
free, WEM-branded equivalent that:
- Runs the same category of checks SEMrush's Site Audit runs (~140 checks
  across crawlability, HTTPS, redirects, duplicate content, internal linking,
  international SEO, structured data, and performance proxies)
- Rolls results up into a single **Site Health Score**, so a non-technical
  stakeholder can see "is this getting better or worse" at a glance
- Cross-references findings against WEM's own priority keyword map and brand
  vocabulary — something no third-party tool does out of the box

Without this, WEM either pays for an external tool or keeps auditing pages
one-by-one with no site-wide view, no scoring, and no way to catch systemic
issues (a broken template, a missing hreflang cluster, a redirect chain baked
into navigation).

## 2. Goals

1. Detect and report on **all 11 check categories** in the catalog below
   (crawlability, HTTPS/security, redirects, on-page/duplicates, site
   architecture/internal linking, links, international SEO, markup/structured
   data, performance, mobile/accessibility, aggregate health) — target ~140
   individual checks.
2. Produce a single **Site Health Score (0–100)** plus 11 category sub-scores,
   computed by a documented, WEM-owned weighting methodology (not a claimed
   reverse-engineering of SEMrush's undisclosed algorithm).
3. Detect **site-wide** issues that a single-page scrape structurally cannot
   catch: duplicate content across pages, orphan pages, redirect chains/loops,
   broken internal link graphs, hreflang cluster consistency.
4. Surface a **prioritized "quick wins" list** — issues ranked by (pages
   affected × severity) — so the SEO team knows what to fix first.
5. Ship inside the existing Streamlit app and CLI with no new external paid
   dependencies for the core (P0) feature set.

## 3. Non-Goals

- **No JavaScript rendering / headless browser in v1.** The crawler parses
  raw HTML only. Client-side-rendered content, true Core Web Vitals (LCP/INP/
  CLS as experienced by real users), and rendered accessibility issues are out
  of scope for this version — see Open Questions for a possible Phase 3
  add-on via Google PageSpeed Insights API.
- **No continuous/scheduled monitoring in v1.** Each run is a point-in-time
  audit. Historical trending (score over time) is a Phase 3 nice-to-have that
  requires persisting audit results somewhere (see Open Questions).
- **No true WCAG accessibility audit.** The Mobile & Accessibility category
  ships heuristic, best-effort checks (missing alt text, missing labels,
  missing viewport) — not a substitute for a real WCAG 2.1 audit tool.
- **No backlink/off-site authority data.** This tool audits WEM's own (or a
  target's own) site structure and content — it does not replace
  `wem-link-prospect-validator`'s SEMrush-API-backed backlink analysis.
- **No AMP validation dependency in P0.** AMP checks are stubbed as P2 since
  WEM's site doesn't currently use AMP; the checks exist in the catalog for
  completeness/future-proofing, not immediate implementation.

## 4. What's Already Built vs. What's New

| Category | Checks in catalog | Already in crawler | Net new |
|---|---|---|---|
| Crawlability & Indexability | 20 | 3 | 17 |
| HTTPS & Security | 10 | 0 | 10 |
| Redirects | 10 | 0 | 10 |
| On-Page & Duplicates | 25 | 10 | 15 |
| Site Architecture & Internal Linking | 15 | 0 | 15 |
| Links (broken/external) | 15 | 0 | 15 |
| International SEO (hreflang) | 12 | 0 | 12 |
| Markup & Structured Data | 10 | 2 | 8 |
| Site Performance | 11 | 1 | 10 |
| Mobile & Accessibility | 7 | 1 | 6 |
| Site Health (Aggregate) | 4 | 0 | 4 |
| **Total** | **139** | **17** | **122** |

The existing crawler's per-page scrape (`scrape_page()` in `core.py`) already
gives us most of the raw HTML we need — the gap is almost entirely (a) new
per-page field extraction (hreflang, security headers, redirect chains, image
byte-checks) and (b) a **new site-level aggregation pass** that nothing in the
current architecture does yet, because today every page is scored in
isolation.

Full check-by-check catalog: see **`checks_catalog.csv`** (shipped alongside
this spec — 139 rows: `check_id, category, check_name, severity, level,
status, notes`).

## 5. User Stories

- As a **WEM SEO team member**, I want to run one audit against wem.io and get
  a single health score, so I can report site health to stakeholders without
  digging through raw data.
- As a **WEM SEO team member**, I want the audit to flag duplicate title tags
  and duplicate body content across the whole site, so I can find templating
  bugs that a single-page check would never catch.
- As a **WEM SEO team member**, I want a prioritized list of quick wins (e.g.
  "23 pages missing alt text" ranked above "1 page with a slow response
  time"), so I know what to fix first with limited time.
- As a **WEM SEO team member**, I want to see which pages are orphaned (exist
  in the sitemap but have no internal links pointing to them), so I can fix
  internal linking gaps before they hurt rankings.
- As a **WEM SEO team member**, I want redirect chains and loops flagged, so I
  can clean up navigation/link debt instead of discovering it by accident.
- As a **WEM SEO team member auditing a competitor**, I want the same health
  score and category breakdown for OutSystems/Mendix/ServiceNow, so I can
  benchmark WEM against them using the same yardstick (competitive positioning
  doc §10 already references this benchmarking need).
- As a **WEM SEO team member**, I want the site-wide checks to run on-demand
  without needing to schedule a recurring job, since ad hoc audits are the
  primary use case for now.

## 6. Architecture Overview

### 6.1 New crawl phases

The current crawler does a single BFS pass and scores each page independently.
The Site Auditor adds a **second pass** after the crawl completes:

```
Phase 1 (existing): BFS crawl -> per-page scrape -> per-page issues
Phase 2 (new):      site-level aggregation over all Phase-1 results
                     -> duplicate content detection (content hashing)
                     -> internal link graph construction (orphans, depth, broken links)
                     -> sitemap.xml fetch + reconciliation against crawled URLs
                     -> robots.txt full validation (beyond simple allow/disallow)
                     -> redirect chain resolution (re-request key URLs with
                        redirects=False, walk the chain manually)
                     -> hreflang cluster consistency check
                     -> HTTPS/security header + certificate check (once per host)
Phase 3 (new):      Health Score calculation from Phase 1 + Phase 2 results
```

### 6.2 New modules (proposed)

```
seo_crawler/
├── core.py              # existing per-page scrape — extend with new fields
├── site_audit.py         # NEW: Phase 2 site-level aggregation functions
├── health_score.py       # NEW: Phase 3 scoring methodology
└── checks_catalog.csv    # NEW: the 139-check reference table (data, not code —
                           #      lets the SEO team add/edit checks without touching Python)
```

### 6.3 New per-page fields required (extends `PageResult` in `core.py`)

| Field | Used by category |
|---|---|
| `redirect_chain` (list of hops) | Redirects |
| `hreflang_tags` (list of lang/url pairs) | International SEO |
| `security_headers` (dict) | HTTPS & Security |
| `content_encoding` (gzip/br/none) | Site Performance |
| `html_byte_size` | Site Performance |
| `viewport_present` (bool) | Markup, Mobile & Accessibility |
| `content_hash` (normalized body hash, for dup-content detection) | On-Page & Duplicates |
| `outbound_link_status` (only if `--check-external-links` is passed) | Links |

### 6.4 New site-level outputs (extends `write_xlsx()` / Streamlit tabs)

New sheets/tabs: **Site Health Score**, **Crawlability**, **HTTPS & Security**,
**Redirects**, **International SEO**, **Site Architecture**, **Duplicate
Content**, **Quick Wins**. Existing sheets (Pages, Issues Summary, Keyword
Matches, Brand Vocabulary) stay as-is.

## 7. Site Health Score Methodology

> **Important:** This is a WEM-original scoring methodology, not a
> reverse-engineered replica of SEMrush's (undisclosed, proprietary) exact
> algorithm. It borrows the industry-standard *Errors / Warnings / Notices*
> severity framing because that framing is generic SEO-audit convention, not
> SEMrush IP.

**Per-check severity weights:**
| Severity | Weight | Meaning |
|---|---|---|
| Error | 3 | Actively harms crawlability/indexability/UX; fix first |
| Warning | 2 | Meaningful but not urgent; fix soon |
| Notice | 1 | Best-practice polish; fix opportunistically |

**Per-check deduction:**
```
deduction(check) = (affected_pages / total_pages) × severity_weight
```

**Category sub-score:**
```
category_score = 100 − min(100, 100 × Σ deduction(check) / len(checks_in_category))
```

**Overall Site Health Score:**
```
site_health_score = weighted_average(category_scores, category_weights)
```
Default category weights start equal (each of the 10 non-aggregate categories
weighted 10%) — see Open Questions on whether WEM wants to weight
Crawlability/HTTPS higher, matching the intuition that a crawlability error is
worse than a missing Twitter Card tag.

**Quick Wins ranking:**
```
impact_score(check) = affected_pages × severity_weight
```
Sorted descending, top 10–15 surfaced in their own report tab.

## 8. Requirements

### P0 — Must Have (v1 ships without these = doesn't solve the core problem)

- [ ] Site-level crawl phase that runs after BFS completes, given the same
      crawl results already collected (no second full crawl required)
- [ ] Sitemap.xml fetch + parse + reconciliation (in sitemap vs. crawled vs.
      orphaned)
- [ ] Full robots.txt validation (not just per-page allow/disallow, which
      already exists) — missing file, syntax errors, blanket-block detection
- [ ] Redirect chain/loop detection for all crawled URLs
- [ ] Duplicate content detection: exact-duplicate titles, meta descriptions,
      H1s, and body content (via normalized content hash) across the crawled
      set
- [ ] Broken internal link detection (already-crawled 4XX/5XX cross-referenced
      against the internal link graph)
- [ ] Orphan page detection (sitemap URLs never reached by internal link
      discovery during the crawl)
- [ ] HTTPS checks: no-HTTPS, mixed content, missing HTTP→HTTPS redirect,
      missing HSTS
- [ ] Hreflang extraction + basic validation (invalid codes, missing return
      links, broken/redirected targets)
- [ ] Site Health Score + category sub-scores computed and displayed
- [ ] Quick Wins ranked list
- [ ] New Excel sheets + Streamlit tabs for all of the above
- [ ] `checks_catalog.csv` shipped as a real, editable reference file (not
      just documentation) — the SEO team can add rows without needing a code
      change for new heuristic checks

**Acceptance criteria (representative sample):**

- Given a crawl of N pages, when the audit completes, then a Site Health Score
  between 0–100 is displayed with all 10 category sub-scores.
- Given a sitemap containing a URL never linked internally during the crawl,
  when the audit completes, then that URL appears in the Orphan Pages list.
- Given two pages with identical `<title>` text, when the audit completes,
  then both URLs appear together under Duplicate Titles.
- Given a URL that redirects A→B→C, when the audit resolves it, then the full
  chain (A, B, C) and hop count are recorded, and a chain-length ≥2 issue is
  flagged.
- Given a URL that redirects A→B→A, when the audit resolves it, then a
  redirect-loop Error is flagged and the resolver stops instead of hanging.
- Given a page served over HTTP with no redirect to HTTPS, when audited, then
  an HTTPS Error is flagged at Site level.
- Given an hreflang tag pointing to a URL that returns 404, when audited, then
  a "broken hreflang target" Error is flagged.

### P1 — Should Have (fast follow, not launch-blocking)

- [ ] External link checking (`--check-external-links` flag; off by default
      since it multiplies request volume)
- [ ] SSL certificate expiry/hostname/protocol checks (requires a raw TLS
      socket check, not just `requests`)
- [ ] Internal link anchor-text quality heuristics (generic anchor text,
      keyword-mismatch anchors)
- [ ] Structured data field-completeness validation (beyond "has schema y/n",
      which already exists — validate required fields per declared `@type`)
- [ ] Keyword cannibalization detection (cross-reference
      `priority_keywords.csv` target mapping against which pages rank for
      which target keyword, per the existing `WEM_TARGET_KEYWORDS` map)
- [ ] Soft-404 heuristic detection

### P2 — Future Considerations (explicitly out of scope for v1, design shouldn't block them)

- [ ] Core Web Vitals via Google PageSpeed Insights API integration (needs API
      key, quota management, and a decision on lab vs. field data — see Open
      Questions)
- [ ] Scheduled/recurring audits with historical trend charts (needs a
      persistence layer — SQLite file, or a lightweight hosted DB — the
      current architecture is stateless per run)
- [ ] AMP validation (only relevant if/when WEM adopts AMP)
- [ ] Full WCAG 2.1 accessibility audit (would need axe-core or similar via a
      headless browser — out of scope without JS rendering)
- [ ] JS-rendered content crawling (headless Chromium via Playwright) — would
      resolve the biggest current blind spot (client-side-rendered pages) but
      is a significant new dependency and infra footprint for a Streamlit
      Cloud deployment

## 9. Success Metrics

**Leading (days–weeks post-launch):**
- WEM SEO team runs at least 1 full site audit per week (adoption)
- Audit completes end-to-end without crashing on wem.io's full site (~150–300
  pages) in under 15 minutes (task completion / reliability)
- At least 80% of flagged P0 issues are independently verifiable as real
  issues when spot-checked manually (precision — false positives erode trust
  fast in a scoring tool)

**Lagging (weeks–months):**
- Site Health Score trend improves over 2–3 audit cycles as flagged issues get
  fixed (only measurable once P2 historical tracking exists — until then,
  track manually by comparing exported reports)
- Reduction in manually-discovered SEO bugs reported ad hoc to the SEO team
  (proxy for "the tool is catching things before a human has to")

## 10. Open Questions

- **[Stakeholder]** Should category weights in the Health Score be equal, or
  should Crawlability/HTTPS count for more than, say, Mobile & Accessibility?
  Spec currently defaults to equal weighting pending input.
- **[Engineering]** For Core Web Vitals (P2): PageSpeed Insights API is free
  but rate-limited (~25,000 requests/day per key, per-page call) — is
  per-page CWV data valuable enough to justify the API key management and
  added run time, or is a lab-only performance proxy (already in P0) good
  enough for now?
- **[Engineering]** Duplicate-content detection: exact content hash is cheap
  and precise but misses *near*-duplicates (e.g. boilerplate-heavy pages with
  minor variation). Is a fuzzy-similarity approach (e.g. shingling/simhash)
  worth the added complexity for v1, or is exact-match sufficient to start?
- **[Stakeholder]** Should audits of competitor domains (OutSystems, Mendix,
  ServiceNow) be a first-class use case with the same UI, or a clearly
  separate "competitive benchmark" mode? Affects how prominently to surface
  the multi-seed comparison view in the Streamlit app.
- **[Engineering]** Where should site-level state (crawl graph, content
  hashes) live during a run — in-memory (fine for current scale, ~100–300
  pages) or should we plan for a larger crawl budget (1,000+ pages) that would
  need a different data structure/storage approach?

## 11. Timeline / Phasing

Given the size (122 net-new checks), this ships in three phases rather than
one release:

**Phase 1 (P0 core):** Crawlability, Redirects, On-Page duplicate detection,
HTTPS/Security, Health Score + Quick Wins. This is the set that most directly
extends what the crawler already half-does and delivers the "single score +
biggest wins" value immediately.

**Phase 2 (P0 remainder + P1):** Site Architecture & Internal Linking,
International SEO, Links (broken/external), Markup & Structured Data
completeness, SSL certificate checks, external link checking.

**Phase 3 (P2):** Core Web Vitals integration, scheduled audits + historical
trending, AMP, and (biggest lift) JS-rendered crawling.

No hard external deadline is known at spec time — phasing is effort-driven,
not date-driven. Flag if there's a specific stakeholder demo or reporting
cycle this needs to align with.

## 12. Appendix: Full Check Catalog

See `checks_catalog.csv` (139 rows). Columns: `check_id, category, check_name,
severity, level, status, notes`. `status` marks whether the check already
exists in the current crawler (`Existing`) or is net-new (`New` / `New
(dependency)` / `New (Phase 3)`).
