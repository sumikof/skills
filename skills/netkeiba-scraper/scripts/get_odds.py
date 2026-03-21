#!/usr/bin/env python3
"""
netkeibaからオッズを取得する。
使用例:
  python3 get_odds.py 202501010101                       # 単勝・複勝
  python3 get_odds.py 202501010101 --type umaren         # 馬連
  python3 get_odds.py 202501010101 --type sanrenpuku     # 3連複
  python3 get_odds.py 202501010101 --type all            # 全馬券種
"""

import sys
import json
import argparse
import time
import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# 馬券種別とAPIパラメータのマッピング
ODDS_TYPES = {
    "tansho":    {"label": "単勝",  "type_param": "b1"},
    "fukusho":   {"label": "複勝",  "type_param": "b3"},
    "umaren":    {"label": "馬連",  "type_param": "b4"},
    "wide":      {"label": "ワイド", "type_param": "b5"},
    "umatan":    {"label": "馬単",  "type_param": "b6"},
    "sanrenpuku":{"label": "3連複", "type_param": "b7"},
    "sanrentan": {"label": "3連単", "type_param": "b8"},
}


def fetch_tansho_fukusho(race_id: str) -> dict:
    """単勝・複勝オッズをAPIから取得"""
    url = f"https://race.netkeiba.com/api/api_get_jra_odds.html?race_id={race_id}&type=b1&action=update"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    resp.encoding = "UTF-8"

    data = {"tansho": [], "fukusho": []}

    try:
        json_data = resp.json()
        odds_data = json_data.get("data", {}).get("odds", {})

        # 単勝オッズ (b1)
        for num, val in odds_data.get("1", {}).items():
            if isinstance(val, list) and len(val) >= 1:
                data["tansho"].append({"num": num, "odds": val[0]})
            elif isinstance(val, str):
                data["tansho"].append({"num": num, "odds": val})

        # 複勝オッズ (b3)
        for num, val in odds_data.get("3", {}).items():
            if isinstance(val, list) and len(val) >= 2:
                data["fukusho"].append({"num": num, "odds_low": val[0], "odds_high": val[1]})
            elif isinstance(val, str):
                data["fukusho"].append({"num": num, "odds_low": val, "odds_high": val})

    except (json.JSONDecodeError, KeyError, TypeError):
        # HTMLページからフォールバック
        data = fetch_odds_html(race_id, "b1")

    return data


def fetch_odds_html(race_id: str, type_param: str) -> dict:
    """HTMLページからオッズをスクレイピング"""
    url = f"https://race.netkeiba.com/odds/index.html?race_id={race_id}&type={type_param}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    resp.encoding = "EUC-JP"

    soup = BeautifulSoup(resp.text, "lxml")
    result = {"html_data": []}

    table = soup.select_one("#odds_tan_fuku_block, .OddsTable, table[id*='odds']")
    if table:
        for row in table.select("tr"):
            cells = row.find_all(["td", "th"])
            if cells:
                row_data = [c.get_text(strip=True) for c in cells]
                result["html_data"].append(row_data)

    return result


def fetch_combined_odds(race_id: str, type_param: str) -> list[list]:
    """馬連・馬単・3連複・3連単などの組み合わせオッズを取得"""
    url = f"https://race.netkeiba.com/api/api_get_jra_odds.html?race_id={race_id}&type={type_param}&action=update"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        json_data = resp.json()
        odds_raw = json_data.get("data", {}).get("odds", {})

        rows = []
        # type_param から数字を抽出
        type_num = type_param.replace("b", "")
        type_odds = odds_raw.get(type_num, {})

        for key, val in type_odds.items():
            odds_val = val[0] if isinstance(val, list) else str(val)
            nums = key.split("_")
            rows.append(nums + [odds_val])

        # オッズ順にソート（数値変換できないものは末尾へ）
        def odds_key(r):
            try:
                return float(r[-1])
            except (ValueError, IndexError):
                return 9999

        rows.sort(key=odds_key)
        return rows

    except (requests.RequestException, json.JSONDecodeError, KeyError):
        return []


def print_tansho_fukusho(race_id: str):
    data = fetch_tansho_fukusho(race_id)

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
    elif "html_data" in data:
        for row in data["html_data"][:20]:
            print("  ".join(row))
    else:
        print("オッズ情報が取得できませんでした。")

    print()


def print_combined(race_id: str, odds_type: str):
    config = ODDS_TYPES[odds_type]
    rows = fetch_combined_odds(race_id, config["type_param"])

    print(f"\n=== {config['label']}オッズ [{race_id}] ===\n")

    if not rows:
        print("オッズ情報が取得できませんでした。")
        print()
        return

    # 上位20件を表示
    display_rows = rows[:20]
    type_label = config["label"]

    if odds_type in ("umaren", "wide", "umatan"):
        print(f"{'1頭目':<6} {'2頭目':<6} オッズ")
        print("-" * 25)
        for r in display_rows:
            if len(r) >= 3:
                print(f"{r[0]:<6} {r[1]:<6} {r[2]}")
    elif odds_type in ("sanrenpuku", "sanrentan"):
        print(f"{'1頭目':<6} {'2頭目':<6} {'3頭目':<6} オッズ")
        print("-" * 30)
        for r in display_rows:
            if len(r) >= 4:
                print(f"{r[0]:<6} {r[1]:<6} {r[2]:<6} {r[3]}")

    if len(rows) > 20:
        print(f"  ... 他 {len(rows) - 20} 通り (オッズ上位20件を表示)")
    print()


def main():
    parser = argparse.ArgumentParser(description="netkeibaからオッズを取得")
    parser.add_argument("race_id", help="レースID (12桁、例: 202501010101)")
    parser.add_argument(
        "--type",
        default="tansho",
        choices=list(ODDS_TYPES.keys()) + ["all"],
        help="馬券種別 (デフォルト: tansho 単勝・複勝も同時表示)"
    )
    args = parser.parse_args()

    race_id = args.race_id.strip()
    if len(race_id) != 12 or not race_id.isdigit():
        print(f"エラー: レースIDは12桁の数字です (例: 202501010101)")
        sys.exit(1)

    print(f"オッズを取得中... (race_id: {race_id})")

    try:
        if args.type in ("tansho", "fukusho"):
            print_tansho_fukusho(race_id)
        elif args.type == "all":
            print_tansho_fukusho(race_id)
            for t in ["umaren", "wide", "umatan", "sanrenpuku"]:
                time.sleep(1)
                print_combined(race_id, t)
        else:
            print_combined(race_id, args.type)

    except requests.RequestException as e:
        print(f"通信エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
