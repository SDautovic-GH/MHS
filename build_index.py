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

    if count > 0:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(updated_html)
        print(f"[✓] Successfully synchronized embedded INITIAL_STANDINGS in index.html")
    else:
        print("[-] Warning: Could not locate INITIAL_STANDINGS in index.html")

if __name__ == "__main__":
    main()
