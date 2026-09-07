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

# ArbiterLive Team IDs for Melrose High School (Entity ID: 14381)
# Official MIAA platform used by athletic directors for schedules and scores
ARBITER_TEAMS = {
    "Golf": "9009654",
    "Football": "856419",
    "Boys' Soccer": "5616965",
    "Girls' Soccer": "5616968",
    "Girls' Volleyball": "4044277",
    "Field Hockey": "4285421",
    "Boys' Cross Country": "7773306",
    "Girls' Cross Country": "7928429",
    "Girls' Swimming": "4332482"
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

def load_scheduled_events():
    """Load official 2026 schedule events (keyed by sport|date) from index.html"""
    events = {}
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        matches = re.findall(
            r'date:\s*"([^"]+)",\s*time:\s*"[^"]+",\s*sport:\s*"([^"]+)",\s*opp:\s*"([^"]+)",\s*isHome:\s*(true|false)',
            content
        )
        for d, s, opp, is_home in matches:
            events[f"{s}|{d}"] = {
                "sport": s,
                "date": d,
                "opponent": opp,
                "isHome": is_home == "true"
            }
    return events

def fetch_arbiter_scores(scheduled_events):
    print("[*] Checking for completed game scores on ArbiterLive (MIAA)...")
    months = {
        'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06',
        'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'
    }
    arbiter_scores = {}
    total_found = 0

    for sport_label, team_id in ARBITER_TEAMS.items():
        url = f"https://www.arbiterlive.com/Teams/Schedule/{team_id}?activeEntityId=14381"
        try:
            html = fetch_url(url, timeout=10)
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL)
            sport_found = 0
            for r in rows:
                tds = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)
                if len(tds) < 5:
                    continue
                cleaned = [' '.join(re.sub(r'<[^>]+>', ' ', td).split()) for td in tds]
                date_col = cleaned[0]
                date_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\b', date_col)
                if not date_match:
                    continue
                m_str, d_str = date_match.group(1), date_match.group(2).zfill(2)
                iso_date = f"2026-{months[m_str]}-{d_str}"
                key = f"{sport_label}|{iso_date}"

                if key not in scheduled_events:
                    continue

                res_col = ''
                for col in cleaned[3:]:
                    if re.search(r'\b[WLT]\s*[\d\.]+\s*-\s*[\d\.]+', col):
                        res_col = col
                        break

                if res_col:
                    m = re.search(r'\b([WLT])\s*([\d\.]+)\s*-\s*([\d\.]+)', res_col)
                    if m:
                        res_letter = m.group(1)
                        mhs_score = float(m.group(2)) if '.' in m.group(2) else int(m.group(2))
                        opp_score = float(m.group(3)) if '.' in m.group(3) else int(m.group(3))
                        res_word = 'WIN' if res_letter == 'W' else ('LOSS' if res_letter == 'L' else 'TIE')
                        ev = scheduled_events[key]
                        arbiter_scores[key] = {
                            "sport": sport_label,
                            "date": iso_date,
                            "opponent": ev["opponent"],
                            "mhsScore": mhs_score,
                            "oppScore": opp_score,
                            "result": res_word,
                            "status": "Final",
                            "isHome": ev["isHome"],
                            "source": "ArbiterLive"
                        }
                        sport_found += 1
                        total_found += 1

            if sport_found > 0:
                print(f"  [+] {sport_label:18}: {sport_found} completed score(s)")
        except Exception as e:
            print(f"  [x] {sport_label:18}: ArbiterLive error ({e})")

    print(f"[*] Total ArbiterLive scores retrieved: {total_found}")
    return arbiter_scores

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

GIRLS_VOLLEYBALL_JERSEYS = {
    "Gen Overlan": "1",
    "Anna Burns": "2",
    "Kayla Ton": "3",
    "Leila Kiggundu": "4",
    "Sadie Smith": "6",
    "Dani DiGiorgio": "7",
    "Daniella DiGiorgio": "7",
    "Amelie Johnson": "8",
    "Adriana Santoriello": "9",
    "Alisa Dautovic": "10",
    "Maggie Shoemaker": "11",
    "Mia Sasso": "12",
    "Sabrina McArt": "13",
    "Ella Friedlaender": "14",
    "Elise Marchais": "15",
    "Lorena Contin": "16",
}

