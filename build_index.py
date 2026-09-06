#!/usr/bin/env python3
"""
MHS Web App Builder
Injects 2026 league standings and score-ready architecture into index.html
Keeps the pristine 96 games of the 2026 Varsity Schedule (no past years or pre-season additions).
"""
import json
import re

with open("standings.json") as f:
    standings_data = json.load(f)

# Minify 2026 standings for initial offline/standalone fallback
embedded_standings_js = json.dumps(standings_data.get("standings", {}))

with open("index.html") as f:
    orig = f.read()

# Verify events array extraction from original (exactly 96 games)
events_match = re.search(r"(const events = \[.*?\];)", orig, re.DOTALL)
if not events_match:
    print("Error: Could not find events array in index.html")
    exit(1)
events_block = events_match.group(1)

css_additions = """
    /* Score display on cards (for completed games) */
    .card.has-score {
      border-color: rgba(59, 130, 246, 0.3);
    }
    .card-score-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.45rem 0.65rem;
      border-radius: 8px;
      background-color: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
    }
    .score-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      font-size: 0.8rem;
      font-weight: 800;
      padding: 0.2rem 0.55rem;
      border-radius: 6px;
      letter-spacing: 0.02em;
    }
    .score-badge.win {
      background-color: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .score-badge.loss {
      background-color: rgba(239, 68, 68, 0.15);
      color: #f87171;
      border: 1px solid rgba(239, 68, 68, 0.35);
    }
    .score-badge.tie {
      background-color: rgba(148, 163, 184, 0.15);
      color: #cbd5e1;
      border: 1px solid rgba(148, 163, 184, 0.35);
    }
    .score-status-text {
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
    }

    /* Filter Bar Enhancements */
    .filter-group {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.5rem;
    }
    .filter-divider {
      width: 1px;
      height: 20px;
      background-color: var(--border-subtle);
      margin: 0 0.25rem;
    }

    /* Standings View Styles */
    .standings-toolbar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      margin-bottom: 1.5rem;
      background-color: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 0.75rem 1rem;
    }
    .sync-status-indicator {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.775rem;
      color: var(--text-muted);
      font-weight: 600;
    }
    .sync-status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background-color: #10b981;
      box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
    }
    .standings-card {
      background-color: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      margin-bottom: 1.75rem;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    .standings-card-header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      padding: 1rem 1.25rem;
      background-color: var(--bg-surface-elevated);
      border-bottom: 1px solid var(--border-subtle);
    }
    .standings-title-group h3 {
      font-size: 1.15rem;
      font-weight: 800;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .standings-subtitle {
      font-size: 0.8rem;
      color: var(--text-secondary);
      margin-top: 0.15rem;
    }
    .standings-ext-link {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      font-size: 0.775rem;
      font-weight: 600;
      color: var(--accent-cyan);
      text-decoration: none;
      padding: 0.35rem 0.65rem;
      border-radius: 6px;
      background-color: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      transition: all 0.15s ease;
    }
    .standings-ext-link:hover {
      border-color: var(--accent-blue);
      color: #fff;
      background-color: var(--accent-blue);
    }
    .table-scroll-wrap {
      width: 100%;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }
    .standings-table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.875rem;
      min-width: 580px;
    }
    .standings-table th {
      padding: 0.75rem 1rem;
      font-size: 0.725rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border-subtle);
      background-color: var(--bg-surface);
      white-space: nowrap;
    }
    .standings-table td {
      padding: 0.85rem 1rem;
      border-bottom: 1px solid var(--border-subtle);
      color: var(--text-primary);
      white-space: nowrap;
    }
    .standings-table tr:last-child td {
      border-bottom: none;
    }
    .standings-table tr:hover {
      background-color: var(--bg-surface-elevated);
    }
    .standings-table tr.is-melrose {
      background-color: rgba(225, 29, 72, 0.09);
      font-weight: 700;
      box-shadow: inset 4px 0 0 var(--accent-red);
    }
    .team-cell {
      display: flex;
      align-items: center;
      gap: 0.65rem;
    }
    .school-mascot-img {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      object-fit: contain;
      background-color: rgba(255, 255, 255, 0.08);
      border: 1px solid var(--border-subtle);
      flex-shrink: 0;
    }
    .school-mascot-fallback {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background-color: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 0.7rem;
      font-weight: 700;
      color: var(--text-secondary);
      flex-shrink: 0;
    }
    .mhs-badge {
      background-color: var(--accent-red);
      color: #ffffff;
      font-size: 0.65rem;
      font-weight: 800;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      letter-spacing: 0.04em;
    }
    .streak-badge {
      display: inline-block;
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
    }
    .streak-badge.streak-w {
      background-color: rgba(16, 185, 129, 0.15);
      color: #34d399;
    }
    .streak-badge.streak-l {
      background-color: rgba(239, 68, 68, 0.15);
      color: #f87171;
    }
    .streak-badge.streak-none {
      background-color: var(--bg-surface-elevated);
      color: var(--text-muted);
    }

    /* Mobile Responsiveness Improvements */
    html, body {
      overflow-x: hidden;
      max-width: 100vw;
    }

    .filter-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 0.35rem;
    }

    @media (max-width: 640px) {
      .nav-tabs {
        width: 100%;
        display: flex;
      }
      .tab-button {
        flex: 1;
        text-align: center;
        padding: 0.45rem 0.25rem;
        font-size: 0.775rem;
      }
      .standings-toolbar {
        flex-direction: column;
        align-items: stretch;
        gap: 0.65rem;
        padding: 0.75rem;
      }
      #standings-sport-filters {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.35rem;
        width: 100%;
      }
      #standings-sport-filters .filter-pill {
        width: 100%;
        text-align: center;
        padding: 0.45rem 0.2rem;
        font-size: 0.725rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .sync-status-indicator {
        justify-content: flex-end;
      }
      .filter-group {
        flex-direction: column;
        align-items: stretch;
        width: 100%;
      }
      .filter-divider {
        display: none;
      }
      .standings-card {
        margin-bottom: 1.25rem;
      }
      .standings-card-header {
        padding: 0.75rem 1rem;
      }
      .standings-table th, .standings-table td {
        padding: 0.65rem 0.6rem;
        font-size: 0.8rem;
      }
    }
"""

