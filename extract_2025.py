#!/usr/bin/env python3
"""
MHS Fall 2025 Data Ingestion Script
Extracts complete Fall 2025 athletic data (Schedule, Scores, Standings, Rosters)
for Melrose High School from MaxPreps and ArbiterLive.
Saves output to seasons/2025.json.
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
        "name": "Football",
        "icon": "🏈"
    },
    "Boys' Soccer": {
        "slug": "soccer",
        "name": "Boys' Soccer",
        "icon": "⚽"
    },
    "Girls' Soccer": {
        "slug": "soccer/girls",
        "name": "Girls' Soccer",
        "icon": "⚽"
    },
    "Girls' Volleyball": {
        "slug": "volleyball",
        "name": "Girls' Volleyball",
        "icon": "🏐"
    },
    "Field Hockey": {
        "slug": "field-hockey",
        "name": "Field Hockey",
        "icon": "🏑"
    }
}

DEFAULT_CATEGORIES = {
    "Girls' Volleyball": {
        "icon": "🏐",
        "categories": [
            {"key": "kills", "label": "Kills", "short": "K"},
            {"key": "aces", "label": "Aces", "short": "ACE"},
            {"key": "digs", "label": "Digs", "short": "DIG"},
            {"key": "assists", "label": "Assists", "short": "AST"},
            {"key": "blocks", "label": "Blocks", "short": "BLK"}
        ]
    },
    "Boys' Soccer": {
        "icon": "⚽",
        "categories": [
            {"key": "goals", "label": "Goals", "short": "G"},
            {"key": "assists", "label": "Assists", "short": "A"},
            {"key": "points", "label": "Points", "short": "PTS"},
            {"key": "shots", "label": "Shots", "short": "SH"},
            {"key": "saves", "label": "Saves", "short": "SV"}
        ]
    },
    "Girls' Soccer": {
        "icon": "⚽",
        "categories": [
            {"key": "goals", "label": "Goals", "short": "G"},
            {"key": "assists", "label": "Assists", "short": "A"},
            {"key": "points", "label": "Points", "short": "PTS"},
            {"key": "shots", "label": "Shots", "short": "SH"},
            {"key": "saves", "label": "Saves", "short": "SV"}
        ]
    },
    "Football": {
        "icon": "🏈",
        "categories": [
            {"key": "passYds", "label": "Pass Yds", "short": "PASS"},
            {"key": "rushYds", "label": "Rush Yds", "short": "RUSH"},
            {"key": "recYds", "label": "Rec Yds", "short": "REC"},
            {"key": "totalTD", "label": "Touchdowns", "short": "TD"},
            {"key": "tackles", "label": "Tackles", "short": "TCK"}
        ]
    },
    "Field Hockey": {
        "icon": "🏑",
        "categories": [
            {"key": "goals", "label": "Goals", "short": "G"},
            {"key": "assists", "label": "Assists", "short": "A"},
            {"key": "points", "label": "Points", "short": "PTS"},
            {"key": "shots", "label": "Shots", "short": "SH"},
            {"key": "saves", "label": "Saves", "short": "SV"}
        ]
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
        except Exception:
            pass
    return None

def clean_school_name(raw_name):
    clean = re.sub(r'\s+(High School|Memorial|Veterans Memorial|HS|Academy).*$', '', raw_name, flags=re.IGNORECASE).strip()
    return clean if clean else raw_name

def parse_time_str(iso_string):
    if not iso_string or len(iso_string) < 16:
        return "TBA"
    time_part = iso_string[11:16]
    try:
        dt = datetime.strptime(time_part, "%H:%M")
        return dt.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return "TBA"

def get_home_venue(sport):
    if sport == "Girls' Volleyball": return "MVMMS"
    if sport == "Football": return "Fred Green Field"
    if sport == "Golf": return "Bellevue Golf Club"
    return "Pine Banks"

def fetch_volleyball_set_scores(match_url):
    if not match_url:
        return None
    try:
        html = fetch_url(match_url, timeout=8)
        tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
        for t in tables:
            headers = [re.sub(r'<[^>]+>', '', th).strip() for th in re.findall(r'<th[^>]*>(.*?)</th>', t[:1000], re.DOTALL)]
            set_headers = [h for h in headers if re.match(r'^S\d+$', h)]
            if not set_headers:
                continue
            tbody = re.search(r'<tbody>(.*?)</tbody>', t, re.DOTALL)
            if not tbody:
                continue
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbody.group(1), re.DOTALL)
            mhs_scores = []
            opp_scores = []
            for r in rows:
                is_mhs = 'melrose' in r.lower()
                tds = [re.sub(r'<[^>]+>', '', td).strip() for td in re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)]
                if len(tds) >= len(set_headers):
                    if is_mhs:
                        mhs_scores = [int(x) if x.isdigit() else 0 for x in tds[:len(set_headers)]]
                    else:
                        opp_scores = [int(x) if x.isdigit() else 0 for x in tds[:len(set_headers)]]
            if mhs_scores and opp_scores and len(mhs_scores) == len(opp_scores):
                sets = []
                for idx, (m_s, o_s) in enumerate(zip(mhs_scores, opp_scores)):
                    sets.append({
                        "label": f"Set {idx + 1}",
                        "score": f"{m_s}-{o_s}",
                        "win": m_s > o_s
                    })
                return sets
    except Exception:
        pass
    return None

def extract_fall_2025():
    print("[*] Starting extraction of Fall 2025 data...")
    events = []
    scores = {}
    standings = {}
    players = {}

    # 1. Extract 5 MaxPreps Sports (Football, Boys Soccer, Girls Soccer, Volleyball, Field Hockey)
    for sport_label, cfg in SPORTS_CONFIG.items():
        slug = cfg["slug"]
        print(f"\n[*] Processing {sport_label}...")

        # Schedule & Scores
        url = f"https://www.maxpreps.com/ma/melrose/melrose-red-hawks/{slug}/25-26/schedule/"
        try:
            html = fetch_url(url)
            data = extract_next_data(html)
            if data:
                contests = data.get("props", {}).get("pageProps", {}).get("contests", [])
                print(f"  Found {len(contests)} raw contests on MaxPreps")
                for c in contests:
                    teams = c[0]
                    if len(teams) < 2:
                        continue
                    mhs = next((t for t in teams if "melrose" in t[14].lower()), None)
                    opp = next((t for t in teams if "melrose" not in t[14].lower()), None)
                    if not mhs or not opp:
                        continue

                    g_type = c[21] if len(c) > 21 else "Game"
                    if g_type == "Scrimmage":
                        continue

                    iso_date = c[11][:10] if len(c) > 11 and c[11] else ""
                    if not iso_date or not iso_date.startswith("2025"):
                        continue

                    time_str = parse_time_str(c[11])
                    opp_full = opp[14]
                    opp_short = clean_school_name(opp_full)
                    is_home = (mhs[4] == 1)
                    venue = get_home_venue(sport_label) if is_home else opp_short

                    event = {
                        "date": iso_date,
                        "time": time_str,
                        "sport": sport_label,
                        "opp": opp_short,
                        "isHome": is_home,
                        "venue": venue
                    }
                    events.append(event)

                    # Score check
                    m_score = mhs[6] if mhs[6] is not None else mhs[3]
                    o_score = opp[6] if opp[6] is not None else opp[3]
                    m_res = mhs[5]

                    if m_score is not None and o_score is not None:
                        if not m_res:
                            if m_score > o_score: m_res = "W"
                            elif m_score < o_score: m_res = "L"
                            else: m_res = "T"

                        score_key = f"{sport_label}|{iso_date}"
                        score_entry = {
                            "sport": sport_label,
                            "date": iso_date,
                            "opponent": opp_full,
                            "mhsScore": m_score,
                            "oppScore": o_score,
                            "result": m_res,
                            "status": "Final",
                            "isHome": is_home,
                            "source": "MaxPreps"
                        }
                        if sport_label == "Girls' Volleyball" and len(c) > 18 and c[18]:
                            sets = fetch_volleyball_set_scores(c[18])
                            if sets:
                                score_entry["setScores"] = sets

                        scores[score_key] = score_entry
        except Exception as e:
            print(f"  Error extracting schedule/scores: {e}")

        # Standings
        s_url = f"https://www.maxpreps.com/ma/melrose/melrose-red-hawks/{slug}/25-26/standings/"
        try:
            s_html = fetch_url(s_url)
            s_data = extract_next_data(s_html)
            if s_data:
                sections = s_data.get("props", {}).get("pageProps", {}).get("standingsData", {}).get("standingSections", [])
                if sections:
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
                                    clean_cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
                                    school_name = clean_cells[1]
                                    img_match = re.search(r'<img[^>]*src="([^"]+)"', cells[1])
                                    mascot = img_match.group(1) if img_match else ""
                                    is_mhs = "melrose" in school_name.lower()
                                    teams.append({
                                        "rank": clean_cells[0],
                                        "school": school_name,
                                        "confRecord": clean_cells[2],
                                        "confPct": clean_cells[3],
                                        "overallRecord": clean_cells[4],
                                        "overallPct": clean_cells[5],
                                        "streak": clean_cells[10],
                                        "mascot": mascot,
                                        "isMHS": is_mhs
                                    })
                    if teams:
                        standings[sport_label] = {
                            "leagueName": league_name,
                            "leagueUrl": league_url,
                            "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "teams": teams
                        }
                        print(f"  Extracted standings: {len(teams)} teams")
        except Exception as e:
            print(f"  Error extracting standings: {e}")

        # Rosters & Stats
        r_url = f"https://www.maxpreps.com/ma/melrose/melrose-red-hawks/{slug}/25-26/roster/"
        try:
            r_html = fetch_url(r_url)
            r_data = extract_next_data(r_html)
            roster = []
            if r_data:
                athletes = r_data.get("props", {}).get("pageProps", {}).get("athleteData", [])
                for a in athletes:
                    aid = a[4] if len(a) > 4 else ""
                    first = a[0] if len(a) > 0 else ""
                    last = a[1] if len(a) > 1 else ""
                    jersey = str(a[2]) if len(a) > 2 and a[2] is not None else ""
                    pos = a[3] if len(a) > 3 and a[3] else ""
                    yr = a[6] if len(a) > 6 and a[6] else ""
                    purl = a[10] if len(a) > 10 and a[10] else ""
                    roster.append({
                        "id": aid,
                        "firstName": first,
                        "lastName": last,
                        "fullName": f"{first} {last}".strip(),
                        "jersey": jersey,
                        "position": pos,
                        "year": yr,
                        "profileUrl": purl,
                        "stats": {}
                    })

            defaults = DEFAULT_CATEGORIES.get(sport_label, {"icon": "🏅", "categories": []})
            if roster:
                players[sport_label] = {
                    "sport": sport_label,
                    "icon": defaults["icon"],
                    "categories": defaults["categories"],
                    "roster": roster
                }
                print(f"  Extracted roster: {len(roster)} players")
        except Exception as e:
            print(f"  Error extracting roster: {e}")

    # 2. Extract Golf from ArbiterLive (Team 9009654, SelectedSchoolYearID=92)
    print("\n[*] Processing Golf from ArbiterLive (2025-26)...")
    months = {
        'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06',
        'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'
    }
    golf_url = "https://www.arbiterlive.com/Teams/Schedule/9009654?activeEntityId=14381&selectedSchoolYearId=92"
    try:
        g_html = fetch_url(golf_url)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', g_html, re.DOTALL)
        golf_count = 0
        for r in rows:
            tds = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)
            if len(tds) < 4:
                continue
            cleaned = [' '.join(re.sub(r'<[^>]+>', ' ', td).split()) for td in tds]
            date_col = cleaned[0]
            d_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\b', date_col)
            if not d_match:
                continue
            m_str, d_str = d_match.group(1), d_match.group(2).zfill(2)
            iso_date = f"2025-{months[m_str]}-{d_str}"

            # time
            t_match = re.search(r'\b(\d{1,2}:\d{2}\s*(?:AM|PM))\b', date_col, re.IGNORECASE)
            time_str = t_match.group(1).upper() if t_match else "TBA"

            is_home = (cleaned[1] == 'vs')
            opp_full = cleaned[2]
            opp_short = clean_school_name(opp_full)
            venue = "Bellevue Golf Club" if is_home else opp_short

            events.append({
                "date": iso_date,
                "time": time_str,
                "sport": "Golf",
                "opp": opp_short,
                "isHome": is_home,
                "venue": venue
            })
            golf_count += 1

            # score
            res_col = cleaned[4] if len(cleaned) > 4 else ""
            m_res = re.search(r'\b([WLT])\s*([\d\.]+)\s*-\s*([\d\.]+)', res_col)
            if m_res:
                res_letter = m_res.group(1)
                mhs_s = float(m_res.group(2)) if '.' in m_res.group(2) else int(m_res.group(2))
                opp_s = float(m_res.group(3)) if '.' in m_res.group(3) else int(m_res.group(3))
                scores[f"Golf|{iso_date}"] = {
                    "sport": "Golf",
                    "date": iso_date,
                    "opponent": opp_full,
                    "mhsScore": mhs_s,
                    "oppScore": opp_s,
                    "result": "WIN" if res_letter == 'W' else ("LOSS" if res_letter == 'L' else "TIE"),
                    "status": "Final",
                    "isHome": is_home,
                    "source": "ArbiterLive"
                }
        print(f"  Extracted Golf: {golf_count} games")
    except Exception as e:
        print(f"  Error extracting Golf: {e}")

    # 3. Extract Cross Country from ArbiterLive (Boys Team 4332481, SelectedSchoolYearID=92)
    print("\n[*] Processing Cross Country from ArbiterLive (2025-26)...")
    xc_url = "https://www.arbiterlive.com/Teams/Schedule/4332481?activeEntityId=14381&selectedSchoolYearId=92"
    try:
        xc_html = fetch_url(xc_url)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', xc_html, re.DOTALL)
        xc_count = 0
        for r in rows:
            tds = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)
            if len(tds) < 4:
                continue
            cleaned = [' '.join(re.sub(r'<[^>]+>', ' ', td).split()) for td in tds]
            date_col = cleaned[0]
            d_match = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\b', date_col)
            if not d_match:
                continue
            m_str, d_str = d_match.group(1), d_match.group(2).zfill(2)
            iso_date = f"2025-{months[m_str]}-{d_str}"

            t_match = re.search(r'\b(\d{1,2}:\d{2}\s*(?:AM|PM))\b', date_col, re.IGNORECASE)
            time_str = t_match.group(1).upper() if t_match else "TBA"

            is_home = (cleaned[1] == 'vs')
            opp_full = cleaned[2]
            opp_short = clean_school_name(opp_full)
            venue = "Pine Banks" if is_home else opp_short

            events.append({
                "date": iso_date,
                "time": time_str,
                "sport": "Cross Country",
                "opp": opp_short,
                "isHome": is_home,
                "venue": venue
            })
            xc_count += 1

            res_col = cleaned[4] if len(cleaned) > 4 else ""
            m_res = re.search(r'\b([WLT])\s*([\d\.]+)\s*-\s*([\d\.]+)', res_col)
            if m_res:
                res_letter = m_res.group(1)
                mhs_s = int(float(m_res.group(2)))
                opp_s = int(float(m_res.group(3)))
                scores[f"Cross Country|{iso_date}"] = {
                    "sport": "Cross Country",
                    "date": iso_date,
                    "opponent": opp_full,
                    "mhsScore": mhs_s,
                    "oppScore": opp_s,
                    "result": "WIN" if res_letter == 'W' else ("LOSS" if res_letter == 'L' else "TIE"),
                    "status": "Final",
                    "isHome": is_home,
                    "source": "ArbiterLive"
                }
        print(f"  Extracted Cross Country: {xc_count} meets")
    except Exception as e:
        print(f"  Error extracting Cross Country: {e}")

    # Sort events by date and time
    events.sort(key=lambda x: (x["date"], x["time"]))

    season_2025_data = {
        "season": "2025",
        "label": "Fall 2025",
        "lastUpdated": datetime.now().isoformat(),
        "events": events,
        "scores": scores,
        "standings": standings,
        "players": players
    }

    os.makedirs("seasons", exist_ok=True)
    out_file = os.path.join("seasons", "2025.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(season_2025_data, f, indent=2)

    print(f"\n[✓] Successfully generated {out_file}!")
    print(f"    Total Events   : {len(events)}")
    print(f"    Total Scores   : {len(scores)}")
    print(f"    Standings Sports: {len(standings)}")
    print(f"    Rosters Sports : {len(players)}")

if __name__ == "__main__":
    extract_fall_2025()
