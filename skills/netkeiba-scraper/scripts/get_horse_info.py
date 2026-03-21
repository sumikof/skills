#!/usr/bin/env python3
"""馬の基本情報・血統を取得する"""
import argparse
import sys
from _scraper import fetch, horse_url


def get_horse_info(horse_id: str, show_pedigree: bool = False) -> dict:
    """馬の基本情報を取得する"""
    url = horse_url(horse_id)
    soup = fetch(url)

    info = {
        "horse_id": horse_id,
        "馬名": "",
        "英名": "",
        "生年月日": "",
        "性別": "",
        "毛色": "",
        "父": "",
        "母": "",
        "母の父": "",
        "生産者": "",
        "産地": "",
        "馬主": "",
        "調教師": "",
        "調教場": "",
        "募集情報": "",
        "獲得賞金": "",
    }

    # 馬名
    horse_title = soup.find(class_="horse_title")
    if not horse_title:
        horse_title = soup.find("div", class_="HorseName")
    if horse_title:
        h1 = horse_title.find("h1")
        if h1:
            info["馬名"] = h1.get_text(strip=True)
        else:
            info["馬名"] = horse_title.get_text(strip=True).split("\n")[0]

    # プロフィールテーブル
    prof_table = soup.find("table", class_="db_prof_table")
    if not prof_table:
        prof_table = soup.find("div", class_="horse_data")

    if prof_table:
        for row in prof_table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue
            key = th.get_text(strip=True)
            value = td.get_text(" ", strip=True)

            mapping = {
                "生年月日": "生年月日",
                "英字名": "英名",
                "性別": "性別",
                "毛色": "毛色",
                "生産者": "生産者",
                "産地": "産地",
                "馬主": "馬主",
                "調教師": "調教師",
                "トレーニングセンター": "調教場",
                "獲得賞金": "獲得賞金",
            }
            for k, v in mapping.items():
                if k in key:
                    info[v] = value
                    break

    # 血統テーブル
    pedigree_table = soup.find("table", class_="blood_table")
    if not pedigree_table:
        pedigree_table = soup.find("table", id="pedigree_table")

    if pedigree_table:
        cells = pedigree_table.find_all("td")
        if len(cells) >= 1:
            info["父"] = cells[0].get_text(strip=True) if len(cells) > 0 else ""
        # 父・母は最初の2つの祖先セル
        links = pedigree_table.find_all("a")
        if len(links) >= 2:
            info["父"] = links[0].get_text(strip=True)
            info["母"] = links[1].get_text(strip=True)
        if len(links) >= 4:
            info["母の父"] = links[3].get_text(strip=True)

    return info


def main():
    parser = argparse.ArgumentParser(description="馬の基本情報を取得")
    parser.add_argument("horse_id", help="馬ID（10桁）例: 2020104308")
    parser.add_argument("--pedigree", action="store_true", help="血統情報を含めて表示")
    args = parser.parse_args()

    info = get_horse_info(args.horse_id, args.pedigree)

    print(f"\n【馬情報】 {info['馬名']}")
    if info["英名"]:
        print(f"英名: {info['英名']}")
    print(f"馬ID: {args.horse_id}")
    print(f"URL : https://db.netkeiba.com/horse/{args.horse_id}/")
    print()

    fields = ["生年月日", "性別", "毛色", "調教師", "調教場", "馬主", "生産者", "産地", "獲得賞金"]
    for f in fields:
        if info[f]:
            print(f"{f}: {info[f]}")

    if args.pedigree or (info["父"] or info["母"]):
        print("\n【血統】")
        if info["父"]:
            print(f"父    : {info['父']}")
        if info["母"]:
            print(f"母    : {info['母']}")
        if info["母の父"]:
            print(f"母の父: {info['母の父']}")

    print(f"\n※ 過去成績: python3 scripts/get_horse_results.py {args.horse_id}")


if __name__ == "__main__":
    main()
