#!/usr/bin/env python3
"""レース結果を取得する"""
import argparse
import sys
from _scraper import fetch, race_result_url


def get_race_result(race_id: str) -> tuple[dict, list[dict]]:
    """レース結果を取得する。(レース情報, 着順リスト) を返す"""
    url = race_result_url(race_id)
    soup = fetch(url)

    # レース情報
    race_info = {"race_id": race_id, "race_name": "", "details": ""}

    name_tag = soup.find(class_="RaceName") or soup.find("h1", class_="race_name")
    if name_tag:
        race_info["race_name"] = name_tag.get_text(strip=True)

    data_tag = soup.find(class_="RaceData01") or soup.find(class_="race_data")
    if data_tag:
        race_info["details"] = data_tag.get_text(" ", strip=True)

    # 結果テーブル
    results = []
    table = soup.find("table", class_="race_table_01")
    if not table:
        for t in soup.find_all("table"):
            ths = [th.get_text(strip=True) for th in t.find_all("th")]
            if "着順" in ths and "馬名" in ths:
                table = t
                break

    if not table:
        print(f"[警告] 結果テーブルが見つかりませんでした。URL: {url}", file=sys.stderr)
        return race_info, results

    # ヘッダー取得
    header_row = table.find("tr")
    headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])] if header_row else []

    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if not cells:
            continue

        texts = [c.get_text(strip=True) for c in cells]
        entry: dict = {}

        if headers:
            for i, h in enumerate(headers):
                if i < len(texts):
                    entry[h] = texts[i]
        else:
            # ヘッダーなしの場合は列位置から推定
            col_names = ["着順", "枠番", "馬番", "馬名", "性齢", "斤量", "騎手", "タイム", "着差", "単勝人気", "オッズ", "後3F", "コーナー通過", "調教師", "馬体重", "賞金"]
            for i, name in enumerate(col_names):
                if i < len(texts):
                    entry[name] = texts[i]

        # 馬IDをリンクから取得
        for cell in cells:
            a_tag = cell.find("a", href=lambda h: h and "/horse/" in h)
            if a_tag:
                href = a_tag["href"]
                horse_id = href.rstrip("/").split("/")[-1]
                entry["horse_id"] = horse_id
                break

        if entry:
            results.append(entry)

    return race_info, results


def main():
    parser = argparse.ArgumentParser(description="レース結果を取得")
    parser.add_argument("race_id", help="レースID（12桁）例: 202506010101")
    args = parser.parse_args()

    if len(args.race_id) != 12 or not args.race_id.isdigit():
        print("エラー: レースIDは12桁の数字です（例: 202506010101）", file=sys.stderr)
        sys.exit(1)

    race_info, results = get_race_result(args.race_id)

    if not results:
        print("レース結果が見つかりませんでした。")
        print(f"URL: https://db.netkeiba.com/race/{args.race_id}/")
        return

    print(f"\n【レース結果】{race_info['race_name']}")
    print(f"詳細: {race_info['details']}")
    print(f"レースID: {args.race_id}  出走頭数: {len(results)}頭\n")

    # 表示する主要カラム
    key_fields = ["着順", "枠番", "馬番", "馬名", "性齢", "斤量", "騎手", "タイム", "着差", "人気", "オッズ", "馬体重"]
    available = [f for f in key_fields if any(f in k for k in results[0].keys())]
    if not available:
        available = list(results[0].keys())[:8]

    header = " | ".join(f"{f:<10}" for f in available[:8])
    print(header)
    print("-" * len(header))

    for r in results:
        row_vals = []
        for f in available[:8]:
            val = r.get(f, "")
            if not val:
                for k in r:
                    if f in k:
                        val = r[k]
                        break
            row_vals.append(f"{val:<10}")
        print(" | ".join(row_vals))

    print(f"\n※ 馬の詳細: python3 scripts/get_horse_info.py <horse_id>")


if __name__ == "__main__":
    main()