def fetch_maxpreps_rosters():
    print("[*] Checking for official team rosters on MaxPreps...")
    existing_players = {}
    if os.path.exists("players.json"):
        try:
            with open("players.json", "r", encoding="utf-8") as f:
                existing_players = json.load(f).get("sports", {})
        except Exception:
            pass

    for sport_label, cfg in SPORTS_CONFIG.items():
        slug = cfg["slug"]
        url = f"https://www.maxpreps.com/ma/melrose/melrose-red-hawks/{slug}/roster/"
        try:
            html = fetch_url(url, timeout=10)
            data = extract_next_data(html)
            if not data:
                continue
            athletes = data.get("props", {}).get("pageProps", {}).get("athleteData", [])
            if not athletes or len(athletes) == 0:
                continue

            current_sport_data = existing_players.get(sport_label, {})
            current_roster_map = {p["id"]: p for p in current_sport_data.get("roster", []) if p.get("id")}
            updated_roster = []

            for a in athletes:
                aid = a[4] if len(a) > 4 else ""
                fname = a[5] if len(a) > 5 else ""
                lname = a[6] if len(a) > 6 else ""
                fullname = a[33] if len(a) > 33 and a[33] else f"{fname} {lname}"
                
                # Assign verified official jersey number if known, otherwise existing, otherwise empty
                jersey = ""
                if sport_label == "Girls' Volleyball":
                    jersey = GIRLS_VOLLEYBALL_JERSEYS.get(fullname, GIRLS_VOLLEYBALL_JERSEYS.get(f"{fname} {lname}", ""))
                if not jersey:
                    existing_p = current_roster_map.get(aid, {})
                    jersey = existing_p.get("jersey", "")

                pos = a[12] if len(a) > 12 and a[12] else ""
                yr = a[36] if len(a) > 36 and a[36] else ""
                purl = a[31] if len(a) > 31 and a[31] else ""

                existing_p = current_roster_map.get(aid, {})
                stats = existing_p.get("stats", {})

                updated_roster.append({
                    "id": aid,
                    "firstName": fname,
                    "lastName": lname,
                    "fullName": fullname,
                    "jersey": str(jersey) if jersey else "",
                    "position": pos,
                    "year": yr,
                    "profileUrl": purl,
                    "stats": stats
                })

            if len(updated_roster) > 0:
                # Sort roster numerically by jersey number if available
                try:
                    updated_roster.sort(key=lambda x: int(x["jersey"]) if x.get("jersey") and str(x["jersey"]).isdigit() else 999)
                except Exception:
                    pass

                if sport_label not in existing_players:
                    existing_players[sport_label] = {"sport": sport_label, "roster": []}
                existing_players[sport_label]["roster"] = updated_roster
                print(f"  [+] {sport_label:18}: {len(updated_roster)} athletes synced from MaxPreps")
        except Exception as e:
            print(f"  [-] {sport_label:18}: Roster error ({e})")

    return existing_players

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("=" * 60)
    print(f"MHS 2026 Sports Data Sync - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    scheduled_events = load_scheduled_events()
    scheduled_keys = set(scheduled_events.keys())
    print(f"[*] Loaded {len(scheduled_keys)} official 2026 varsity games")

    # Fetch from ArbiterLive (MIAA official hub - covers Golf, Cross Country, Swimming, and all varsity sports)
    arbiter_scores = fetch_arbiter_scores(scheduled_events)

    # Fetch from MaxPreps (Football, Volleyball, Soccer, Field Hockey)
    maxpreps_scores = fetch_scores(scheduled_keys)

    existing_scores = {}
    if os.path.exists("scores.json"):
        try:
            with open("scores.json", "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                existing_scores = existing_data.get("scores", {})
        except Exception:
            pass

    # Merge: existing manual scores, updated by ArbiterLive and MaxPreps
    existing_scores.update(arbiter_scores)
    existing_scores.update(maxpreps_scores)
    scores_payload = {
        "lastUpdated": datetime.now().isoformat(),
        "scores": existing_scores
    }
    with open("scores.json", "w", encoding="utf-8") as f:
        json.dump(scores_payload, f, indent=2)
    print(f"[✓] Saved scores.json ({len(existing_scores)} completed varsity scores)")

    standings = fetch_standings()
    standings_payload = {
        "lastUpdated": datetime.now().isoformat(),
        "standings": standings
    }
    with open("standings.json", "w", encoding="utf-8") as f:
        json.dump(standings_payload, f, indent=2)
    print(f"[✓] Saved standings.json ({len(standings)} sports standings)")

    players_data = fetch_maxpreps_rosters()
    players_payload = {
        "lastUpdated": datetime.now().isoformat(),
        "sports": players_data
    }
    with open("players.json", "w", encoding="utf-8") as f:
        json.dump(players_payload, f, indent=2)
    print(f"[✓] Saved players.json ({len(players_data)} sports rosters synced)")

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
