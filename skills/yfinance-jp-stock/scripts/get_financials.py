#!/usr/bin/env python3
"""財務諸表取得スクリプト"""

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


def format_millions(val):
    """金額を百万円単位でフォーマット"""
    if pd.isna(val):
        return "N/A"
    return f"{val / 1e6:,.0f}"


def main():
    parser = argparse.ArgumentParser(description="財務諸表を取得します")
    parser.add_argument("ticker", help="ティッカーシンボル（例: 7203.T または 7203）")
    parser.add_argument("--type", choices=["income", "balance", "cashflow"], default="income",
                        help="財務諸表の種類（income: 損益計算書, balance: 貸借対照表, cashflow: キャッシュフロー計算書）")
    parser.add_argument("--quarterly", action="store_true", help="四半期データを取得")
    args = parser.parse_args()

    ticker = normalize_ticker(args.ticker)
    stock = yf.Ticker(ticker)

    # 銘柄名を取得
    try:
        info = stock.info
        name = info.get("longName") or info.get("shortName") or ticker
    except Exception:
        name = ticker

    type_labels = {
        "income": "損益計算書",
        "balance": "貸借対照表",
        "cashflow": "キャッシュフロー計算書",
    }

    # 財務データを取得
    try:
        if args.type == "income":
            data = stock.quarterly_financials if args.quarterly else stock.financials
        elif args.type == "balance":
            data = stock.quarterly_balance_sheet if args.quarterly else stock.balance_sheet
        else:
            data = stock.quarterly_cashflow if args.quarterly else stock.cashflow
    except Exception as e:
        print(f"エラー: {ticker} の財務データを取得できませんでした。")
        print(f"  詳細: {e}")
        sys.exit(1)

    if data is None or data.empty:
        print(f"エラー: {ticker} の{type_labels[args.type]}データが見つかりません。")
        sys.exit(1)

    # ヘッダー
    period_label = "四半期" if args.quarterly else "通期"
    print(f"\n{'='*60}")
    print(f"  {name} ({ticker})")
    print(f"  {type_labels[args.type]}（{period_label}）")
    print(f"  単位: 百万円")
    print(f"{'='*60}\n")

    # カラム名を日付文字列に変換
    display_df = data.copy()
    display_df.columns = [col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col) for col in display_df.columns]

    # 金額を百万円単位でフォーマット
    display_df = display_df.map(format_millions)

    print(display_df.to_string())
    print()


if __name__ == "__main__":
    main()
