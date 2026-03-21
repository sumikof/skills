#!/usr/bin/env python3
"""
日銀時系列統計APIのgetDataLayerを使って、カテゴリ階層からデータをまとめて取得する。

使用例:
  python get_layer.py --db FM08 --layer1 USD --frequency M
  python get_layer.py --db FM08 --layer1 USD --frequency M --start 202001 --end 202412
  python get_layer.py --db FM08 --layer1 USD --frequency M --output usd_data.csv
  python get_layer.py --db MD02 --frequency M --start 202001
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
import requests

BASE_URL = "https://www.stat-search.boj.or.jp/api/v1"


def fetch_data_layer(
    db: str,
    layer1: str | None,
    layer2: str | None,
    layer3: str | None,
    layer4: str | None,
    layer5: str | None,
    frequency: str | None,
    start_date: str | None,
    end_date: str | None,
    lang: str,
) -> list[dict]:
    """getDataLayerで階層カテゴリからデータを取得する。ページネーション自動処理。"""
    results = []
    params: dict = {
        "format": "json",
        "lang": lang,
        "db": db,
    }
    # layer1〜5は指定があった場合のみ追加
    for i, val in enumerate([layer1, layer2, layer3, layer4, layer5], start=1):
        if val:
            params[f"layer{i}"] = val
    if frequency:
        params["frequency"] = frequency
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date

    start_position = None

    while True:
        if start_position is not None:
            params["startPosition"] = start_position

        try:
            resp = requests.get(f"{BASE_URL}/getDataLayer", params=params, timeout=30)
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
                print("該当データなし: 指定した条件のデータが見つかりませんでした。")
                print("ヒント: --db, --layer1, --frequency の指定を確認してください。")
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
        print(f"  次ページ取得中... ({len(results)} 件取得済み)")

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
    """系列データリストをワイド形式のDataFrameに変換する。"""
    name_key = "NAME_OF_TIME_SERIES_J" if lang == "jp" else "NAME_OF_TIME_SERIES"

    series_dfs = []
    for item in results:
        code = item.get("SERIES_CODE", item.get("SERIES CODE", "unknown"))
        name = item.get(name_key, item.get("NAME_OF_TIME_SERIES_J", ""))
        values_block = item.get("VALUES", {})

        dates = [parse_date(d) for d in values_block.get("SURVEY_DATES", [])]
        vals = values_block.get("VALUES", [])

        if not dates:
            continue

        col_name = code if not name else f"{code} ({name[:30]})"
        df = pd.DataFrame({"日付": dates, col_name: vals})
        df = df.set_index("日付")
        series_dfs.append(df)

    if not series_dfs:
        return pd.DataFrame()

    combined = pd.concat(series_dfs, axis=1)
    combined.index.name = "日付"
    return combined


def print_series_summary(results: list[dict], lang: str) -> None:
    """取得系列のサマリーを表示する。"""
    name_key = "NAME_OF_TIME_SERIES_J" if lang == "jp" else "NAME_OF_TIME_SERIES"
    print(f"\n--- 取得系列一覧 ({len(results)} 件) ---")
    for item in results[:20]:  # 20件まで表示
        code = item.get("SERIES_CODE", item.get("SERIES CODE", ""))
        name = item.get(name_key, item.get("NAME_OF_TIME_SERIES_J", ""))
        freq = item.get("FREQUENCY", "")
        n = len(item.get("VALUES", {}).get("VALUES", []))
        print(f"  {code}: {name[:50]} [{freq}] {n}件")
    if len(results) > 20:
        print(f"  ... 他 {len(results) - 20} 件")


def main():
    parser = argparse.ArgumentParser(
        description="日銀APIからカテゴリ階層を指定してデータをまとめて取得する",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  %(prog)s --db FM08 --layer1 USD --frequency M
  %(prog)s --db FM08 --layer1 USD --frequency M --start 202001 --end 202412
  %(prog)s --db FM08 --layer1 EUR --frequency M --output eur_data.csv
  %(prog)s --db MD02 --frequency M --start 202001
  %(prog)s --db FM08 --layer1 USD --layer2 Tokyo --frequency M

頻度コード:
  D=日次, M=月次, Q=四半期, CY=暦年

主なDBコード:
  FM08  外国為替レート    MD02  マネーストック
  IR01  金利             PR01  企業物価指数
        """,
    )
    parser.add_argument("--db", required=True, help="データベースコード（例: FM08, MD02）")
    parser.add_argument("--layer1", default=None, help="階層1（例: USD, EUR）")
    parser.add_argument("--layer2", default=None, help="階層2")
    parser.add_argument("--layer3", default=None, help="階層3")
    parser.add_argument("--layer4", default=None, help="階層4")
    parser.add_argument("--layer5", default=None, help="階層5")
    parser.add_argument("--frequency", default=None, choices=["D", "M", "Q", "CY"],
                        help="頻度 D=日次/M=月次/Q=四半期/CY=暦年")
    parser.add_argument("--start", default=None, help="取得開始年月 YYYYMM（例: 202001）")
    parser.add_argument("--end", default=None, help="取得終了年月 YYYYMM（例: 202412）")
    parser.add_argument("--lang", default="jp", choices=["jp", "en"], help="表示言語（デフォルト: jp）")
    parser.add_argument("--output", default=None, help="CSV保存先ファイルパス（例: result.csv）")
    args = parser.parse_args()

    # 取得条件の表示
    conditions = [f"DB='{args.db}'"]
    for i in range(1, 6):
        v = getattr(args, f"layer{i}", None)
        if v:
            conditions.append(f"layer{i}={v}")
    if args.frequency:
        conditions.append(f"頻度={args.frequency}")
    if args.start or args.end:
        conditions.append(f"{args.start or '開始'}〜{args.end or '最新'}")

    print(f"データ取得中: {', '.join(conditions)}")

    results = fetch_data_layer(
        db=args.db,
        layer1=args.layer1,
        layer2=args.layer2,
        layer3=args.layer3,
        layer4=args.layer4,
        layer5=args.layer5,
        frequency=args.frequency,
        start_date=args.start,
        end_date=args.end,
        lang=args.lang,
    )

    if not results:
        print("データが取得できませんでした。条件を見直してください。")
        sys.exit(1)

    print_series_summary(results, args.lang)

    df = build_dataframe(results, args.lang)
    if df.empty:
        print("データが空です。")
        sys.exit(0)

    # 表示設定
    pd.set_option("display.max_rows", 500)
    pd.set_option("display.max_columns", 20)
    pd.set_option("display.unicode.east_asian_width", True)
    pd.set_option("display.width", 160)

    # 多系列の場合は先頭5列のみ表示
    display_df = df.iloc[:, :5] if len(df.columns) > 5 else df
    suffix = f"\n（先頭5系列のみ表示。全{len(df.columns)}系列はCSV保存を推奨）" if len(df.columns) > 5 else ""
    print(f"\n=== データ ({len(df)} 件 × {len(df.columns)} 系列) ==={suffix}\n")
    print(display_df.to_string())

    # CSV保存
    if args.output:
        out_path = Path(args.output)
        df.to_csv(out_path, encoding="utf-8-sig")
        print(f"\nCSV保存: {out_path.resolve()} （{len(df.columns)} 系列 × {len(df)} 件）")
    elif len(df.columns) > 5:
        print("\nヒント: 系列が多い場合は --output result.csv でCSVに保存することを推奨します。")


if __name__ == "__main__":
    main()
