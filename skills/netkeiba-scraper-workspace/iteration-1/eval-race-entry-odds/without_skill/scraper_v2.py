#!/usr/bin/env python3
"""
netkeibaから出走表・オッズを取得するスクリプト（スキルなし版）。
Race ID: 202506010111
日付: 2025年1月5日
競馬場: 中山競馬場
レース: 第11レース
"""

import sys
import json
import time
import requests
from bs4 import BeautifulSoup

RACE_ID = "202506010111"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
}

GATE_COLORS = {
    "1": "白", "2": "黒", "3": "赤", "4": "青",
    "5": "黄", "6": "緑", "7": "橙", "8": "桃",
}


def get_race_entry(race_id: str):
    """出走表を取得する"""
    url = f"https://race.netkeiba.com/race/shutuba.html?race_id={race_id}"
    print(f"出走表URL: {url}")

    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    resp.encoding = "EUC-JP"

    soup = BeautifulSoup(resp.text, "html.parser")

    # レース情報
    race_info = {}
    title = soup.select_one(".RaceName, .RaceTitle")
    race_info["race_name"] = title.get_text(strip=True) if title else "-"

    data01 = soup.select_one(".RaceData01")
    race_info["race_detail"] = " ".join(data01.get_text(" ", strip=True).split()) if data01 else "-"

    data02 = soup.select_one(".RaceData02")
    race_info["race_meta"] = " ".join(data02.get_text(" ", strip=True).split()) if data02 else "-"

    # 出走馬
    horses = []
    table = soup.select_one(".ShutubaTable, #shutuba_table")
    if not table:
        table = soup.find("table", class_=lambda x: x and "Shutuba" in x)

    if table:
        for row in table.select("tr.HorseList, tr[class*='HorseList']"):
            cells = row.find_all("td")
            if len(cells) < 5:
                continue

            horse = {}

            waku = row.select_one(".Waku, [class*='Waku']")
            horse["waku"] = waku.get_text(strip=True) if waku else cells[0].get_text(strip=True)

            umaban = row.select_one(".Umaban, [class*='Umaban']")
            horse["umaban"] = umaban.get_text(strip=True) if umaban else ""

            horse_name_elem = row.select_one(".HorseName a, .Horse_Name a")
            if horse_name_elem:
                horse["horse_name"] = horse_name_elem.get_text(strip=True)
                href = horse_name_elem.get("href", "")
                horse["horse_id"] = href.split("/horse/")[1].strip("/") if "/horse/" in href else ""
            else:
                horse["horse_name"] = ""
                horse["horse_id"] = ""

            seireii = row.select_one(".Barei, .HorseSex")
            horse["seireii"] = seireii.get_text(strip=True) if seireii else ""

            # 斤量検出
            kinryo_cell = None
            for cell in cells:
                text = cell.get_text(strip=True)
                try:
                    val = float(text.replace("▲", "").replace("△", "").replace("☆", ""))
                    if 48 <= val <= 62:
                        kinryo_cell = text
                except ValueError:
                    pass
            horse["kinryo"] = kinryo_cell or ""

            jockey_elem = row.select_one(".Jockey a, .RiderName a")
            horse["jockey"] = jockey_elem.get_text(strip=True) if jockey_elem else ""

            trainer_elem = row.select_one(".Trainer a, .TrainerName a")
            horse["trainer"] = trainer_elem.get_text(strip=True) if trainer_elem else ""

            weight_elem = row.select_one(".Weight, .HorseWeight")
            horse["weight"] = weight_elem.get_text(strip=True) if weight_elem else ""

            if horse["horse_name"]:
                horses.append(horse)

    return race_info, horses


