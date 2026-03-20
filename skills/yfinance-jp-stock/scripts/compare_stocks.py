#!/usr/bin/env python3
"""複数銘柄比較スクリプト"""

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


def format_market_cap(val):
    """時価総額を億円単位でフォーマット"""
    if val is None:
        return "N/A"
    oku = val / 1e8
    if oku >= 10000:
        return f"{oku:,.0f}億円"
    return f"{oku:,.0f}億円"


def get_metric(info: dict, key: str):
    """指標を取得"""
    return info.get(key)


def format_val(val, fmt: str):
    """値をフォーマット"""
    if val is None:
        return "N/A"
    if fmt == "price":
        return f"{val:,.1f}"
    elif fmt == "pct":
        return f"{val * 100:.2f}%"
    elif fmt == "pct_raw":
        return f"{val:.2f}%"
    elif fmt == "ratio":
        return f"{val:.2f}"
    elif fmt == "market_cap":
        return format_market_cap(val)
    elif fmt == "int":
        return f"{int(val):,}"
    return str(val)


# 利用可能な指標
METRICS = {
    "price": ("現在値", "regularMarketPrice", "price"),
    "per": ("PER", "trailingPE", "ratio"),
    "forward_per": ("PER（予想）", "forwardPE", "ratio"),
    "pbr": ("PBR", "priceToBook", "ratio"),
    "eps": ("EPS", "trailingEps", "price"),
    "dividend_yield": ("配当利回り", "dividendYield", "pct_raw"),
    "roe": ("ROE", "returnOnEquity", "pct"),
    "market_cap": ("時価総額", "marketCap", "market_cap"),
    "52w_high": ("52週高値", "fiftyTwoWeekHigh", "price"),
    "52w_low": ("52週安値", "fiftyTwoWeekLow", "price"),
    "volume": ("出来高", "volume", "int"),
}

DEFAULT_METRICS = ["price", "per", "pbr", "dividend_yield", "roe", "market_cap"]


def main():
    parser = argparse.ArgumentParser(description="複数銘柄を比較します")
    parser.add_argument("tickers", nargs="+", help="ティッカーシンボル（スペース区切り）")
    parser.add_argument("--metrics", default=",".join(DEFAULT_METRICS),
                        help=f"比較指標（カンマ区切り）。利用可能: {','.join(METRICS.keys())}")
    args = parser.parse_args()

    tickers = [normalize_ticker(t) for t in args.tickers]
    metric_keys = [m.strip() for m in args.metrics.split(",")]

    # 不正な指標チェック
    invalid = [m for m in metric_keys if m not in METRICS]
    if invalid:
        print(f"エラー: 不明な指標: {', '.join(invalid)}")
        print(f"  利用可能な指標: {', '.join(METRICS.keys())}")
        sys.exit(1)

    # 各銘柄の情報を取得
    stock_data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            name = info.get("longName") or info.get("shortName") or ticker
            stock_data[ticker] = {"name": name, "info": info}
        except Exception as e:
            print(f"警告: {ticker} の情報取得に失敗しました: {e}")
            stock_data[ticker] = {"name": ticker, "info": {}}

    if not stock_data:
        print("エラー: いずれの銘柄の情報も取得できませんでした。")
        sys.exit(1)

    # 比較テーブルを構築
    columns = {}
    for ticker in tickers:
        data = stock_data[ticker]
        col_name = f"{data['name']}\n({ticker})"
        values = []
        for key in metric_keys:
            label, info_key, fmt = METRICS[key]
            val = get_metric(data["info"], info_key)
            values.append(format_val(val, fmt))
        columns[col_name] = values

    row_labels = [METRICS[key][0] for key in metric_keys]
    df = pd.DataFrame(columns, index=row_labels)
    df.index.name = "指標"

    # ヘッダー
    print(f"\n{'='*60}")
    print(f"  銘柄比較（{len(tickers)}銘柄）")
    print(f"{'='*60}\n")

    print(df.to_string())
    print()


if __name__ == "__main__":
    main()
