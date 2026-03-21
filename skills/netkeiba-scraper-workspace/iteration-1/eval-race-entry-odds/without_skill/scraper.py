#!/usr/bin/env python3
"""
Netkeiba scraper for race entry and odds information.
Race ID: 202506010111
Date: 2025-01-05
Venue: 中山競馬場 (Nakayama)
Race: 11R
"""

import requests
from bs4 import BeautifulSoup
import sys
import time

# Race ID breakdown: 202506010111
# 2025: Year
# 06: Venue code (中山=06)
# 01: Meet number
# 11: Race number

RACE_ID = "202506010111"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

def scrape_race_entry(race_id):
    """Scrape race entry (出走表) from netkeiba."""
    url = f"https://race.netkeiba.com/race/shutuba.html?race_id={race_id}"
    print(f"出走表URL: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        response.encoding = 'EUC-JP'
        print(f"出走表ページ取得成功 (Status: {response.status_code})")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract race info
        race_info = extract_race_info(soup)

        # Extract entries
        entries = extract_entries(soup)

        return race_info, entries

    except requests.exceptions.RequestException as e:
        print(f"出走表取得エラー: {e}")
        return None, []

def extract_race_info(soup):
    """Extract race information from the page."""
    info = {}

    # Race title/name
    title_elem = soup.find('div', class_='RaceName') or soup.find('h1', class_='RaceName')
    if title_elem:
        info['race_name'] = title_elem.get_text(strip=True)

    # Race data (date, venue, distance, etc.)
    race_data = soup.find('div', class_='RaceData01')
    if race_data:
        info['race_data'] = race_data.get_text(separator=' ', strip=True)

    race_data2 = soup.find('div', class_='RaceData02')
    if race_data2:
        info['race_data2'] = race_data2.get_text(separator=' ', strip=True)

    # Try alternate selectors
    if not info:
        race_header = soup.find('div', class_='RaceTableWrap') or soup.find('div', id='RaceList_ItemBox')
        if race_header:
            info['header'] = race_header.get_text(separator=' ', strip=True)[:200]

    return info

def extract_entries(soup):
    """Extract horse entries from the race page."""
    entries = []

    # Main table for shutuba (出走表)
    table = soup.find('table', class_='Shutuba_Table') or soup.find('table', id='shutuba_table')

    if not table:
        # Try other table selectors
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables on page")
        for i, t in enumerate(tables):
            classes = t.get('class', [])
            print(f"  Table {i}: classes={classes}, id={t.get('id', 'none')}")

        # Use first table with many rows
        for t in tables:
            rows = t.find_all('tr')
            if len(rows) > 5:
                table = t
                break

    if not table:
        print("出走表のテーブルが見つかりませんでした")
        return entries

    rows = table.find_all('tr')
    print(f"テーブル行数: {len(rows)}")

    for row in rows:
        cells = row.find_all(['td', 'th'])
        if not cells:
            continue

        # Skip header rows
        if row.find('th'):
            continue

        entry = {}

        # Try to extract horse number, horse name, jockey, weight
        cell_texts = [cell.get_text(strip=True) for cell in cells]

        if len(cell_texts) >= 3:
            entry['data'] = cell_texts

            # Look for horse number
            for i, text in enumerate(cell_texts):
                if text.isdigit() and int(text) <= 18:
                    entry['horse_number'] = text
                    break

            # Look for horse name (link)
            for cell in cells:
                horse_link = cell.find('a', href=lambda x: x and 'horse' in str(x).lower())
                if horse_link:
                    entry['horse_name'] = horse_link.get_text(strip=True)
                    break

            if entry:
                entries.append(entry)

    return entries

def scrape_race_entry_v2(race_id):
    """Alternative scraping using the DB version of netkeiba."""
    url = f"https://db.netkeiba.com/race/{race_id}/"
    print(f"\n代替URL (db.netkeiba.com): {url}")

    try:
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        # Try different encodings
        for encoding in ['EUC-JP', 'utf-8', 'Shift_JIS']:
            try:
                response.encoding = encoding
                content = response.text
                if '出走' in content or '競馬' in content or '馬' in content:
                    print(f"エンコーディング {encoding} で日本語テキスト確認")
                    break
            except Exception:
                continue

        print(f"db.netkeiba.com ページ取得成功 (Status: {response.status_code})")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract race info
        race_name = ""
        for selector in ['h1.RaceName', '.RaceName', 'h1', '.race_name']:
            elem = soup.select_one(selector)
            if elem:
                race_name = elem.get_text(strip=True)
                break

        print(f"\nレース名: {race_name}")

        # Find the race result/entry table
        table = None
        for t in soup.find_all('table'):
            headers = [th.get_text(strip=True) for th in t.find_all('th')]
            if any(h in ['馬名', '馬番', '枠番'] for h in headers):
                table = t
                print(f"出走表テーブル発見 (headers: {headers[:5]})")
                break

        entries = []
        if table:
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            print(f"カラム: {headers}")

            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = row.find_all(['td', 'th'])
                if not cells:
                    continue

                cell_data = [cell.get_text(strip=True) for cell in cells]
                if cell_data:
                    entry = dict(zip(headers, cell_data)) if headers else {'data': cell_data}

                    # Get horse link
                    for cell in cells:
                        link = cell.find('a', href=lambda x: x and '/horse/' in str(x))
                        if link:
                            entry['horse_link'] = link.get('href', '')
                            break

                    entries.append(entry)

        return race_name, entries, soup

    except requests.exceptions.RequestException as e:
        print(f"db.netkeiba.com 取得エラー: {e}")
        return "", [], None

def scrape_odds(race_id, session=None):
    """Scrape odds for the race."""
    # Try win odds (単勝オッズ)
    odds_url = f"https://race.netkeiba.com/odds/index.html?race_id={race_id}&type=b1"
    print(f"\n単勝オッズURL: {odds_url}")

    if session is None:
        session = requests.Session()

    try:
        response = session.get(odds_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        response.encoding = 'EUC-JP'
        print(f"オッズページ取得成功 (Status: {response.status_code})")

        soup = BeautifulSoup(response.text, 'html.parser')

        odds_data = []

        # Find odds table
        odds_table = soup.find('table', id='Odds_Tanpuku_Table') or \
                     soup.find('table', class_='Odds_Table') or \
                     soup.find('div', id='odds_tan_block')

        if not odds_table:
            # Search all tables
            for table in soup.find_all('table'):
                headers = [th.get_text(strip=True) for th in table.find_all('th')]
                if any(h in ['単勝', 'オッズ', '馬名'] for h in headers):
                    odds_table = table
                    print(f"オッズテーブル発見: {headers[:5]}")
                    break

        if odds_table:
            rows = odds_table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if not cells:
                    continue
                cell_texts = [c.get_text(strip=True) for c in cells]
                if cell_texts and any(c.replace('.', '').isdigit() for c in cell_texts):
                    odds_data.append(cell_texts)

        return odds_data

    except requests.exceptions.RequestException as e:
        print(f"オッズ取得エラー: {e}")
        return []

def scrape_shutuba_table(race_id):
    """Scrape from shutuba_table endpoint."""
    url = f"https://race.netkeiba.com/race/shutuba_table.html?race_id={race_id}&rf=race_submenu"
    print(f"\n出走表テーブルURL: {url}")

    session = requests.Session()

    try:
        response = session.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        response.encoding = 'EUC-JP'
        print(f"Status: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Print page title
        title = soup.find('title')
        if title:
            print(f"ページタイトル: {title.get_text()}")

        return soup, session

    except requests.exceptions.RequestException as e:
        print(f"エラー: {e}")
        return None, session

def main():
    race_id = RACE_ID
    print("=" * 60)
    print(f"ネット競馬 出走表・オッズ調査")
    print(f"Race ID: {race_id}")
    print(f"開催日: 2025年1月5日")
    print(f"競馬場: 中山競馬場")
    print(f"レース: 第11レース")
    print("=" * 60)

    all_output = []

    # Method 1: Try race.netkeiba.com shutuba
    print("\n【方法1】race.netkeiba.com から出走表取得")
    race_info, entries = scrape_race_entry(race_id)

    if race_info:
        print(f"\nレース情報: {race_info}")
        all_output.append(f"レース情報: {race_info}")

    if entries:
        print(f"\n出走馬 ({len(entries)}頭):")
        for e in entries[:18]:
            print(f"  {e}")
    else:
        print("出走表データが取得できませんでした")

    time.sleep(1)

    # Method 2: Try db.netkeiba.com
    print("\n【方法2】db.netkeiba.com から出走表取得")
    race_name, db_entries, db_soup = scrape_race_entry_v2(race_id)

    if db_entries:
        print(f"\n出走馬 ({len(db_entries)}頭):")
        for e in db_entries[:18]:
            print(f"  {e}")

    time.sleep(1)

    # Method 3: Try odds page
    print("\n【方法3】オッズ取得")
    odds = scrape_odds(race_id)
    if odds:
        print(f"\n単勝オッズ データ ({len(odds)}行):")
        for row in odds[:20]:
            print(f"  {row}")

    time.sleep(1)

    # Method 4: shutuba_table
    print("\n【方法4】出走表テーブル取得")
    shutuba_soup, session = scrape_shutuba_table(race_id)

    if shutuba_soup:
        # Extract all tables info
        tables = shutuba_soup.find_all('table')
        print(f"テーブル数: {len(tables)}")

        for i, t in enumerate(tables):
            classes = t.get('class', [])
            table_id = t.get('id', '')
            rows = t.find_all('tr')
            print(f"  Table[{i}]: id='{table_id}', classes={classes}, rows={len(rows)}")

            if len(rows) > 3:
                # Try to extract this table
                headers = [th.get_text(strip=True) for th in t.find_all('th')]
                print(f"    Headers: {headers[:8]}")

                for row in t.find_all('tr')[1:]:
                    cells = row.find_all(['td'])
                    if cells:
                        cell_texts = [c.get_text(strip=True) for c in cells[:10]]
                        if any(cell_texts):
                            print(f"    Row: {cell_texts}")

    # Additional: try to get page source structure
    print("\n【デバッグ】ページ構造確認")
    debug_url = f"https://race.netkeiba.com/race/shutuba.html?race_id={race_id}"
    try:
        resp = requests.get(debug_url, headers=HEADERS, timeout=30)
        resp.encoding = 'EUC-JP'
        soup_debug = BeautifulSoup(resp.text, 'html.parser')

        # Find all divs with class containing 'Race'
        race_divs = soup_debug.find_all(True, class_=lambda x: x and any('Race' in c or 'race' in c for c in x))
        print(f"Race関連要素数: {len(race_divs)}")
        for div in race_divs[:5]:
            tag = div.name
            classes = div.get('class', [])
            text = div.get_text(strip=True)[:80]
            print(f"  <{tag} class='{' '.join(classes)}'> {text}")

        # Check body content
        body = soup_debug.find('body')
        if body:
            body_text = body.get_text(separator='\n', strip=True)
            # Check if we got actual content or redirected
            if len(body_text) < 100:
                print(f"ページコンテンツが少ない (body text length: {len(body_text)})")
                print(f"Body text: {body_text}")
            else:
                print(f"ページコンテンツ取得確認 (body text length: {len(body_text)})")
                # Print first 500 chars
                print(f"最初の内容:\n{body_text[:500]}")

    except Exception as e:
        print(f"デバッグ取得エラー: {e}")

if __name__ == "__main__":
    main()
