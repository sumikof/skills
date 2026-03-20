#!/usr/bin/env python3
"""株価取得スクリプト（現在値・履歴）"""

import argparse
import sys

import pandas as pd
import yfinance as yf

pd.set_option("display.unicode.east_asian_width", True)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", 200)


def normalize_ticker(ticker: str) -> str:
    """数字のみの入力に.Tを自動付与"""
    if ticker.isdigit():
        return f"{ticker}.T"
    return ticker


def main():
    parser = argparse.ArgumentParser(description="日本株の株価を取得します")
    parser.add_argument("ticker", help="ティッカーシンボル（例: 7203.T または 7203）")
    parser.add_argument("--period", default="1mo", help="取得期間（例: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max）")
    parser.add_argument("--interval", default="1d", help="データ間隔（例: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo）")
    parser.add_argument("--start", default=None, help="開始日（YYYY-MM-DD）")
    parser.add_argument("--end", default=None, help="終了日（YYYY-MM-DD）")
    args = parser.parse_args()

    ticker = normalize_ticker(args.ticker)
    stock = yf.Ticker(ticker)

    # 銘柄名を取得
    try:
        info = stock.info
        name = info.get("longName") or info.get("shortName") or ticker
    except Exception:
        name = ticker

    # 株価データを取得
    if args.start:
        hist = stock.history(start=args.start, end=args.end, interval=args.interval)
    else:
        hist = stock.history(period=args.period, interval=args.interval)

    if hist.empty:
        print(f"エラー: {ticker} のデータを取得できませんでした。ティッカーシンボルを確認してください。")
        print("  ヒント: 日本株は証券コードに .T を付けてください（例: 7203.T）")
        sys.exit(1)

    # 表示期間
    start_date = hist.index[0].strftime("%Y-%m-%d")
    end_date = hist.index[-1].strftime("%Y-%m-%d")

    # ヘッダー
    print(f"\n{'='*60}")
    print(f"  {name} ({ticker})")
    print(f"  期間: {start_date} ~ {end_date}")
    print(f"{'='*60}\n")

    # テーブル表示
    display_df = hist[["Open", "High", "Low", "Close", "Volume"]].copy()
    display_df.columns = ["始値", "高値", "安値", "終値", "出来高"]
    display_df.index = display_df.index.strftime("%Y-%m-%d")
    display_df.index.name = "日付"

    # 数値フォーマット
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
