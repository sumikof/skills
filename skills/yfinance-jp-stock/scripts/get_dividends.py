#!/usr/bin/env python3
"""配当情報取得スクリプト"""

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
    parser = argparse.ArgumentParser(description="配当情報を取得します")
    parser.add_argument("ticker", help="ティッカーシンボル（例: 7203.T または 7203）")
    args = parser.parse_args()

    ticker = normalize_ticker(args.ticker)
    stock = yf.Ticker(ticker)

    # 銘柄名を取得
    try:
        info = stock.info
        name = info.get("longName") or info.get("shortName") or ticker
    except Exception:
        info = {}
        name = ticker

    # 配当データを取得
    dividends = stock.dividends

    if dividends is None or dividends.empty:
        print(f"エラー: {ticker} の配当データが見つかりません。")
        sys.exit(1)

    # ヘッダー
    print(f"\n{'='*60}")
    print(f"  {name} ({ticker})")
    print(f"  配当履歴")
    print(f"{'='*60}\n")

    # テーブル表示
    display_df = pd.DataFrame({
        "配当金（円）": dividends.values,
    }, index=dividends.index.strftime("%Y-%m-%d"))
    display_df.index.name = "権利確定日"
    display_df["配当金（円）"] = display_df["配当金（円）"].map(lambda x: f"{x:,.1f}")

    print(display_df.to_string())

    # サマリー
    print(f"\n--- サマリー ---")
    print(f"  直近配当額:   {dividends.iloc[-1]:,.1f}円")

    # 年間配当（直近12ヶ月）
    recent = dividends[dividends.index >= dividends.index[-1] - pd.DateOffset(years=1)]
    annual_div = recent.sum()
    print(f"  年間配当:     {annual_div:,.1f}円（直近12ヶ月合計）")

    # 配当利回り
    div_yield = info.get("dividendYield")
    if div_yield is not None:
        print(f"  配当利回り:   {div_yield:.2f}%")
    else:
        current_price = info.get("regularMarketPrice")
        if current_price and current_price > 0:
            calc_yield = annual_div / current_price * 100
            print(f"  配当利回り:   {calc_yield:.2f}%（推計）")
        else:
            print(f"  配当利回り:   N/A")

    # 配当回数
    print(f"  配当実績:     {len(dividends)}回（全期間）")
    print()


if __name__ == "__main__":
    main()