content = orig
content = content.replace("  </style>", css_additions + "\n  </style>")

# 2. Update nav-tabs: add Standings tab
old_nav_tabs = """      <div class="nav-tabs" role="tablist">
        <button class="tab-button active" id="tab-calendar" onclick="switchTab('calendar')" role="tab" aria-selected="true">Date Schedule</button>
        <button class="tab-button" id="tab-sports" onclick="switchTab('sports')" role="tab" aria-selected="false">By Sport</button>
      </div>"""

new_nav_tabs = """      <div class="nav-tabs" role="tablist">
        <button class="tab-button active" id="tab-calendar" onclick="switchTab('calendar')" role="tab" aria-selected="true">Date Schedule</button>
        <button class="tab-button" id="tab-sports" onclick="switchTab('sports')" role="tab" aria-selected="false">By Sport</button>
        <button class="tab-button" id="tab-standings" onclick="switchTab('standings')" role="tab" aria-selected="false">🏆 Standings</button>
      </div>"""
content = content.replace(old_nav_tabs, new_nav_tabs)

# 3. Add standings-view main panel after sports-view
standings_view_html = """
  <main id="standings-view" class="view-panel" role="tabpanel" aria-labelledby="tab-standings">
    <div class="standings-toolbar">
      <div class="filter-pills" id="standings-sport-filters">
        <button class="filter-pill active" data-sport="all" onclick="setStandingsSport('all')">All Sports</button>
        <button class="filter-pill" data-sport="Football" onclick="setStandingsSport('Football')">Football</button>
        <button class="filter-pill" data-sport="Boys' Soccer" onclick="setStandingsSport('Boys\\' Soccer')">Boys' Soccer</button>
        <button class="filter-pill" data-sport="Girls' Soccer" onclick="setStandingsSport('Girls\\' Soccer')">Girls' Soccer</button>
        <button class="filter-pill" data-sport="Girls' Volleyball" onclick="setStandingsSport('Girls\\' Volleyball')">Girls' Volleyball</button>
        <button class="filter-pill" data-sport="Field Hockey" onclick="setStandingsSport('Field Hockey')">Field Hockey</button>
      </div>
      <div class="sync-status-indicator" id="standings-sync-badge">
        <span class="sync-status-dot"></span>
        <span id="standings-sync-text">Middlesex League 2026</span>
      </div>
    </div>
    <div id="standings-container"></div>
  </main>"""

