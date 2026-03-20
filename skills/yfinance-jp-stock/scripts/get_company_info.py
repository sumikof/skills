#!/usr/bin/env python3
"""企業概要・バリュエーション情報取得スクリプト"""

import argparse
import sys

import yfinance as yf


def normalize_ticker(ticker: str) -> str:
    """数字のみの入力に.Tを自動付与"""
    if ticker.isdigit():
        return f"{ticker}.T"
    return ticker


def format_market_cap(value):
    """時価総額を億円単位でフォーマット"""
    if value is None or value == "N/A":
        return "N/A"
    oku = value / 1e8
    if oku >= 10000:
        return f"{oku:,.0f}億円（{oku/10000:,.1f}兆円）"
    return f"{oku:,.0f}億円"


def get_value(info: dict, key: str, fmt: str = "str"):
    """infoから値を安全に取得してフォーマット"""
    val = info.get(key)
    if val is None:
        return "N/A"
    if fmt == "str":
        return str(val)
    elif fmt == "price":
        return f"{val:,.1f}"
    elif fmt == "pct":
        return f"{val * 100:.2f}%"
    elif fmt == "pct_raw":
        return f"{val:.2f}%"
    elif fmt == "ratio":
        return f"{val:.2f}"
    elif fmt == "eps":
        return f"{val:,.1f}"
    elif fmt == "market_cap":
        return format_market_cap(val)
    return str(val)


def main():
    parser = argparse.ArgumentParser(description="企業概要・バリュエーション情報を取得します")
    parser.add_argument("ticker", help="ティッカーシンボル（例: 7203.T または 7203）")
    args = parser.parse_args()

    ticker = normalize_ticker(args.ticker)
    stock = yf.Ticker(ticker)

    try:
        info = stock.info
    except Exception as e:
        print(f"エラー: {ticker} の情報を取得できませんでした。")
        print(f"  詳細: {e}")
        sys.exit(1)

    if not info or info.get("regularMarketPrice") is None:
        print(f"エラー: {ticker} のデータが見つかりません。ティッカーシンボルを確認してください。")
        print("  ヒント: 日本株は証券コードに .T を付けてください（例: 7203.T）")
        sys.exit(1)

    name = info.get("longName") or info.get("shortName") or ticker

    print(f"\n{'='*60}")
    print(f"  {name} ({ticker})")
    print(f"{'='*60}")

    # 企業概要
    print(f"\n--- 企業概要 ---")
    print(f"  銘柄名:     {name}")
    print(f"  セクター:   {get_value(info, 'sector')}")
    print(f"  業種:       {get_value(info, 'industry')}")
    print(f"  市場:       {get_value(info, 'exchange')}")
    print(f"  通貨:       {get_value(info, 'currency')}")
    print(f"  時価総額:   {get_value(info, 'marketCap', 'market_cap')}")
    print(f"  従業員数:   {get_value(info, 'fullTimeEmployees')}")

    website = info.get("website")
    if website:
        print(f"  ウェブサイト: {website}")

    # 株価情報
    print(f"\n--- 株価情報 ---")
    print(f"  現在値:     {get_value(info, 'regularMarketPrice', 'price')}")
    print(f"  前日終値:   {get_value(info, 'previousClose', 'price')}")
    print(f"  始値:       {get_value(info, 'open', 'price')}")
    print(f"  日中高値:   {get_value(info, 'dayHigh', 'price')}")
    print(f"  日中安値:   {get_value(info, 'dayLow', 'price')}")
    print(f"  出来高:     {get_value(info, 'volume')}")

    # バリュエーション
    print(f"\n--- バリュエーション ---")
    print(f"  PER:          {get_value(info, 'trailingPE', 'ratio')}")
    print(f"  PER（予想）:  {get_value(info, 'forwardPE', 'ratio')}")
    print(f"  PBR:          {get_value(info, 'priceToBook', 'ratio')}")
    print(f"  EPS:          {get_value(info, 'trailingEps', 'eps')}")
    print(f"  EPS（予想）:  {get_value(info, 'forwardEps', 'eps')}")
    print(f"  配当利回り:   {get_value(info, 'dividendYield', 'pct_raw')}")
    print(f"  ROE:          {get_value(info, 'returnOnEquity', 'pct')}")
    print(f"  52週高値:     {get_value(info, 'fiftyTwoWeekHigh', 'price')}")
    print(f"  52週安値:     {get_value(info, 'fiftyTwoWeekLow', 'price')}")
    print()


if __name__ == "__main__":
    main()
