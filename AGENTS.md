# AGENTS.md

Universal AI agent operating instructions for `MHS` (`mhs.dautovic.com`).
This file governs autonomous AI coding assistants across all platforms (Google Antigravity, Anthropic Claude Code, Gemini, OpenAI Codex, Cursor, GitHub Copilot).

---

## 1. System Navigation & Sources of Truth

Always consult the project documentation and sync utilities before modifying any code:

| Document / Tool | Purpose |
| :--- | :--- |
| **[README.md](README.md)** | Core project overview, feature catalog, domain endpoints, and synchronization commands. |
| **[index.html](index.html)** | The standalone Progressive Web App (monolithic, self-contained client UI, styling, and embedded runtime state). |
| **[build_index.py](build_index.py)** | Central season synchronizer: bundles `seasons/*.json` into `index.html` under `SEASONS_DATA`. |
| **[update_data.py](update_data.py)** | Live cron scraper for active season schedules, scores, standings, and player rosters. |
| **[extract_2025.py](extract_2025.py)** | Archive data extraction script for past seasons (Fall 2025). |
| **[.github/workflows/update-scores.yml](.github/workflows/update-scores.yml)** | Automated GitHub Actions schedule scraper running 6 times daily. |

---

## 2. Non-Negotiable Repository Invariants

| Invariant | Rule |
| :--- | :--- |
| **100% Self-Contained PWA** | `index.html` must remain a zero-dependency, single-file Progressive Web App capable of running 100% offline from service worker cache. Never introduce external runtime JS/CSS frameworks, npm package trees, or remote CDN script tags. |
| **Multi-Season Architecture** | All historical and active season archives reside in `seasons/<YEAR>.json`. Never edit raw multi-season JSON blocks inside `index.html` by hand; always run `python3 build_index.py` to synchronize `seasons/*.json` into `SEASONS_DATA` in `index.html`. |
| **Cross-OS Sync & Deploy Pipeline** | Synchronization between dev workstations (macOS local clone in `~/Developer/MHS`, Windows in `C:\.Developer\MHS\`) runs strictly through `SyncGit-macOS-MHS.ps1` and `SyncGit-MHS.ps1`. Pushes to `main` automatically trigger Cloudflare Pages deployments to `https://mhs.dautovic.com/` in ~20 seconds, with GitHub Pages as a fallback mirror. Never edit in cloud drive mirrors. |
| **The "Calm App" Mandate** | In Today, Upcoming, and Scores views, UI elements must never jump or shift unexpectedly. Live background syncs must update silently without displacing the user's scroll position or reading state. |
| **Pure Markdown Documentation** | Documentation files use pure Markdown tables (`\| Key \| Value \|`), never YAML front-matter (`--- ... ---`). File naming follows hyphenated conventions. |
| **Comment & Code Hygiene** | Comments in code explain *why* or state an architectural invariant in 1–3 lines. Never include build numbers, personal timestamps, user quotes, or historical narration ("it used to be X"). Obsolete code is removed cleanly in the same commit. |

---

## 3. Platform Pitfalls & Critical Guardrails (DO NOT REPEAT)

| Pitfall / Hazard | Root Cause & Mandate |
| :--- | :--- |
| **MaxPreps Athlete Schema Traps** | In the Next.js `athleteData` JSON tuple, index `a[7]` is the **class year / grade code** (e.g. `11` for Jr, `12` for Sr). The **actual jersey number is at index `a[8]`**. Using `a[7]` causes all athletes to falsely display grade numbers as jerseys. Name fields are `a[5]` (first), `a[6]` (last), and `a[33]` (full name). |
| **Background Fetch Clobbering Archive State** | `loadDynamicScoresAndStandings()` runs asynchronously in the background. It must **only** update active global UI state if `currentSeason === '2026'`. For archived seasons (e.g. `2025`), dynamic fetches update in-memory `SEASONS_DATA['2026']` without clobbering the selected historical season. |
| **Temporal Dead Zone (TDZ) Crash** | `index.html` runs as a monolithic script block. `SafeStorage` must be declared before `currentSeason` and any state initialization. Any top-level code executing before `SafeStorage` or helper declarations will throw a TDZ `ReferenceError`, silently blanking the app. |
| **Mobile Header Width & Button Clipping** | On mobile screens ($\le 480\text{px}$, including iPhone Air, 15, and SE at 375px–390px):<br>1. `.header-brand-text` (`Melrose SPORTS`) is hidden to preserve horizontal clearance for action pills.<br>2. `.brand-badge` is sized at `48px × 34px` with font size `0.85rem`.<br>3. `#season-picker-btn` uses compact year tags (`'26`, `'25`).<br>4. `#sport-picker-btn` must maintain `width: auto; max-width: 125px; flex-shrink: 0;`—**never** use `flex: 1` or unrestrained `min-width`, which over-stretches the button and pushes the rightmost `🔍` search button off-screen. |
| **Historical Season Temporal Filtering** | Past season dates (e.g. 2025) are all in the past relative to the system clock. Comparing them to `getTodayEasternString()` causes Today and Upcoming to either show 0 items or dump 100+ past games. For historical seasons (`currentSeason !== '2026'`), Today and Upcoming display a clean "Season Concluded" banner with a direct link to the Scores tab. |

---

## 4. Operational Verification Protocol

Before declaring any task, bugfix, or refactoring complete:

1. **Syntax & AST Validation:**
   Run automated JavaScript syntax checks on `index.html` via `node -c` (extracting the script block if needed) and verify Python scripts with `python3 -m py_compile <script>.py`.
2. **Season Data Synchronization:**
   Whenever season JSON or score schemas change, execute `python3 build_index.py` and confirm that `SEASONS_DATA` is populated and synchronized.
3. **Multi-Viewport Measurement:**
   Always verify header and layout rendering on both desktop and mobile viewports (specifically iPhone 390px and 375px) to guarantee zero button clipping or overflow.
4. **Clean Git State:**
   Run `git status` to ensure zero stray temporary files or unvetted artifacts before pushing via `SyncGit-macOS-MHS.ps1`.

