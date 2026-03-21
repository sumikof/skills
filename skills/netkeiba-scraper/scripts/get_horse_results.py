#!/usr/bin/env python3
"""馬の過去成績を取得する"""
import argparse
import csv
import sys
from _scraper import fetch, horse_result_url, horse_url


def get_horse_results(horse_id: str, last: int = 0) -> tuple[str, list[dict]]:
    """馬の過去成績を取得する。(馬名, 成績リスト) を返す"""
    # 馬名を取得
    horse_name = horse_id
    try:
        info_soup = fetch(horse_url(horse_id))
        title_tag = info_soup.find(class_="horse_title") or info_soup.find(class_="HorseName")
        if title_tag:
            h1 = title_tag.find("h1")
            if h1:
                horse_name = h1.get_text(strip=True)
    except Exception:
        pass

    url = horse_result_url(horse_id)
    soup = fetch(url)

    results = []

    table = soup.find("table", class_="db_h_race_results")
    if not table:
        for t in soup.find_all("table"):
            headers = [th.get_text(strip=True) for th in t.find_all("th")]
            if "日付" in headers and "着順" in headers:
                table = t
                break

    if not table:
        print(f"[警告] 成績テーブルが見つかりませんでした。URL: {url}", file=sys.stderr)
        return horse_name, results

    # ヘッダー取得
    header_row = table.find("tr")
    if not header_row:
        return horse_name, results
    headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

    rows = table.find_all("tr")[1:]
    if last > 0:
        rows = rows[-last:]  # 直近N戦

    for row in rows:
        cells = row.find_all("td")
        if not cells:
            continue

        texts = [c.get_text(strip=True) for c in cells]
        entry: dict = {}

        for i, h in enumerate(headers):
            if i < len(texts):
                entry[h] = texts[i]

        # レースIDを取得
        for cell in cells:
            a_tag = cell.find("a", href=lambda h: h and "/race/" in h)
            if a_tag:
                href = a_tag["href"]
                race_id = href.rstrip("/").split("/")[-1]
                if race_id.isdigit() and len(race_id) == 12:
                    entry["race_id"] = race_id
                break

        if entry:
            results.append(entry)

    return horse_name, results


def main():
    parser = argparse.ArgumentParser(description="馬の過去成績を取得")
    parser.add_argument("horse_id", help="馬ID（10桁）例: 2020104308")
    parser.add_argument("--last", type=int, default=0, help="直近N戦を表示（デフォルト: 全件）")
    parser.add_argument("--output", help="CSV保存先ファイル名（例: results.csv）")
    args = parser.parse_args()

    horse_name, results = get_horse_results(args.horse_id, args.last)

    if not results:
        print(f"成績が見つかりませんでした。")
        print(f"URL: https://db.netkeiba.com/horse/result/{args.horse_id}/")
        return

    label = f"直近{args.last}戦" if args.last > 0 else f"全{len(results)}戦"
    print(f"\n【{horse_name}】の過去成績（{label}）")
    print(f"馬ID: {args.horse_id}\n")

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)
        print(f"CSVを保存しました: {args.output}")
        return

    # テーブル表示（主要項目のみ）
    key_fields = ["日付", "開催", "レース名", "距離", "頭数", "枠番", "馬番", "オッズ", "人気", "着順", "騎手", "タイム", "着差", "賞金"]
    available = [f for f in key_fields if any(f in k for k in results[0].keys())]
    if not available:
        available = list(results[0].keys())[:10]

    # ヘッダー出力
    header = " | ".join(f"{f:<10}" for f in available[:8])
    print(header)
    print("-" * len(header))

    for r in results:
        row_values = []
        for f in available[:8]:
            # キーが完全一致しない場合は部分一致で探す
            val = r.get(f, "")
            if not val:
                for k in r:
                    if f in k:
                        val = r[k]
                        break
            row_values.append(f"{val:<10}")
        print(" | ".join(row_values))


if __name__ == "__main__":
    main()