def print_entry(race_info: dict, horses: list, race_id: str):
    print(f"\n=== 出走表 [{race_id}] ===")
    print(f"レース名  : {race_info.get('race_name', '-')}")
    print(f"レース詳細: {race_info.get('race_detail', '-')}")
    print(f"開催情報  : {race_info.get('race_meta', '-')}")
    print()

    if not horses:
        print("出走馬情報が取得できませんでした。")
        return

    print(f"{'枠':<3} {'馬番':<4} {'馬名':<18} {'性齢':<5} {'斤量':<5} {'騎手':<12} {'調教師':<12} {'馬体重':<10} 馬ID")
    print("-" * 90)

    for h in horses:
        gate_color = GATE_COLORS.get(h.get("waku", ""), "")
        waku_str = f"{h.get('waku', '')}({gate_color})" if gate_color else h.get("waku", "")
        print(
            f"{waku_str:<5} {h.get('umaban', ''):<4} {h.get('horse_name', ''):<18} "
            f"{h.get('seireii', ''):<5} {h.get('kinryo', ''):<5} {h.get('jockey', ''):<12} "
            f"{h.get('trainer', ''):<12} {h.get('weight', ''):<10} {h.get('horse_id', '')}"
        )
    print(f"\n出走頭数: {len(horses)}頭\n")


def get_tansho_fukusho_odds(race_id: str):
    """単勝・複勝オッズをAPIから取得"""
    url = f"https://race.netkeiba.com/api/api_get_jra_odds.html?race_id={race_id}&type=b1&action=update"
    print(f"オッズAPI URL: {url}")

    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    resp.encoding = "UTF-8"

    data = {"tansho": [], "fukusho": []}

    try:
        json_data = resp.json()
        odds_data = json_data.get("data", {}).get("odds", {})

        for num, val in odds_data.get("1", {}).items():
            if isinstance(val, list) and len(val) >= 1:
                data["tansho"].append({"num": num, "odds": val[0]})
            elif isinstance(val, str):
                data["tansho"].append({"num": num, "odds": val})

        for num, val in odds_data.get("3", {}).items():
            if isinstance(val, list) and len(val) >= 2:
                data["fukusho"].append({"num": num, "odds_low": val[0], "odds_high": val[1]})
            elif isinstance(val, str):
                data["fukusho"].append({"num": num, "odds_low": val, "odds_high": val})

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"JSON解析エラー: {e}")
        data = {}

    return data


def print_tansho_fukusho(data: dict, race_id: str):
    print(f"\n=== 単勝・複勝オッズ [{race_id}] ===\n")

    tansho = sorted(data.get("tansho", []), key=lambda x: int(x.get("num", 99)))
    fukusho = sorted(data.get("fukusho", []), key=lambda x: int(x.get("num", 99)))

    if tansho or fukusho:
        max_len = max(len(tansho), len(fukusho))
        print(f"{'馬番':<4} {'単勝オッズ':<12}  {'馬番':<4} {'複勝オッズ（低-高）'}")
        print("-" * 45)
        for i in range(max_len):
            t = tansho[i] if i < len(tansho) else {}
            f = fukusho[i] if i < len(fukusho) else {}
            t_str = f"{t.get('num', ''):<4} {t.get('odds', '-'):<12}" if t else " " * 16
            f_str = f"{f.get('num', ''):<4} {f.get('odds_low', '-')}〜{f.get('odds_high', '-')}" if f else ""
            print(f"{t_str}  {f_str}")
    else:
        print("オッズ情報が取得できませんでした。")
    print()


def main():
    race_id = RACE_ID
    print(f"出走表を取得中... (race_id: {race_id})")

    try:
        race_info, horses = get_race_entry(race_id)
        print_entry(race_info, horses, race_id)
    except requests.RequestException as e:
        print(f"通信エラー: {e}")
        sys.exit(1)

    print(f"オッズを取得中... (race_id: {race_id})")
    try:
        odds_data = get_tansho_fukusho_odds(race_id)
        print_tansho_fukusho(odds_data, race_id)
    except requests.RequestException as e:
        print(f"通信エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
