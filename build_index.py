#!/usr/bin/env python3
"""
MHS Index Standings & Multi-Season Synchronizer
Synchronizes all seasons (seasons/*.json) into index.html
while keeping individual season JSON files and 2026 live scores fresh.
"""
import json
import re
import os

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    if not os.path.exists("index.html"):
        print("[-] Missing index.html")
        return

    os.makedirs("seasons", exist_ok=True)

    # 1. Synchronize 2026 season file if scores.json, standings.json, players.json exist
    season_2026_file = os.path.join("seasons", "2026.json")
    if os.path.exists(season_2026_file):
        with open(season_2026_file, "r", encoding="utf-8") as f:
            s2026 = json.load(f)
    else:
        s2026 = {"season": "2026", "label": "Fall 2026", "events": [], "scores": {}, "standings": {}, "players": {}}

    if os.path.exists("scores.json"):
        with open("scores.json", "r", encoding="utf-8") as f:
            s2026["scores"] = json.load(f).get("scores", {})

    if os.path.exists("standings.json"):
        with open("standings.json", "r", encoding="utf-8") as f:
            s2026["standings"] = json.load(f).get("standings", {})

    if os.path.exists("players.json"):
        with open("players.json", "r", encoding="utf-8") as f:
            s2026["players"] = json.load(f).get("sports", {})

    if os.path.exists("schedule.json"):
        with open("schedule.json", "r", encoding="utf-8") as f:
            sched_data = json.load(f).get("schedule", {})
        for ev in s2026.get("events", []):
            key = f"{ev['sport']}|{ev['date']}"
            if key in sched_data:
                ev["isHome"] = sched_data[key]["isHome"]
                ev["venue"] = sched_data[key]["venue"]

    with open(season_2026_file, "w", encoding="utf-8") as f:
        json.dump(s2026, f, indent=2)

    # 2. Gather all seasons from seasons/*.json
    seasons_data = {}
    for fn in sorted(os.listdir("seasons")):
        if fn.endswith(".json"):
            s_key = fn.replace(".json", "")
            with open(os.path.join("seasons", fn), "r", encoding="utf-8") as f:
                seasons_data[s_key] = json.load(f)

    print(f"[*] Loaded {len(seasons_data)} season(s): {', '.join(seasons_data.keys())}")

    # 3. Read index.html
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    seasons_json_str = json.dumps(seasons_data)

    # Check if const SEASONS_DATA already exists
    if "const SEASONS_DATA =" in html:
        updated_html, count = re.subn(
            r"const SEASONS_DATA = \{.*?\};\n",
            lambda m: f"const SEASONS_DATA = {seasons_json_str};\n",
            html
        )
    else:
        # First time migration from flat variables to SEASONS_DATA
        target_pattern = r"const events = \[[\s\S]*?let currentPlayersData = INITIAL_PLAYERS;\n"
        replacement = (
            f"const SEASONS_DATA = {seasons_json_str};\n\n"
            "const SafeStorage = {\n"
            "  getItem: function(key) {\n"
            "    try { return localStorage.getItem(key); } catch (e) { return null; }\n"
            "  },\n"
            "  setItem: function(key, val) {\n"
            "    try { localStorage.setItem(key, val); } catch (e) {}\n"
            "  },\n"
            "  removeItem: function(key) {\n"
            "    try { localStorage.removeItem(key); } catch (e) {}\n"
            "  }\n"
            "};\n\n"
            "let currentSeason = SafeStorage.getItem('mhs_selected_season') || '2026';\n"
            "if (!SEASONS_DATA[currentSeason]) {\n"
            "  const available = Object.keys(SEASONS_DATA).sort();\n"
            "  currentSeason = available.length > 0 ? available[available.length - 1] : '2026';\n"
            "}\n\n"
            "let events = (SEASONS_DATA[currentSeason] && SEASONS_DATA[currentSeason].events) || [];\n"
            "let INITIAL_STANDINGS = (SEASONS_DATA[currentSeason] && SEASONS_DATA[currentSeason].standings) || {};\n"
            "let currentStandingsData = INITIAL_STANDINGS;\n"
            "let INITIAL_SCORES = (SEASONS_DATA[currentSeason] && SEASONS_DATA[currentSeason].scores) || {};\n"
            "let INITIAL_PLAYERS = (SEASONS_DATA[currentSeason] && SEASONS_DATA[currentSeason].players) || {};\n"
            "let currentPlayersData = INITIAL_PLAYERS;\n"
        )
        updated_html, count = re.subn(target_pattern, lambda m: replacement, html)

    if count > 0:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(updated_html)
        print(f"[✓] Successfully synchronized SEASONS_DATA in index.html ({count} replacement)")
    else:
        print("[-] Warning: Could not match SEASONS_DATA or flat variables in index.html")

if __name__ == "__main__":
    main()
