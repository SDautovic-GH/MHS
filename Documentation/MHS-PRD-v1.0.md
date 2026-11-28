# MHS Sports (`mhs.dautovic.com`) — PRD & Technical Reference

| Field | Value |
| :--- | :--- |
| **Document Type** | Product Requirements Document (PRD) & Technical Spec |
| **App Name** | Melrose High School Fall Varsity Sports (`MHS`) |
| **App Version** | 1.0.0 |
| **PRD Revision** | v1.0 |
| **Date** | 2026-11-27 |
| **Author** | Samir Dautovic |
| **Status** | Deployed & Active (`https://mhs.dautovic.com/`) |
| **Summary** | Zero-dependency, 100% self-contained Progressive Web App (PWA) for Melrose High School Fall Varsity athletics—delivering live schedules, MIAA postseason matchups, verified scores, Middlesex League standings, player rosters/stats, venue directions, and multi-season archives (`2025`, `2026`, and beyond). |

---

## 1. Objective & Non-Goals

- **Primary Objective:** Provide Melrose High School families, students, and fans with a fast, calm, offline-capable sports companion across iPhone, iPad, and desktop browsers—consolidating fragmented ArbiterLive schedules and MaxPreps scores/standings/rosters into one clean interface.
- **Audience:** Melrose High School parents, student-athletes, coaches, and community supporters on iOS Safari (standalone PWA / Add to Home Screen) and desktop browsers.
- **Non-Goals:**
  - No external runtime JavaScript/CSS frameworks, bundlers, or npm dependency trees (`index.html` remains 100% self-contained).
  - No backend database servers or user accounts; all state is static JSON + embedded `SEASONS_DATA` + browser `SafeStorage`.
  - No layout jumps or unexpected delayed UI shifts during background score refreshes ("Calm App" mandate).

---

## 2. Active Decisions & Technical Rationale

| Date | Decision | Reason & Trade-offs | Status |
| :--- | :--- | :--- | :--- |
| 2026-10-16 | Single-File Zero-Dependency PWA (`index.html`) | Guarantees instant cold start, 100% offline reliability, and zero build tooling overhead on Cloudflare Pages and GitHub Pages. Trade-off: CSS, HTML, JS, and `SEASONS_DATA` coexist in one file and must be syntax-checked (`node -c`) and brace-verified after edits. | Locked |
| 2026-10-22 | Multi-Season Archive Pipeline (`seasons/<YEAR>.json` + `build_index.py`) | Keeps historical seasons (`2025`) separate from active season (`2026`) while allowing `build_index.py` to bundle all seasons into `SEASONS_DATA` inside `index.html`. | Locked |
| 2026-11-01 | Dual-Source Scraper (`update_data.py`: ArbiterLive + MaxPreps) | ArbiterLive provides authoritative MIAA/MHS game times and venues; MaxPreps provides Middlesex League standings, set-by-set scores, and varsity player rosters/stats. | Locked |
| 2026-11-12 | Remove `[skip ci]` from GitHub Actions Auto-Commits | Cloudflare Pages honors `[skip ci]` and skips building/deploying commits that include it. Since `GITHUB_TOKEN` pushes do not trigger recursive GitHub Actions runs, omitting `[skip ci]` ensures every automated score update deploys to `mhs.dautovic.com` in ~20s. | Locked |
| 2026-11-14 | Value-Based MaxPreps `athleteData` Parsing | MaxPreps shifts trailing tuple indices (e.g., `a[31..37]`) across deployments. Deriving `fullName` from `a[5]` + `a[6]` and matching `profileUrl` (`http*`) and `year` (`Fr.`/`So.`/`Jr.`/`Sr.`) by value prevents positions (`DS`, `S`) or timestamps from leaking into athlete names/links. | Locked |
| 2026-11-25 | Mobile Floating Liquid Glass Capsule Bottom Bar (`<= 640px`) | Matches `AvidityCarpool` and `RSSReader` mobile ergonomics: hides the top `.nav-tabs-wrapper` on mobile so the header stays a single row, and places the 4 primary tabs (`Today`, `Upcoming`, `Scores`, `Standings`) in a `46px` frosted bottom pill (`max-width: 320px`) with live count badges. Desktop (`> 640px`) retains top `.nav-tabs`. | Locked |
| 2026-11-25 | Un-Boxed Mobile Scores Layout (`<= 640px`) | Removes the nested `.scores-sport-group-card` border/padding box and tightens `.container` side padding (`0.55rem`) on mobile so score cards sit cleanly with more room for opponent names. | Locked |

---

## 3. Core Features & Views

