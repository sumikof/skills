#!/usr/bin/env python3
"""特定日の開催レース一覧を取得する"""
import argparse
import sys
from _scraper import fetch, race_list_url, VENUE_CODES


def get_race_list(date: str, venue: str = "") -> list[dict]:
    """開催レース一覧を取得する"""
    url = race_list_url(date, venue)
    soup = fetch(url)

    races = []
    # レース一覧テーブルを探す
    race_list_box = soup.find("div", class_="RaceList_Box")
    if not race_list_box:
        # 旧レイアウトも試みる
        race_list_box = soup.find("div", id="race_list_box")

    if not race_list_box:
        print(f"[警告] レース一覧が見つかりませんでした。URL: {url}", file=sys.stderr)
        return races

    for item in race_list_box.find_all("li", class_=["RaceList_DataItem", "race_list_data"]):
        a_tag = item.find("a")
        if not a_tag:
            continue
        href = a_tag.get("href", "")
        # race_id を href から抽出
        race_id = ""
        if "race_id=" in href:
            race_id = href.split("race_id=")[-1].split("&")[0]
        elif "/race/" in href:
            race_id = href.rstrip("/").split("/")[-1]

        race_info = {
            "race_id": race_id,
            "race_name": "",
            "race_number": "",
            "venue": "",
            "distance": "",
            "condition": "",
        }

        # レース番号
        num_tag = item.find(class_=["RaceList_Num", "race_num"])
        if num_tag:
            race_info["race_number"] = num_tag.get_text(strip=True)

        # レース名
        name_tag = item.find(class_=["RaceList_ItemTitle", "race_name"])
        if not name_tag:
            name_tag = item.find("span", class_="RaceName")
        if name_tag:
            race_info["race_name"] = name_tag.get_text(strip=True)

        # 会場・距離・条件
        detail_tag = item.find(class_=["RaceList_Detail", "race_detail"])
        if detail_tag:
            detail_text = detail_tag.get_text(" ", strip=True)
            race_info["condition"] = detail_text

        races.append(race_info)

    return races


def main():
    parser = argparse.ArgumentParser(description="特定日の開催レース一覧を取得")
    parser.add_argument("date", help="日付（YYYYMMDD形式）例: 20250601")
    parser.add_argument("--venue", default="", help="競馬場コード（例: 05=東京）")
    args = parser.parse_args()

    if len(args.date) != 8 or not args.date.isdigit():
        print("エラー: 日付はYYYYMMDD形式で指定してください（例: 20250601）", file=sys.stderr)
        sys.exit(1)

    print(f"\n開催レース一覧: {args.date[:4]}年{args.date[4:6]}月{args.date[6:8]}日")
    if args.venue:
        venue_name = VENUE_CODES.get(args.venue, args.venue)
        print(f"競馬場フィルタ: {venue_name}（コード: {args.venue}）")

    races = get_race_list(args.date, args.venue)

    if not races:
        print("レースが見つかりませんでした。")
        print("\n[ヒント] レースIDを直接確認するには、netkeibaのレースページURLから取得してください。")
        print("例: https://race.netkeiba.com/race/shutuba.html?race_id=202506010101")
        return

    print(f"\n合計: {len(races)}レース\n")
    print(f"{'レースID':<15} {'R':<4} {'レース名':<30} {'条件'}")
    print("-" * 70)
    for r in races:
        print(f"{r['race_id']:<15} {r['race_number']:<4} {r['race_name']:<30} {r['condition']}")


if __name__ == "__main__":
    main()