content = content.replace("    <div class=\"grid\" id=\"sport-golf\"></div>\n  </main>", "    <div class=\"grid\" id=\"sport-golf\"></div>\n  </main>\n" + standings_view_html)

# 4. Locate the main script tag
main_script_anchor = "<script>\n// Complete Varsity Athletic Schedule Data"
script_start = content.find(main_script_anchor)
if script_start == -1:
    print(f"Error: Could not find main script anchor: {main_script_anchor}")
    exit(1)

js_code = f"""
// Complete Varsity Athletic Schedule Data (Pristine 96 games of Fall 2026)
{events_block}

// 2026 Middlesex League Standings (Preloaded for instant offline & standalone access)
const INITIAL_STANDINGS = {embedded_standings_js};
let currentStandingsData = INITIAL_STANDINGS;

// Apply score payload to scheduled events as games are played
function applyScores(scoreMap) {{
  if (!scoreMap) return;
  events.forEach(e => {{
    const key = e.sport + '|' + e.date;
    if (scoreMap[key]) {{
      const sc = scoreMap[key];
      e.result = sc.result;
      e.mhsScore = sc.mhsScore;
      e.oppScore = sc.oppScore;
      e.status = sc.status || 'Final';
    }}
  }});
}}

// ==========================================
// Theme & Safari / Google Drive Robustness
// ==========================================
const inIframe = (function() {{
  try {{
    return window.self !== window.top;
  }} catch (e) {{
    return true;
  }}
}})();

const host = (window.location && window.location.hostname) ? window.location.hostname : '';
const ref = document.referrer || '';
const isGoogleDriveContext = Boolean(inIframe || 
  host.indexOf('googleusercontent.com') !== -1 ||
  host.indexOf('drive.google.com') !== -1 ||
  ref.indexOf('google.com') !== -1);

if (inIframe) {{
  const popoutEl = document.getElementById('popout-btn');
  if (popoutEl) {{
    popoutEl.style.display = 'inline-flex';
    popoutEl.href = window.location.href;
  }}
}}

const SafeStorage = {{
  getItem: function(key) {{
    try {{ return localStorage.getItem(key); }} catch (e) {{ return null; }}
  }},
  setItem: function(key, val) {{
    try {{ localStorage.setItem(key, val); }} catch (e) {{}}
  }}
}};

let currentThemeMode = SafeStorage.getItem('mhs_theme_preference') || 'auto';
const systemDarkQuery = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

function updateThemeUI() {{
  const root = document.documentElement;
  const iconEl = document.getElementById('theme-icon');
  const textEl = document.getElementById('theme-text');
  const btnEl = document.getElementById('theme-toggle');
  const metaThemeColor = document.getElementById('meta-theme-color');

  let effectiveIsDark;

  if (currentThemeMode === 'dark') {{
    root.setAttribute('data-theme', 'dark');
    effectiveIsDark = true;
    if (iconEl) iconEl.textContent = '🌙';
    if (textEl) textEl.textContent = 'Dark';
    if (btnEl) btnEl.title = 'Theme: Dark (Click to change)';
  }} else if (currentThemeMode === 'light') {{
    root.setAttribute('data-theme', 'light');
    effectiveIsDark = false;
    if (iconEl) iconEl.textContent = '☀️';
    if (textEl) textEl.textContent = 'Light';
    if (btnEl) btnEl.title = 'Theme: Light (Click to change)';
  }} else {{
    if (isGoogleDriveContext) {{
      root.setAttribute('data-theme', 'dark');
      effectiveIsDark = true;
      if (iconEl) iconEl.textContent = '💻';
      if (textEl) textEl.textContent = 'Auto (Dark)';
      if (btnEl) btnEl.title = 'Theme: Auto (Google Drive mode: Dark)';
    }} else {{
      effectiveIsDark = systemDarkQuery ? systemDarkQuery.matches : true;
      root.setAttribute('data-theme', effectiveIsDark ? 'dark' : 'light');
      if (iconEl) iconEl.textContent = '💻';
      if (textEl) textEl.textContent = 'Auto';
      if (btnEl) btnEl.title = 'Theme: Auto (Matches OS: ' + (effectiveIsDark ? 'Dark' : 'Light') + ')';
    }}
  }}

  const color = effectiveIsDark ? '#0b0f19' : '#f8fafc';
  if (metaThemeColor) {{
    metaThemeColor.setAttribute('content', color);
  }}
}}

function cycleTheme() {{
  if (currentThemeMode === 'auto') currentThemeMode = 'dark';
  else if (currentThemeMode === 'dark') currentThemeMode = 'light';
  else currentThemeMode = 'auto';
  SafeStorage.setItem('mhs_theme_preference', currentThemeMode);
  updateThemeUI();
}}

if (systemDarkQuery && systemDarkQuery.addEventListener) {{
  systemDarkQuery.addEventListener('change', () => {{
    if (currentThemeMode === 'auto' && !isGoogleDriveContext) updateThemeUI();
  }});
}} else if (systemDarkQuery && systemDarkQuery.addListener) {{
  systemDarkQuery.addListener(() => {{
    if (currentThemeMode === 'auto' && !isGoogleDriveContext) updateThemeUI();
  }});
}}

// ==========================================
// Card Rendering & Filters
// ==========================================
function getSportClass(sport) {{
  switch (sport) {{
    case "Girls' Volleyball": return "sport-vball";
    case "Boys' Soccer": return "sport-bsoc";
    case "Girls' Soccer": return "sport-gsoc";
    case "Football": return "sport-fball";
    case "Field Hockey": return "sport-fhockey";
    case "Cross Country": return "sport-xc";
    case "Golf": return "sport-golf";
    default: return "sport-other";
  }}
}}

function formatDate(isoStr) {{
  const parts = isoStr.split('-');
  const d = new Date(parts[0], parts[1] - 1, parts[2]);
  return d.toLocaleDateString('en-US', {{ weekday: 'short', month: 'short', day: 'numeric' }});
}}

function renderCard(item) {{
  const locClass = item.isHome ? 'home' : 'away';
  const locLabel = item.isHome ? 'HOME' : 'AWAY';
  const prefix = item.isHome ? 'vs.' : '@';
  
  let scoreHtml = '';
  if (item.result && item.mhsScore !== undefined && item.oppScore !== undefined) {{
    const resClass = item.result === 'W' ? 'win' : item.result === 'L' ? 'loss' : 'tie';
    const resLabel = item.result === 'W' ? 'WIN' : item.result === 'L' ? 'LOSS' : 'TIE';
    scoreHtml = `
      <div class="card-score-row">
        <div class="score-badge ${{resClass}}">
          <span>${{resLabel}}</span>
          <span>${{item.mhsScore}} - ${{item.oppScore}}</span>
        </div>
        <span class="score-status-text">FINAL SCORE</span>
      </div>
    `;
  }}

  return `
    <div class="card ${{item.result ? 'has-score' : ''}}">
      <div class="card-header">
        <span class="date-label">${{formatDate(item.date)}}</span>
        <span class="sport-tag ${{getSportClass(item.sport)}}">${{item.sport}}</span>
      </div>
      <div class="matchup">${{prefix}} ${{item.opp}}</div>
      ${{scoreHtml}}
      <div class="meta-row">
        <span>⏰ ${{item.time}}</span>
        <span class="location-badge ${{locClass}}">${{locLabel}}</span>
      </div>
      <div class="venue-detail">${{item.venue}}</div>
    </div>
  `;
}}

let activeLocFilter = 'all'; // 'all' | 'home' | 'away'

function setLocFilter(loc) {{
  activeLocFilter = loc;
  document.querySelectorAll('.filter-pill').forEach(btn => {{
    btn.classList.toggle('active', btn.getAttribute('data-loc') === loc);
  }});
  renderDailyView();
}}

function onFilterChange() {{
  renderDailyView();
}}

function renderDailyView() {{
  const searchEl = document.getElementById('schedule-search');
  const query = (searchEl && searchEl.value) ? searchEl.value.trim().toLowerCase() : '';

  const sorted = [...events].sort((a, b) => a.date.localeCompare(b.date));

  const filtered = sorted.filter(item => {{
    if (activeLocFilter === 'home' && !item.isHome) return false;
    if (activeLocFilter === 'away' && item.isHome) return false;

    if (query) {{
      const matchText = `${{item.sport}} ${{item.opp}} ${{item.venue}} ${{item.date}} ${{item.result || ''}}`.toLowerCase();
      if (!matchText.includes(query)) return false;
    }}
    return true;
  }});

  const container = document.getElementById('daily-grid');
  const countEl = document.getElementById('filter-count');

  if (countEl) {{
    countEl.textContent = `Showing ${{filtered.length}} of ${{events.length}} games`;
  }}

  if (filtered.length === 0) {{
    container.innerHTML = `
      <div class="empty-state">
        <p style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">No games match your search</p>
        <p style="font-size: 0.85rem;">Try adjusting your search query or location filter.</p>
      </div>
    `;
  }} else {{
    container.innerHTML = filtered.map(renderCard).join('');
  }}
}}

function populateSportsView() {{
  const filterBySport = (sportName) => 
    events.filter(e => e.sport === sportName).sort((a, b) => a.date.localeCompare(b.date));

  const sportsMap = [
    {{ id: 'sport-vball', countId: 'count-vball', name: "Girls' Volleyball" }},
    {{ id: 'sport-bsoc', countId: 'count-bsoc', name: "Boys' Soccer" }},
    {{ id: 'sport-gsoc', countId: 'count-gsoc', name: "Girls' Soccer" }},
    {{ id: 'sport-fball', countId: 'count-fball', name: "Football" }},
    {{ id: 'sport-fhockey', countId: 'count-fhockey', name: "Field Hockey" }},
    {{ id: 'sport-xc', countId: 'count-xc', name: "Cross Country" }},
    {{ id: 'sport-golf', countId: 'count-golf', name: "Golf" }}
  ];

  sportsMap.forEach(s => {{
    const list = filterBySport(s.name);
    const container = document.getElementById(s.id);
    const countEl = document.getElementById(s.countId);
    if (container) container.innerHTML = list.map(renderCard).join('');
    if (countEl) countEl.textContent = `${{list.length}} games`;
  }});
}}

// ==========================================
// Standings Rendering (2026-27 Season)
// ==========================================
let activeStandingsSport = 'all';

function setStandingsSport(sport) {{
  activeStandingsSport = sport;
  document.querySelectorAll('#standings-sport-filters .filter-pill').forEach(btn => {{
    btn.classList.toggle('active', btn.getAttribute('data-sport') === sport);
  }});
  renderStandingsView();
}}

function renderStandingsView() {{
  const container = document.getElementById('standings-container');
  if (!container || !currentStandingsData) return;

  const sports = Object.keys(currentStandingsData);
  const targetSports = activeStandingsSport === 'all' ? sports : sports.filter(s => s === activeStandingsSport);

  if (targetSports.length === 0) {{
    container.innerHTML = `<div class="empty-state"><p>No standings data available for this sport.</p></div>`;
    return;
  }}

  container.innerHTML = targetSports.map(sportKey => {{
    const data = currentStandingsData[sportKey];
    if (!data || !data.teams || data.teams.length === 0) return '';

    const rowsHtml = data.teams.map(t => {{
      const isMHS = t.isMHS;
      let streakClass = 'streak-none';
      if (t.streak && t.streak.endsWith('W')) streakClass = 'streak-w';
      else if (t.streak && t.streak.endsWith('L')) streakClass = 'streak-l';

      const mascotHtml = t.mascot 
        ? `<img class="school-mascot-img" src="${{t.mascot}}" alt="${{t.school}}" loading="lazy" onerror="this.style.display='none'; if (this.nextElementSibling) this.nextElementSibling.style.display='inline-flex';"><span class="school-mascot-fallback" style="display:none;">${{t.school.charAt(0)}}</span>`
        : `<span class="school-mascot-fallback">${{t.school.charAt(0)}}</span>`;

      return `
        <tr class="${{isMHS ? 'is-melrose' : ''}}">
          <td style="text-align: center; font-weight: 700;">${{t.rank}}</td>
          <td>
            <div class="team-cell">
              ${{mascotHtml}}
              <span>${{t.school}}</span>
              ${{isMHS ? '<span class="mhs-badge">MELROSE</span>' : ''}}
            </div>
          </td>
          <td style="text-align: center; font-weight: 600;">${{t.confRecord}}</td>
          <td style="text-align: center; color: var(--text-secondary);">${{t.confPct}}</td>
          <td style="text-align: center; font-weight: 600;">${{t.overallRecord}}</td>
          <td style="text-align: center; color: var(--text-secondary);">${{t.overallPct}}</td>
          <td style="text-align: center;">
            <span class="streak-badge ${{streakClass}}">${{t.streak || '—'}}</span>
          </td>
        </tr>
      `;
    }}).join('');

    const extLink = data.leagueUrl 
      ? `<a href="${{data.leagueUrl}}" target="_blank" rel="noopener" class="standings-ext-link">Full League on MaxPreps ↗</a>`
      : '';

    return `
      <div class="standings-card">
        <div class="standings-card-header">
          <div class="standings-title-group">
            <h3>🏆 ${{sportKey}}</h3>
            <div class="standings-subtitle">${{data.leagueName || 'Middlesex League'}} • 2026 Fall Season</div>
          </div>
          ${{extLink}}
        </div>
        <div class="table-scroll-wrap">
          <table class="standings-table">
            <thead>
              <tr>
                <th style="width: 44px; text-align: center;">#</th>
                <th>School</th>
                <th style="text-align: center;">League W-L</th>
                <th style="text-align: center;">League %</th>
                <th style="text-align: center;">Overall W-L</th>
                <th style="text-align: center;">Overall %</th>
                <th style="text-align: center;">Streak</th>
              </tr>
            </thead>
            <tbody>
              ${{rowsHtml}}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }}).join('');
}}

function switchTab(view) {{
  document.querySelectorAll('.tab-button').forEach(b => {{
    b.classList.remove('active');
    b.setAttribute('aria-selected', 'false');
  }});
  document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));

  if (view === 'calendar') {{
    const tab = document.getElementById('tab-calendar');
    if (tab) {{ tab.classList.add('active'); tab.setAttribute('aria-selected', 'true'); }}
    document.getElementById('calendar-view').classList.add('active');
  }} else if (view === 'sports') {{
    const tab = document.getElementById('tab-sports');
    if (tab) {{ tab.classList.add('active'); tab.setAttribute('aria-selected', 'true'); }}
    document.getElementById('sports-view').classList.add('active');
  }} else if (view === 'standings') {{
    const tab = document.getElementById('tab-standings');
    if (tab) {{ tab.classList.add('active'); tab.setAttribute('aria-selected', 'true'); }}
    document.getElementById('standings-view').classList.add('active');
    renderStandingsView();
  }}
}}

// ==========================================
// Dynamic Data Integration (Fetch scores.json & standings.json)
// ==========================================
async function loadDynamicScoresAndStandings() {{
  try {{
    const scoresResp = await fetch('./scores.json', {{ cache: 'no-store' }});
    if (scoresResp.ok) {{
      const scoresJson = await scoresResp.json();
      if (scoresJson && scoresJson.scores) {{
        applyScores(scoresJson.scores);
        renderDailyView();
        populateSportsView();
      }}
    }}
  }} catch (e) {{}}

  try {{
    const stdResp = await fetch('./standings.json', {{ cache: 'no-store' }});
    if (stdResp.ok) {{
      const stdJson = await stdResp.json();
      if (stdJson && stdJson.standings) {{
        currentStandingsData = stdJson.standings;
        renderStandingsView();
      }}
    }}
  }} catch (e) {{}}
}}

// Initial Render
updateThemeUI();
renderDailyView();
populateSportsView();
renderStandingsView();
loadDynamicScoresAndStandings();
"""

new_content = content[:script_start + len("<script>")] + js_code + "\n</script>\n</body>\n</html>\n"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"[✓] Successfully wrote updated index.html ({len(new_content)} bytes)")