| View / Feature | Behavior & Data Source |
| :--- | :--- |
| **Today** | Shows games scheduled for the current Eastern Time date (`getTodayEasternString()`), Next Game countdown ticker, live search, sport filter, and location pills (`All`, `Home`, `Away`, `FNL`). Historical seasons (`currentSeason !== '2026'`) display a "Season Concluded" banner linking to `Scores`. |
| **Upcoming** | Chronological list of remaining active-season varsity contests across all 7 Fall sports (`Football`, `Boys' Soccer`, `Girls' Soccer`, `Girls' Volleyball`, `Field Hockey`, `Cross Country`, `Golf`), including MIAA postseason matchups. |
| **Scores** | Completed results grouped by sport with W-L-T record badges, home/away tags, set/period breakdowns, and venue links. |
| **Standings** | Two sub-views: **Team Standings** (Middlesex League tables from `standings.json`) and **Player Stats** (varsity leaders, jersey numbers, positions, class years, and MaxPreps profile links from `players.json`). |
| **Header Controls** | Compact `MHS` badge, season selector (`'26`, `'25`), sport filter pill, and expandable live search drawer (`🔍`), plus theme toggle (`Auto` / `Dark` / `Light`) and `MMTV Livestreams` / `Venues & Directions` footer actions. |

---

## 4. Data, Scraper & Deployment Architecture

| Component | Path | Responsibility |
| :--- | :--- | :--- |
| **Frontend PWA** | `index.html` | Self-contained UI, CSS design tokens (light/dark), `SEASONS_DATA`, and background sync (`loadDynamicScoresAndStandings()`). |
| **Web App Manifest** | `manifest.json` | Standalone PWA metadata (`#991b1b` theme/background, `180`/`192`/`512`/`1024` icon set). |
| **Season Archives** | `seasons/2025.json`, `seasons/2026.json` | Canonical per-season event, score, standings, and player snapshots. |
| **Live JSON Feeds** | `scores.json`, `standings.json`, `players.json`, `schedule.json` | Updated by `update_data.py` and fetched asynchronously by `index.html` for `2026`. |
| **Live Scraper** | `update_data.py` | Pulls ArbiterLive & MaxPreps schedules, scores, Middlesex League standings, and player stats; resolves TBA playoff matchups and invokes `build_index.py`. |
| **Season Bundler** | `build_index.py` | Embeds `seasons/*.json` into `SEASONS_DATA` inside `index.html`. |
| **Archive Extractor** | `extract_2025.py` | Extracts historical Fall 2025 data into `seasons/2025.json`. |
| **Scheduled CI** | `.github/workflows/update-scores.yml` | Runs `python update_data.py` 6 times daily (`0 2,11,13,14,15,16 * * *` UTC) and pushes changes to `main`. |
| **Cross-OS Sync** | `SyncGit-macOS-MHS.ps1`, `SyncGit-MHS.ps1` | Stashes local edits, pulls `origin/main`, commits, and pushes; `main` auto-deploys to `https://mhs.dautovic.com/` (Cloudflare Pages) and mirrors to GitHub Pages. |

---

## 5. Mistakes, Pitfalls & Guardrails (DO NOT REPEAT)

- **MaxPreps `athleteData` Tuple Traps:** In MaxPreps Next.js `athleteData`, `a[7]` is grade code (`9`–`12`), **not** jersey number (`a[8]`). Trailing indices (`a[31..37]`) also shift when MaxPreps updates its schema; always build `fullName` from `a[5]` + `a[6]` and detect `profileUrl` (`http*`) and `year` (`Fr.`/`So.`/`Jr.`/`Sr.`) by value.
- **Cloudflare Pages `[skip ci]` Trap:** Never put `[skip ci]` in `.github/workflows/update-scores.yml` commit messages; Cloudflare Pages skips building any commit containing `[skip ci]`, silently freezing `mhs.dautovic.com` on stale data.
- **Temporal Dead Zone (TDZ) Crash:** `SafeStorage` must be declared before `currentSeason` and any top-level state initialization in `index.html`. Any top-level reference before declaration throws a `ReferenceError` and blanks the app.
- **Background Fetch Clobbering Archive State:** `loadDynamicScoresAndStandings()` runs asynchronously and must only mutate active UI state when `currentSeason === '2026'`, never clobbering `2025` archive views.
- **Mobile Header Clearance (`<= 480px`):** `#sport-picker-btn` must keep `width: auto; max-width: 125px; flex-shrink: 0;` (never `flex: 1`) so the rightmost `🔍` search button is never clipped on 375px–390px iPhones.
- **Never Hand-Edit `SEASONS_DATA` in `index.html`:** Always update `seasons/<YEAR>.json` (or run `update_data.py`) and synchronize via `python3 build_index.py`.

---

## 6. Verification Checklist

1. **JS & CSS Validation:** Run `node -c` on all inline `<script>` blocks in `index.html`, verify balanced `{`/`}` braces in `<style>`, and run `python3 -m py_compile` on modified Python scripts.
2. **Data Synchronization:** Run `python3 build_index.py` after any `seasons/*.json` edit.
3. **Sync & Live Deployment:** Push via `./SyncGit-macOS-MHS.ps1` (macOS) or `.\SyncGit-MHS.ps1` (Windows) and verify changes live on `https://mhs.dautovic.com/`.
