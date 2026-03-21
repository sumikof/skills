#!/usr/bin/env python3
"""
日銀時系列統計APIのgetDataCodeを使って、系列コード指定でデータを取得する。

使用例:
  python get_data.py --db FM08 --code FXUSDM
  python get_data.py --db FM08 --code FXUSDM --start 202401 --end 202412
  python get_data.py --db FM08 --code FXUSDM,FXEURM --start 202001
  python get_data.py --db FM08 --code FXUSDM --output result.csv
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://www.stat-search.boj.or.jp/api/v1"


def fetch_data_code(
    db: str,
    codes: list[str],
    start_date: str | None,
    end_date: str | None,
    lang: str,
) -> list[dict]:
    """getDataCodeで系列データを取得する。ページネーション自動処理。"""
    results = []
    params = {
        "format": "json",
        "lang": lang,
        "db": db,
        "code": ",".join(codes),
    }
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date

    start_position = None

    while True:
        if start_position is not None:
            params["startPosition"] = start_position

        try:
            resp = requests.get(f"{BASE_URL}/getDataCode", params=params, timeout=30)
        except requests.RequestException as e:
            print(f"通信エラー: {e}")
            sys.exit(1)

        if resp.status_code != 200:
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
                print(f"該当データなし: 指定した条件のデータが見つかりませんでした。")
                print("ヒント: --db, --code, --start, --end の指定を確認してください。")
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


def parse_date(raw: int | str) -> str:
    """YYYYMM または YYYYMMDD 形式の日付を文字列に変換する。"""
    s = str(raw)
    if len(s) == 6:
        return f"{s[:4]}-{s[4:6]}"
    if len(s) == 8:
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return s


def build_dataframe(results: list[dict], lang: str) -> pd.DataFrame:
    """系列データリストをワイド形式のDataFrameに変換する（複数系列は列として並べる）。"""
    name_key = "NAME_OF_TIME_SERIES_J" if lang == "jp" else "NAME_OF_TIME_SERIES"
    unit_key = "UNIT_J" if lang == "jp" else "UNIT"

    series_dfs = []
    for item in results:
        code = item.get("SERIES_CODE", item.get("SERIES CODE", "unknown"))
        name = item.get(name_key, item.get("NAME_OF_TIME_SERIES_J", ""))
        unit = item.get(unit_key, item.get("UNIT_J", ""))
        values_block = item.get("VALUES", {})

        dates = [parse_date(d) for d in values_block.get("SURVEY_DATES", [])]
        vals = values_block.get("VALUES", [])

        if not dates:
            continue

        col_name = f"{code}" if not name else f"{code} ({name})"
        df = pd.DataFrame({"日付": dates, col_name: vals})
        df = df.set_index("日付")
        series_dfs.append((df, unit))

    if not series_dfs:
        return pd.DataFrame()

    # 複数系列を横結合
    combined = pd.concat([s[0] for s in series_dfs], axis=1)
    combined.index.name = "日付"
    return combined


def print_series_info(results: list[dict], lang: str) -> None:
    """取得した系列の情報を表示する。"""
    name_key = "NAME_OF_TIME_SERIES_J" if lang == "jp" else "NAME_OF_TIME_SERIES"
    unit_key = "UNIT_J" if lang == "jp" else "UNIT"

    print("\n--- 取得系列 ---")
    for item in results:
        code = item.get("SERIES_CODE", item.get("SERIES CODE", ""))
        name = item.get(name_key, item.get("NAME_OF_TIME_SERIES_J", ""))
        unit = item.get(unit_key, item.get("UNIT_J", ""))
        freq = item.get("FREQUENCY", "")
        n = len(item.get("VALUES", {}).get("VALUES", []))
        print(f"  {code}: {name} [{unit}] / {freq} / {n}件")


def main():
    parser = argparse.ArgumentParser(
        description="日銀APIから系列コード指定でデータを取得する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s --db FM08 --code FXUSDM
  %(prog)s --db FM08 --code FXUSDM --start 202401 --end 202412
  %(prog)s --db FM08 --code FXUSDM,FXEURM --start 202001
  %(prog)s --db MD02 --code MD02MABJMTA --output result.csv

系列コードの調べ方:
  python search_series.py --db FM08 --keyword "USD"
        """,
    )
    parser.add_argument("--db", required=True, help="データベースコード（例: FM08, CO）")
    parser.add_argument("--code", required=True, help="系列コード（複数はカンマ区切り: FXUSDM,FXEURM）")
    parser.add_argument("--start", default=None, help="取得開始年月 YYYYMM（例: 202001）")
    parser.add_argument("--end", default=None, help="取得終了年月 YYYYMM（例: 202412）")
    parser.add_argument("--lang", default="jp", choices=["jp", "en"], help="表示言語（デフォルト: jp）")
    parser.add_argument("--output", default=None, help="CSV保存先ファイルパス（例: result.csv）")
    args = parser.parse_args()

    codes = [c.strip() for c in args.code.split(",") if c.strip()]
    if not codes:
        print("エラー: --code に有効な系列コードを指定してください。")
        sys.exit(1)

    period_info = ""
    if args.start or args.end:
        period_info = f" ({args.start or '開始'}〜{args.end or '最新'})"

    print(f"DB '{args.db}' / 系列: {', '.join(codes)}{period_info} のデータを取得中...")

    results = fetch_data_code(args.db, codes, args.start, args.end, args.lang)

    if not results:
        print("データが取得できませんでした。--db と --code を確認してください。")
        sys.exit(1)

    print_series_info(results, args.lang)

    df = build_dataframe(results, args.lang)
    if df.empty:
        print("データが空です。")
        sys.exit(0)

    # 表示設定
    pd.set_option("display.max_rows", 500)
    pd.set_option("display.unicode.east_asian_width", True)
    pd.set_option("display.width", 120)

    print(f"\n=== データ ({len(df)} 件) ===\n")
    print(df.to_string())

    # サマリー
    print("\n--- サマリー ---")
    for col in df.columns:
        numeric = pd.to_numeric(df[col], errors="coerce")
        if numeric.notna().any():
            print(
                f"  {col}: 最小={numeric.min():.4g}, 最大={numeric.max():.4g}, "
                f"平均={numeric.mean():.4g}, 最新={numeric.dropna().iloc[-1]:.4g}"
            )

    # CSV保存
    if args.output:
        out_path = Path(args.output)
        df.to_csv(out_path, encoding="utf-8-sig")
        print(f"\nCSV保存: {out_path.resolve()}")


if __name__ == "__main__":
    main()
