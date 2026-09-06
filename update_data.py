#!/usr/bin/env python3
"""
MHS Sports Data Updater
Fetches 2026 Middlesex League standings and live game scores from MaxPreps for Melrose High School.
Only attaches scores to official games in the 2026 Fall Varsity Schedule.
Generates scores.json and standings.json for the MHS web app.
"""

import json
import os
import re
import ssl
import sys
import urllib.request
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
CTX = ssl.create_default_context()

SPORTS_CONFIG = {
    "Football": {
        "slug": "football",
        "name": "Football"
    },
    "Boys' Soccer": {
        "slug": "soccer",
        "name": "Boys' Soccer"
    },
    "Girls' Soccer": {
        "slug": "soccer/girls",
        "name": "Girls' Soccer"
    },
    "Girls' Volleyball": {
        "slug": "volleyball",
        "name": "Girls' Volleyball"
    },
    "Field Hockey": {
        "slug": "field-hockey",
        "name": "Field Hockey"
    }
}

def fetch_url(url, timeout=12):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
        return resp.read().decode("utf-8")

def extract_next_data(html):
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception as e:
            print(f"Error parsing JSON: {e}")
    return None

def load_scheduled_keys():
    """Load official 2026 schedule keys (sport|date) from index.html"""
    scheduled = set()
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        matches = re.findall(r'date:\s*"([^"]+)",\s*time:\s*"[^"]+",\s*sport:\s*"([^"]+)"', content)
        for d, s in matches:
            scheduled.add(f"{s}|{d}")
    return scheduled

def fetch_scores(scheduled_keys):
    print("[*] Checking for completed 2026 game scores on MaxPreps...")
    scores_by_key = {}
    total_found = 0

    for sport_label, cfg in SPORTS_CONFIG.items():
        slug = cfg["slug"]
        url = f"https://www.maxpreps.com/ma/melrose/melrose-red-hawks/{slug}/schedule/"
        try:
            html = fetch_url(url)
            data = extract_next_data(html)
            if not data:
                continue

            contests = data.get("props", {}).get("pageProps", {}).get("contests", [])
            sport_scores = 0

            for c in contests:
                teams = c[0]
                if len(teams) < 2:
                    continue

                mhs = next((t for t in teams if "melrose" in t[14].lower()), None)
                opp = next((t for t in teams if "melrose" not in t[14].lower()), None)
                if not mhs or not opp:
                    continue

                iso_date = c[11][:10] if len(c) > 11 and c[11] else ""
                key = f"{sport_label}|{iso_date}"

                # Only include scores for games present in the 2026 Varsity Schedule
                if key not in scheduled_keys:
                    continue

                mhs_res = mhs[5]
                mhs_score = mhs[6] if mhs[6] is not None else mhs[3]
                opp_score = opp[6] if opp[6] is not None else opp[3]

                if mhs_res is not None or mhs_score is not None:
                    if not mhs_res and mhs_score is not None and opp_score is not None:
                        if mhs_score > opp_score:
                            mhs_res = "W"
                        elif mhs_score < opp_score:
                            mhs_res = "L"
                        else:
                            mhs_res = "T"

                    scores_by_key[key] = {
                        "sport": sport_label,
                        "date": iso_date,
                        "opponent": opp[14],
                        "mhsScore": mhs_score,
                        "oppScore": opp_score,
                        "result": mhs_res,
                        "status": "Final",
                        "isHome": mhs[4] == 1,
                        "source": "MaxPreps"
                    }
                    sport_scores += 1
                    total_found += 1

            if sport_scores > 0:
                print(f"  [+] {sport_label:18}: {sport_scores} completed score(s)")
        except Exception as e:
            print(f"  [x] {sport_label}: Error fetching scores ({e})")

    print(f"[*] Total completed 2026 varsity games: {total_found}")
    return scores_by_key

