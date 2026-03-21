#!/usr/bin/env python3
"""レースの出走表を取得する"""
import argparse
import csv
import sys
from _scraper import fetch, race_entry_url


def get_race_entry(race_id: str) -> tuple[dict, list[dict]]:
    """出走表を取得する。(レース情報, 出走馬リスト) を返す"""
    url = race_entry_url(race_id)
    soup = fetch(url)

    # レース情報を取得
    race_info = {"race_id": race_id, "race_name": "", "details": ""}

    race_name_tag = soup.find(class_="RaceName")
    if race_name_tag:
        race_info["race_name"] = race_name_tag.get_text(strip=True)

    race_data_tag = soup.find(class_="RaceData01")
    if race_data_tag:
        race_info["details"] = race_data_tag.get_text(" ", strip=True)

    # 出走表テーブルを取得
    entries = []
    table = soup.find("table", class_="Shutuba_Table")
    if not table:
        table = soup.find("table", id="shutuba_table")
    if not table:
        # 他のテーブルを探す
        for t in soup.find_all("table"):
            if t.find("th", string=lambda x: x and "馬名" in x):
                table = t
                break

    if not table:
        print(f"[警告] 出走表が見つかりませんでした。URL: {url}", file=sys.stderr)
        return race_info, entries

    rows = table.find_all("tr")
    for row in rows[1:]:  # ヘッダーをスキップ
        cells = row.find_all(["td", "th"])
        if len(cells) < 5:
            continue

        texts = [c.get_text(strip=True) for c in cells]

        # 馬名・馬IDを取得
        horse_name = ""
        horse_id = ""
        for cell in cells:
            a_tag = cell.find("a", href=lambda h: h and "/horse/" in h)
            if a_tag:
                horse_name = a_tag.get_text(strip=True)
                href = a_tag["href"]
                horse_id = href.rstrip("/").split("/")[-1]
                break

        if not horse_name:
            continue

        # 騎手IDを取得
        jockey_name = ""
        jockey_id = ""
        for cell in cells:
            a_tag = cell.find("a", href=lambda h: h and "/jockey/" in h)
            if a_tag:
                jockey_name = a_tag.get_text(strip=True)
                href = a_tag["href"]
                jockey_id = href.rstrip("/").split("/")[-1]
                break

        # テキストベースで各列を取得（列数によって柔軟に）
        entry = {
            "枠番": texts[0] if len(texts) > 0 else "",
            "馬番": texts[1] if len(texts) > 1 else "",
            "馬名": horse_name,
            "horse_id": horse_id,
            "性齢": "",
            "斤量": "",
            "騎手": jockey_name,
            "jockey_id": jockey_id,
            "調教師": "",
            "馬体重": "",
            "単勝オッズ": "",
        }

        # 性齢・斤量・調教師・馬体重・オッズを列から探す
        for i, cell in enumerate(cells):
            text = cell.get_text(strip=True)
            cls = " ".join(cell.get("class", []))
            if "Sex" in cls or "Barei" in cls:
                entry["性齢"] = text
            elif "Jockey" in cls and "Weight" not in cls:
                if not entry["騎手"]:
                    entry["騎手"] = text
            elif "Weight" in cls and "Horse" not in cls:
                entry["斤量"] = text
            elif "Trainer" in cls:
                entry["調教師"] = text
            elif "HorseWeight" in cls or "Weight_Horses" in cls:
                entry["馬体重"] = text
            elif "Odds" in cls or "Popular" in cls:
                if not entry["単勝オッズ"]:
                    entry["単勝オッズ"] = text

        # フォールバック: 列位置から推定
        if len(texts) >= 10 and not entry["性齢"]:
            entry["性齢"] = texts[4] if len(texts) > 4 else ""
            entry["斤量"] = texts[5] if len(texts) > 5 else ""
            entry["調教師"] = texts[7] if len(texts) > 7 else ""
            entry["馬体重"] = texts[8] if len(texts) > 8 else ""

        entries.append(entry)

    return race_info, entries


def main():
    parser = argparse.ArgumentParser(description="レースの出走表を取得")
    parser.add_argument("race_id", help="レースID（12桁）例: 202506010101")
    parser.add_argument("--format", choices=["table", "csv"], default="table", help="出力形式")
    args = parser.parse_args()

    if len(args.race_id) != 12 or not args.race_id.isdigit():
        print("エラー: レースIDは12桁の数字です（例: 202506010101）", file=sys.stderr)
        sys.exit(1)

    race_info, entries = get_race_entry(args.race_id)

    if not entries:
        print("出走馬が見つかりませんでした。")
        print(f"URL: https://race.netkeiba.com/race/shutuba.html?race_id={args.race_id}")
        return

    print(f"\n{race_info['race_name']}  [{race_info['details']}]")
    print(f"レースID: {args.race_id}  出走頭数: {len(entries)}頭\n")

    if args.format == "csv":
        writer = csv.DictWriter(sys.stdout, fieldnames=list(entries[0].keys()))
        writer.writeheader()
        writer.writerows(entries)
    else:
        # テーブル表示
        print(f"{'枠':<3} {'馬番':<4} {'馬名':<16} {'性齢':<5} {'斤量':<5} {'騎手':<12} {'調教師':<10} {'馬体重':<8} {'オッズ'}")
        print("-" * 80)
        for e in entries:
            print(
                f"{e['枠番']:<3} {e['馬番']:<4} {e['馬名']:<16} {e['性齢']:<5} "
                f"{e['斤量']:<5} {e['騎手']:<12} {e['調教師']:<10} {e['馬体重']:<8} {e['単勝オッズ']}"
            )
        print(f"\n※ 馬の詳細: python3 scripts/get_horse_info.py <horse_id>")


if __name__ == "__main__":
    main()
