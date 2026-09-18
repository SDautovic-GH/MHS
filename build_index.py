#!/usr/bin/env python3
"""
MHS Index Standings Synchronizer
Safely updates the embedded INITIAL_STANDINGS data inside index.html without touching markup or styles.
"""
import json
import re
import os

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    if not os.path.exists("standings.json") or not os.path.exists("index.html"):
        print("[-] Missing standings.json or index.html")
        return

    with open("standings.json", "r", encoding="utf-8") as f:
        standings_data = json.load(f)

    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    new_standings_json = json.dumps(standings_data.get("standings", {}))
    updated_html, count = re.subn(
        r"const INITIAL_STANDINGS = \{.*?\};",
        lambda m: f"const INITIAL_STANDINGS = {new_standings_json};",
        html
    )

    s_count = 0
    if os.path.exists("scores.json"):
        with open("scores.json", "r", encoding="utf-8") as f:
            scores_data = json.load(f)
        new_scores_json = json.dumps(scores_data.get("scores", {}))
        updated_html, s_count = re.subn(
            r"const INITIAL_SCORES = \{.*?\};",
            lambda m: f"const INITIAL_SCORES = {new_scores_json};",
            updated_html
        )
        if s_count > 0:
            print(f"[✓] Successfully synchronized embedded INITIAL_SCORES in index.html")

    p_count = 0
    if os.path.exists("players.json"):
        with open("players.json", "r", encoding="utf-8") as f:
            players_data = json.load(f)
        new_players_json = json.dumps(players_data.get("sports", {}))
        updated_html, p_count = re.subn(
            r"const INITIAL_PLAYERS = \{.*?\};",
            lambda m: f"const INITIAL_PLAYERS = {new_players_json};",
            updated_html
        )
        if p_count > 0:
            print(f"[✓] Successfully synchronized embedded INITIAL_PLAYERS in index.html")

    loc_count = 0
    if os.path.exists("schedule.json"):
        with open("schedule.json", "r", encoding="utf-8") as f:
            sched_data = json.load(f).get("schedule", {})

        def replacer(m):
            d, t, s, opp, is_home, venue = m.groups()
            key = f"{s}|{d}"
            if key in sched_data:
                upd = sched_data[key]
                new_is_home = "true" if upd["isHome"] else "false"
                new_venue = upd["venue"]
                if is_home != new_is_home or venue != new_venue:
                    nonlocal loc_count
                    loc_count += 1
                return f'{{ date: "{d}", time: "{t}", sport: "{s}", opp: "{opp}", isHome: {new_is_home}, venue: "{new_venue}" }}'
            return m.group(0)

        pattern = r'\{\s*date:\s*"([^"]+)",\s*time:\s*"([^"]+)",\s*sport:\s*"([^"]+)",\s*opp:\s*"([^"]+)",\s*isHome:\s*(true|false),\s*venue:\s*"([^"]+)"\s*\}'
        updated_html = re.sub(pattern, replacer, updated_html)
        if loc_count > 0:
            print(f"[✓] Successfully synchronized {loc_count} game location(s) in events array")

    if count > 0 or s_count > 0 or p_count > 0 or loc_count > 0:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(updated_html)
        print(f"[✓] Successfully updated index.html (standings: {count}, scores: {s_count}, players: {p_count}, locations: {loc_count})")
    else:
        print("[-] Warning: No embedded data patterns matched in index.html")

if __name__ == "__main__":
    main()
