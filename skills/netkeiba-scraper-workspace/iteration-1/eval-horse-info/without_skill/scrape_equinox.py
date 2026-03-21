#!/usr/bin/env python3
"""
イクイノックスの競走馬情報と過去成績をnetkeibaから取得するスクリプト
"""

import requests
from bs4 import BeautifulSoup
import time
import re
import sys

# netkeibaでのイクイノックスの馬ID
# イクイノックス (Equinox) - 2019年生まれ、キタサンブラック産駒
HORSE_ID = "2019105521"

BASE_URL = "https://db.netkeiba.com"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

def fetch_page(url):
    """ページを取得する"""
    print(f"\n[取得中] {url}")
    response = requests.get(url, headers=headers, timeout=30)
    response.encoding = "EUC-JP"
    if response.status_code != 200:
        print(f"エラー: ステータスコード {response.status_code}")
        return None
    return response.text

def search_horse():
    """イクイノックスを検索する"""
    search_url = f"{BASE_URL}/horse/search/?name=%83C%83N%83C%83m%83b%83N%83X"
    html = fetch_page(search_url)
    if not html:
        # 直接URLでアクセス
        return None

    soup = BeautifulSoup(html, "lxml")

    # 検索結果から馬を探す
    results = []
    table = soup.find("table", class_="horse_table")
    if table:
        rows = table.find_all("tr")[1:]  # ヘッダーをスキップ
        for row in rows:
            cols = row.find_all("td")
            if cols:
                horse_link = row.find("a", href=re.compile(r"/horse/\d+"))
                if horse_link:
                    horse_name = horse_link.text.strip()
                    horse_href = horse_link["href"]
                    horse_id = re.search(r"/horse/(\d+)", horse_href)
                    if horse_id:
                        results.append({
                            "name": horse_name,
                            "id": horse_id.group(1),
                            "url": BASE_URL + horse_href
                        })
                        print(f"  見つかりました: {horse_name} (ID: {horse_id.group(1)})")

    return results

def get_horse_info(horse_id):
    """馬の基本情報を取得する"""
    url = f"{BASE_URL}/horse/{horse_id}/"
    html = fetch_page(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "lxml")

    info = {}

    # 馬名
    horse_title = soup.find("div", class_="horse_title")
    if horse_title:
        horse_name = horse_title.find("h1")
        if horse_name:
            info["馬名"] = horse_name.text.strip()
        # 英語名
        horse_name_en = horse_title.find("p", class_="eng_name")
        if horse_name_en:
            info["英語名"] = horse_name_en.text.strip()

    # プロフィールテーブル
    profile_table = soup.find("table", class_="horse_info")
    if profile_table:
        rows = profile_table.find_all("tr")
        for row in rows:
            th = row.find("th")
            td = row.find("td")
            if th and td:
                key = th.text.strip()
                value = td.text.strip()
                info[key] = value

    # 成績サマリー
    career_record = soup.find("p", class_="txt_01")
    if career_record:
        info["通算成績"] = career_record.text.strip()

    # 獲得賞金
    money_table = soup.find("div", class_="race_money")
    if money_table:
        info["獲得賞金"] = money_table.text.strip()

    return info, html, soup

def get_race_results(soup, horse_id):
    """過去レース成績を取得する"""
    results = []

    # レース結果テーブルを探す
    race_table = soup.find("table", class_="race_table_01")
    if not race_table:
        race_table = soup.find("table", summary="過去成績")
    if not race_table:
        # クラスなしでテーブルを探す
        tables = soup.find_all("table")
        for t in tables:
            headers = t.find_all("th")
            header_texts = [h.text.strip() for h in headers]
            if "着順" in header_texts or "レース名" in header_texts:
                race_table = t
                break

    if race_table:
        rows = race_table.find_all("tr")
        if rows:
            # ヘッダー行を取得
            header_row = rows[0]
            headers = [th.text.strip() for th in header_row.find_all("th")]
            if not headers:
                headers = [td.text.strip() for td in header_row.find_all("td")]

            print(f"\n  レース結果テーブルのヘッダー: {headers}")

            # データ行を取得
            for row in rows[1:]:
                cols = row.find_all("td")
                if cols:
                    row_data = {}
                    for i, col in enumerate(cols):
                        if i < len(headers):
                            row_data[headers[i]] = col.text.strip()
                        else:
                            row_data[f"col_{i}"] = col.text.strip()
                    results.append(row_data)

    return results

def format_output(horse_info, race_results):
    """出力フォーマットを整形する"""
    output = []
    output.append("=" * 60)
    output.append("イクイノックス (Equinox) 競走馬情報")
    output.append("=" * 60)

    if horse_info:
        output.append("\n【基本情報】")
        for key, value in horse_info.items():
            output.append(f"  {key}: {value}")

    output.append("\n" + "=" * 60)
    output.append("【過去成績】")
    output.append("=" * 60)

    if race_results:
        output.append(f"\n総レース数: {len(race_results)} レース")
        output.append("")

        for i, race in enumerate(race_results, 1):
            output.append(f"\n--- レース {i} ---")
            for key, value in race.items():
                if value:  # 空でない場合のみ表示
                    output.append(f"  {key}: {value}")
    else:
        output.append("\n成績データが見つかりませんでした。")

    return "\n".join(output)

def main():
    output_lines = []

    def log(msg):
        print(msg)
        output_lines.append(msg)

    log("=" * 60)
    log("イクイノックス (Equinox) netkeibaスクレイピング")
    log("=" * 60)
    log(f"\n対象馬ID: {HORSE_ID}")
    log(f"データソース: {BASE_URL}")

    # 馬情報ページにアクセス
    log("\n[1] 馬の基本情報を取得中...")
    result = get_horse_info(HORSE_ID)

    if result is None:
        log("エラー: 馬情報の取得に失敗しました")
        sys.exit(1)

    horse_info, html, soup = result

    if horse_info:
        log("\n【基本情報】")
        for key, value in horse_info.items():
            log(f"  {key}: {value}")
    else:
        log("基本情報が見つかりませんでした")

    time.sleep(1)

    # 過去成績を取得
    log("\n[2] 過去レース成績を取得中...")
    race_results = get_race_results(soup, HORSE_ID)

    log("\n" + "=" * 60)
    log("【過去成績】")
    log("=" * 60)

    if race_results:
        log(f"\n総レース数: {len(race_results)} レース")

        for i, race in enumerate(race_results, 1):
            log(f"\n--- レース {i} ---")
            for key, value in race.items():
                if value:
                    log(f"  {key}: {value}")
    else:
        log("成績データが見つかりませんでした。")

        # HTMLを詳しく調べる
        log("\n[デバッグ] ページのテーブル情報:")
        tables = soup.find_all("table")
        log(f"  テーブル数: {len(tables)}")
        for i, t in enumerate(tables):
            classes = t.get("class", [])
            summary = t.get("summary", "")
            log(f"  テーブル{i+1}: class={classes}, summary={summary}")

    log("\n" + "=" * 60)
    log("スクレイピング完了")
    log("=" * 60)

    # 出力をファイルに保存
    output_path = "/home/user/skills/skills/netkeiba-scraper-workspace/iteration-1/eval-horse-info/without_skill/outputs/output.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"\n出力ファイル保存完了: {output_path}")

if __name__ == "__main__":
    main()
