#!/usr/bin/env python3
"""指数取得スクリプト（日経225・TOPIX等）"""

import argparse
import sys

import pandas as pd
import yfinance as yf

pd.set_option("display.unicode.east_asian_width", True)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", 200)

# エイリアスマッピング
INDEX_ALIASES = {
    "日経平均": "^N225",
    "日経225": "^N225",
    "nikkei": "^N225",
    "nikkei225": "^N225",
    "topix": "1306.T",
    "TOPIX": "1306.T",
    "マザーズ": "2516.T",
    "グロース": "2516.T",
    "jasdaq": "1551.T",
    "JASDAQ": "1551.T",
    "ダウ": "^DJI",
    "dow": "^DJI",
    "sp500": "^GSPC",
    "S&P500": "^GSPC",
    "nasdaq": "^IXIC",
    "NASDAQ": "^IXIC",
    "reit": "1343.T",
    "REIT": "1343.T",
    "jreit": "1343.T",
}


def resolve_index(name: str) -> str:
    """エイリアスを解決"""
    return INDEX_ALIASES.get(name, name)


def main():
    parser = argparse.ArgumentParser(description="指数データを取得します")
    parser.add_argument("index", help="指数シンボルまたはエイリアス（例: ^N225, 日経平均, TOPIX）")
    parser.add_argument("--period", default="1mo", help="取得期間（例: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max）")
    parser.add_argument("--interval", default="1d", help="データ間隔（例: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo）")
    args = parser.parse_args()

    symbol = resolve_index(args.index)
    ticker = yf.Ticker(symbol)

    # 指数名を取得
    try:
        info = ticker.info
        name = info.get("longName") or info.get("shortName") or symbol
    except Exception:
        name = symbol

    # データ取得
    hist = ticker.history(period=args.period, interval=args.interval)

    if hist.empty:
        print(f"エラー: {symbol} のデータを取得できませんでした。")
        print(f"  指定されたシンボル: {args.index}")
        if args.index != symbol:
            print(f"  解決先シンボル: {symbol}")
        print(f"\n  利用可能なエイリアス:")
        for alias, sym in sorted(INDEX_ALIASES.items()):
            print(f"    {alias:12s} → {sym}")
        sys.exit(1)

    # 表示期間
    start_date = hist.index[0].strftime("%Y-%m-%d")
    end_date = hist.index[-1].strftime("%Y-%m-%d")

    # ヘッダー
    print(f"\n{'='*60}")
    print(f"  {name} ({symbol})")
    print(f"  期間: {start_date} ~ {end_date}")
    print(f"{'='*60}\n")

    # テーブル表示
    display_df = hist[["Open", "High", "Low", "Close", "Volume"]].copy()
    display_df.columns = ["始値", "高値", "安値", "終値", "出来高"]
    display_df.index = display_df.index.strftime("%Y-%m-%d")
    display_df.index.name = "日付"

    for col in ["始値", "高値", "安値", "終値"]:
        display_df[col] = display_df[col].map(lambda x: f"{x:,.1f}")
    display_df["出来高"] = display_df["出来高"].map(lambda x: f"{int(x):,}")

    print(display_df.to_string())

    # サマリー
    close = hist["Close"]
    high_val = hist["High"].max()
    low_val = hist["Low"].min()
    change_rate = (close.iloc[-1] / close.iloc[0] - 1) * 100

    print(f"\n--- サマリー ---")
    print(f"  期間高値: {high_val:,.1f}")
    print(f"  期間安値: {low_val:,.1f}")
    print(f"  終値（最新）: {close.iloc[-1]:,.1f}")
    print(f"  変動率: {change_rate:+.2f}%")
    print()


if __name__ == "__main__":
    main()
