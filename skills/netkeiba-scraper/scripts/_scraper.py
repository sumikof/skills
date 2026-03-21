"""netkeibaスクレイピング共通ユーティリティ"""
import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://db.netkeiba.com"
RACE_URL = "https://race.netkeiba.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.netkeiba.com/",
}

VENUE_CODES = {
    "01": "札幌", "02": "函館", "03": "福島", "04": "新潟",
    "05": "東京", "06": "中山", "07": "中京", "08": "京都",
    "09": "阪神", "10": "小倉",
}


def fetch(url: str, interval: float = 1.0) -> BeautifulSoup:
    """URLをフェッチしてBeautifulSoupオブジェクトを返す"""
    time.sleep(interval)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding
    return BeautifulSoup(resp.text, "lxml")


def horse_url(horse_id: str) -> str:
    return f"{BASE_URL}/horse/{horse_id}/"


def horse_result_url(horse_id: str) -> str:
    return f"{BASE_URL}/horse/result/{horse_id}/"


def race_entry_url(race_id: str) -> str:
    return f"{RACE_URL}/race/shutuba.html?race_id={race_id}"


def race_result_url(race_id: str) -> str:
    return f"{BASE_URL}/race/{race_id}/"


def race_list_url(date: str, venue: str = "") -> str:
    """開催レース一覧のURL（date: YYYYMMDD形式）"""
    url = f"{RACE_URL}/top/race_list.html?kaisai_date={date}"
    if venue:
        url += f"&kaisai_id={venue}"
    return url