def fetch_standings():
    print("[*] Fetching 2026 Middlesex League standings from MaxPreps...")
    standings_data = {}

    for sport_label, cfg in SPORTS_CONFIG.items():
        slug = cfg["slug"]
        team_standings_url = f"https://www.maxpreps.com/ma/melrose/melrose-red-hawks/{slug}/standings/"
        try:
            html = fetch_url(team_standings_url)
            data = extract_next_data(html)
            if not data:
                continue

            sections = data.get("props", {}).get("pageProps", {}).get("standingsData", {}).get("standingSections", [])
            if not sections:
                continue

            league_sec = sections[0]
            league_name = league_sec.get("headerName") or "Middlesex League"
            league_url = league_sec.get("fullStandingsLink")

            teams = []
            if league_url:
                l_html = fetch_url(league_url)
                tables = re.findall(r"<table[^>]*>(.*?)</table>", l_html, re.DOTALL)
                if tables:
                    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tables[0], re.DOTALL)
                    for r in rows[2:]:
                        cells = re.findall(r"<td[^>]*>(.*?)</td>", r, re.DOTALL)
                        if len(cells) >= 11:
                            rank = re.sub(r"<[^>]+>", "", cells[0]).strip()
                            name_m = re.search(r'<span class="school-name">([^<]+)</span>', cells[1])
                            sname = name_m.group(1).strip() if name_m else re.sub(r"<[^>]+>", "", cells[1]).strip()
                            conf_wl = re.sub(r"<[^>]+>", "", cells[2]).strip()
                            conf_pct = re.sub(r"<[^>]+>", "", cells[3]).strip()
                            overall_wl = re.sub(r"<[^>]+>", "", cells[6]).strip()
                            overall_pct = re.sub(r"<[^>]+>", "", cells[7]).strip()
                            streak = re.sub(r"<[^>]+>", "", cells[10]).strip()
                            mascot_m = re.search(r'<img[^>]+src="([^"]+)"', cells[1])
                            mascot = mascot_m.group(1).replace("&amp;", "&") if mascot_m else ""

                            teams.append({
                                "rank": rank,
                                "school": sname,
                                "confRecord": conf_wl,
                                "confPct": conf_pct,
                                "overallRecord": overall_wl,
                                "overallPct": overall_pct,
                                "streak": streak,
                                "mascot": mascot,
                                "isMHS": "melrose" in sname.lower()
                            })

            standings_data[sport_label] = {
                "leagueName": league_name,
                "leagueUrl": league_url,
                "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "teams": teams
            }
            print(f"  [+] {sport_label:18}: {league_name} ({len(teams)} teams)")
        except Exception as e:
            print(f"  [x] {sport_label}: Error fetching standings ({e})")

    return standings_data

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("=" * 60)
    print(f"MHS 2026 Sports Data Sync - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    scheduled_keys = load_scheduled_keys()
    print(f"[*] Loaded {len(scheduled_keys)} official 2026 varsity games")

    scores = fetch_scores(scheduled_keys)
    scores_payload = {
        "lastUpdated": datetime.now().isoformat(),
        "scores": scores
    }
    with open("scores.json", "w", encoding="utf-8") as f:
        json.dump(scores_payload, f, indent=2)
    print(f"[✓] Saved scores.json ({len(scores)} completed varsity scores)")

    standings = fetch_standings()
    standings_payload = {
        "lastUpdated": datetime.now().isoformat(),
        "standings": standings
    }
    with open("standings.json", "w", encoding="utf-8") as f:
        json.dump(standings_payload, f, indent=2)
    print(f"[✓] Saved standings.json ({len(standings)} sports standings)")

    build_script = os.path.join(script_dir, "build_index.py")
    if os.path.exists(build_script):
        try:
            import subprocess
            subprocess.run([sys.executable, build_script], check=True)
            print("[✓] Synchronized index.html")
        except Exception as e:
            print(f"[-] Warning: build_index.py sync failed: {e}")

    print("=" * 60)
    print("Sync complete!")

if __name__ == "__main__":
    main()
