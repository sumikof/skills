"""
日銀APIを使ってFM08データベースのUSD関連系列を調査するスクリプト
API: https://www.stat-search.boj.or.jp/api/v1
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "https://www.stat-search.boj.or.jp/api/v1"

def log(msg):
    print(msg)
    sys.stdout.flush()

def get_metadata(db="FM08", keyword=None, lang="jp", fmt="json"):
    """メタデータAPIでFM08の系列情報を取得"""
    url = f"{BASE_URL}/getMetadata"
    params = {
        "db": db,
        "lang": lang,
        "format": fmt,
    }
    if keyword:
        params["keyword"] = keyword

    log(f"\n[API呼び出し] GET {url}")
    log(f"  パラメータ: {params}")

    resp = requests.get(url, params=params, timeout=30)
    log(f"  ステータス: {resp.status_code}")
    return resp

def get_data_code(db="FM08", lang="jp", fmt="json"):
    """コードAPIでFM08の系列コード一覧を取得"""
    url = f"{BASE_URL}/getDataCode"
    params = {
        "db": db,
        "lang": lang,
        "format": fmt,
    }

    log(f"\n[API呼び出し] GET {url}")
    log(f"  パラメータ: {params}")

    resp = requests.get(url, params=params, timeout=30)
    log(f"  ステータス: {resp.status_code}")
    return resp

def get_data_layer(db="FM08", lang="jp", fmt="json"):
    """階層APIでFM08の階層構造を取得"""
    url = f"{BASE_URL}/getDataLayer"
    params = {
        "db": db,
        "lang": lang,
        "format": fmt,
    }

    log(f"\n[API呼び出し] GET {url}")
    log(f"  パラメータ: {params}")

    resp = requests.get(url, params=params, timeout=30)
    log(f"  ステータス: {resp.status_code}")
    return resp

def main():
    log("=" * 70)
    log("日銀API FM08データベース USD関連系列調査")
    log(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 70)

    # ====================================================
    # 1. FM08のメタデータをキーワード「米ドル」で検索
    # ====================================================
    log("\n" + "=" * 60)
    log("1. FM08メタデータ検索 - キーワード: 米ドル")
    log("=" * 60)

    resp = get_metadata(db="FM08", keyword="米ドル", lang="jp", fmt="json")
    if resp.status_code == 200:
        try:
            data = resp.json()
            log(f"\n[レスポンスJSON構造]")
            log(json.dumps(data, ensure_ascii=False, indent=2)[:3000])

            # 系列コード一覧を抽出
            series_list = []
            if isinstance(data, dict):
                # 様々なキー構造に対応
                for key in ["series", "data", "items", "result", "metadata"]:
                    if key in data:
                        series_list = data[key]
                        log(f"\n  → '{key}'キーで{len(series_list)}件の系列を発見")
                        break
                if not series_list and "stat" in data:
                    log(f"\n  → レスポンス全体: {json.dumps(data, ensure_ascii=False, indent=2)[:2000]}")
            elif isinstance(data, list):
                series_list = data
                log(f"\n  → リスト形式で{len(series_list)}件の系列")

            if series_list:
                log(f"\n[米ドル関連系列 - {len(series_list)}件]")
                for s in series_list[:50]:
                    log(f"  {s}")
        except json.JSONDecodeError:
            log(f"\n[テキストレスポンス]")
            log(resp.text[:3000])
    else:
        log(f"\nエラー: {resp.text[:500]}")

    import time
    time.sleep(1)

    # ====================================================
    # 2. FM08のメタデータをキーワード「USD」で検索（英語）
    # ====================================================
    log("\n" + "=" * 60)
    log("2. FM08メタデータ検索 - キーワード: USD (lang=en)")
    log("=" * 60)

    resp = get_metadata(db="FM08", keyword="USD", lang="en", fmt="json")
    if resp.status_code == 200:
        try:
            data = resp.json()
            log(f"\n[レスポンスJSON構造]")
            log(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
        except json.JSONDecodeError:
            log(f"\n[テキストレスポンス]")
            log(resp.text[:3000])
    else:
        log(f"\nエラー: {resp.text[:500]}")

    time.sleep(1)

    # ====================================================
    # 3. FM08のコードAPI（キーワードなし全件）
    # ====================================================
    log("\n" + "=" * 60)
    log("3. FM08 コードAPI（全件取得）")
    log("=" * 60)

    resp = get_data_code(db="FM08", lang="jp", fmt="json")
    if resp.status_code == 200:
        try:
            data = resp.json()
            log(f"\n[レスポンスJSON構造 (最初の3000文字)]")
            log(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
        except json.JSONDecodeError:
            log(f"\n[テキストレスポンス (最初の3000文字)]")
            log(resp.text[:3000])
    else:
        log(f"\nエラー: {resp.text[:500]}")

    time.sleep(1)

    # ====================================================
    # 4. FM08の階層API
    # ====================================================
    log("\n" + "=" * 60)
    log("4. FM08 階層API")
    log("=" * 60)

    resp = get_data_layer(db="FM08", lang="jp", fmt="json")
    if resp.status_code == 200:
        try:
            data = resp.json()
            log(f"\n[レスポンスJSON構造 (最初の3000文字)]")
            log(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
        except json.JSONDecodeError:
            log(f"\n[テキストレスポンス (最初の3000文字)]")
            log(resp.text[:3000])
    else:
        log(f"\nエラー: {resp.text[:500]}")

    time.sleep(1)

    # ====================================================
    # 5. CSV形式でメタデータ取得（米ドル、日本語）
    # ====================================================
    log("\n" + "=" * 60)
    log("5. FM08メタデータ CSV形式 - キーワード: 米ドル")
    log("=" * 60)

    resp = get_metadata(db="FM08", keyword="米ドル", lang="jp", fmt="csv")
    if resp.status_code == 200:
        log(f"\n[CSVレスポンス]")
        log(resp.text[:5000])
    else:
        log(f"\nエラー: {resp.text[:500]}")

    time.sleep(1)

    # ====================================================
    # 6. CSV形式でFM08全件メタデータ取得
    # ====================================================
    log("\n" + "=" * 60)
    log("6. FM08メタデータ CSV形式 全件")
    log("=" * 60)

    resp = get_metadata(db="FM08", keyword=None, lang="jp", fmt="csv")
    if resp.status_code == 200:
        log(f"\n[CSVレスポンス (全文)]")
        log(resp.text)
    else:
        log(f"\nエラー: {resp.text[:500]}")

    time.sleep(1)

    # ====================================================
    # 7. FM08のメタデータをキーワード「ドル」で検索
    # ====================================================
    log("\n" + "=" * 60)
    log("7. FM08メタデータ検索 - キーワード: ドル")
    log("=" * 60)

    resp = get_metadata(db="FM08", keyword="ドル", lang="jp", fmt="csv")
    if resp.status_code == 200:
        log(f"\n[CSVレスポンス]")
        log(resp.text[:5000])
    else:
        log(f"\nエラー: {resp.text[:500]}")

    log("\n" + "=" * 70)
    log("調査完了")
    log("=" * 70)

if __name__ == "__main__":
    main()
