#!/usr/bin/env python3
"""
日銀時系列統計APIのgetMetadataを使って、DBの系列一覧を取得・検索する。

使用例:
  python search_series.py --db FM08
  python search_series.py --db FM08 --keyword "USD"
  python search_series.py --db CO --keyword "景況"
  python search_series.py --db IR01 --keyword "overnight" --lang en
"""

import argparse
import sys

import pandas as pd
import requests

BASE_URL = "https://www.stat-search.boj.or.jp/api/v1"


def fetch_metadata(db: str, lang: str) -> list[dict]:
    """getMetadataで指定DBの全系列メタデータを取得する。ページネーション自動処理。"""
    results = []
    params = {
        "format": "json",
        "lang": lang,
        "db": db,
    }
    start_position = None

    while True:
        if start_position is not None:
            params["startPosition"] = start_position

        try:
            resp = requests.get(f"{BASE_URL}/getMetadata", params=params, timeout=30)
        except requests.RequestException as e:
            print(f"通信エラー: {e}")
            sys.exit(1)

        if resp.status_code != 200:
            # エラー時もJSONが返る場合がある
            try:
                err = resp.json()
                msg = err.get("MESSAGE", resp.text)
            except Exception:
                msg = resp.text
            print(f"APIエラー (HTTP {resp.status_code}): {msg}")
            sys.exit(1)

        try:
            data = resp.json()
        except Exception as e:
            print(f"JSONパースエラー: {e}\nレスポンス: {resp.text[:500]}")
            sys.exit(1)

        status = data.get("STATUS", 0)
        if status != 200:
            msg_id = data.get("MESSAGEID", "")
            msg = data.get("MESSAGE", "不明なエラー")
            if msg_id == "M181030I":
                print(f"該当データなし: DB '{db}' にデータが見つかりませんでした。")
                sys.exit(0)
            print(f"APIエラー (STATUS={status}): {msg}")
            sys.exit(1)

        resultset = data.get("RESULTSET", [])
        if isinstance(resultset, dict):
            resultset = [resultset]
        results.extend(resultset)

        next_pos = data.get("NEXTPOSITION")
        if next_pos is None:
            break
        start_position = next_pos

    return results


def build_dataframe(results: list[dict], lang: str) -> pd.DataFrame:
    """メタデータリストをDataFrameに変換する。"""
    rows = []
    name_key = "NAME_OF_TIME_SERIES_J" if lang == "jp" else "NAME_OF_TIME_SERIES"
    for item in results:
        rows.append({
            "系列コード": item.get("SERIES_CODE", item.get("SERIES CODE", "")),
            "名称": item.get(name_key, item.get("NAME_OF_TIME_SERIES_J", "")),
            "頻度": item.get("FREQUENCY", ""),
            "開始": item.get("START_DATE", ""),
            "終了": item.get("END_DATE", ""),
        })
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(
        description="日銀APIの系列メタデータを検索・一覧表示する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s --db FM08
  %(prog)s --db FM08 --keyword "USD"
  %(prog)s --db CO --keyword "景況"
  %(prog)s --db IR01 --keyword "overnight" --lang en

主なDBコード:
  FM08  外国為替レート    MD02  マネーストック
  IR01  金利             PR01  企業物価指数
  CO    短観（Tankan）   MD01  マネタリーベース
  BS01  日銀バランスシート
        """,
    )
    parser.add_argument("--db", required=True, help="データベースコード（例: FM08, CO, IR01）")
    parser.add_argument("--keyword", default="", help="名称でフィルタリング（部分一致）")
    parser.add_argument("--lang", default="jp", choices=["jp", "en"], help="表示言語（デフォルト: jp）")
    args = parser.parse_args()

    print(f"DB '{args.db}' の系列メタデータを取得中...")
    results = fetch_metadata(args.db, args.lang)

    if not results:
        print(f"DB '{args.db}' にデータが見つかりませんでした。")
        sys.exit(0)

    df = build_dataframe(results, args.lang)

    # キーワードフィルタ
    if args.keyword:
        mask = df["名称"].str.contains(args.keyword, case=False, na=False) | \
               df["系列コード"].str.contains(args.keyword, case=False, na=False)
        df = df[mask]
        if df.empty:
            print(f"キーワード '{args.keyword}' に一致する系列が見つかりませんでした。")
            sys.exit(0)

    # 表示設定
    pd.set_option("display.max_rows", 200)
    pd.set_option("display.max_colwidth", 60)
    pd.set_option("display.unicode.east_asian_width", True)
    pd.set_option("display.width", 120)

    keyword_info = f"（キーワード: {args.keyword}）" if args.keyword else ""
    print(f"\n=== DB: {args.db} {keyword_info} — {len(df)} 件 ===\n")
    print(df.to_string(index=False))
    print(f"\n合計: {len(df)} 件")
    print("\nヒント: 系列コードを確認したら get_data.py でデータを取得できます。")
    print(f"  例: python get_data.py --db {args.db} --code <系列コード>")


if __name__ == "__main__":
    main()
