#!/usr/bin/env python3
"""yfinanceで株価を取得してSQLiteに保存するスクリプト"""

import argparse
import sqlite3
from datetime import datetime
from typing import List

import yfinance as yf

from dataclasses import dataclass
import enum


class OvrIndex(enum.Enum):
    DJI = '^DJI'  # Dow Jones Industrial Average
    DJT = '^DJT'  # , 'Dow Jones Trnsport
    DJU = '^DJU'  # Dow Jones Utility Average
    BANK = '^BANK'  # NASDAQ Bank
    IXCO = '^IXCO'  # NASDAQ Computer
    NDX = '^NDX'  # NASDAQ-100
    NBI = '^NBI'  # NASDAQ Biotechnology
    NDXT = '^NDXT'  # NASDAQ 100 Technology
    INDS = '^INDS'  # NASDAQ Industrial
    INSR = '^INSR'  # NASDAQ Insurance
    OFIN = '^OFIN'  # NASDAQ Other Finance
    IXTC = '^IXTC'  # NASDAQ Telecommunications
    TRAN = '^TRAN'  # NASDAQ Transportation
    NYY = '^NYY'  # NYSE TMT INDEX
    NYI = '^NYI'  # NYSE INTL 100 INDEX
    NY = '^NY'  # NYSE US 100 INDEX
    NYL = '^NYL'  # NYSE NY World Leader Index
    XMI = '^XMI'  # NYSE ACRA Major Market Index
    OEX = '^OEX'  # S&P 100 Index
    GSPC = '^GSPC'  # S&P 500 Index
    HSI = '^HSI'  # Hang Seng Index
    FCHI = '^FCHI'  # CAC 40
    BVSP = '^BVSP'  # IBOVESPA
    N225 = '^N225'  # Nikkei 225
    RUA = '^RUA'  # Russel 3000
    XSX = '^XAX'  # NY AMEX Composit Index
    SOX = '^SOX'  # PHLX Semiconductor Index
    DXY = 'DX-Y.NYB'  # US Dollar/USDX - Index - Cash')


class CmdFuture(enum.Enum):
    ES_F = 'ES=F'  # S&P Futures
    YM_F = 'YM=F'  # Dow Futures
    NQ_F = 'NQ=F'  # Nasdaq Futures
    RTY_F = 'RTY=F'  # Russell 2000 Futures
    ZB_F = 'ZB=F'  # U.S. Treasury Bond Futures,Dec-
    ZN_F = 'ZN=F'  # 10-Year T-Note Futures,Dec-2021
    ZF_F = 'ZF=F'  # Five-Year US Treasury Note Futu
    ZT_F = 'ZT=F'  # 2-Year T-Note Futures,Dec-2021
    GC_F = 'GC=F'  # Gold
    MGC_F = 'MGC=F'  # Micro Gold Futures,Feb-2022
    SI_F = 'SI=F'  # Silver
    SIL_F = 'SIL=F'  # Micro Silver Futures,Dec-2021
    PL_F = 'PL=F'  # Platinum Jan 22
    HG_F = 'HG=F'  # Copper Dec 21
    PA_F = 'PA=F'  # Palladium Mar 22
    CL_F = 'CL=F'  # Crude Oil
    HO_F = 'HO=F'  # Heating Oil Dec 21
    NG_F = 'NG=F'  # Natural Gas Dec 21
    RB_F = 'RB=F'  # RBOB Gasoline Dec 21
    BZ_F = 'BZ=F'  # Brent Crude Oil Last Day Financ
    B0_F = 'B0=F'  # Mont Belvieu LDH Propane (OPIS)
    ZC_F = 'ZC=F'  # Corn Futures,Mar-2022
    ZO_F = 'ZO=F'  # Oat Futures,Mar-2022
    KE_F = 'KE=F'  # KC HRW Wheat Futures,Dec-2021
    ZR_F = 'ZR=F'  # Rough Rice Futures,Jan-2022
    ZM_F = 'ZM=F'  # Soybean Meal Futures,Jan-2022
    ZL_F = 'ZL=F'  # Soybean Oil Futures,Jan-2022
    ZS_F = 'ZS=F'  # Soybean Futures,Jan-2022
    GF_F = 'GF=F'  # Feeder Cattle Futures,Jan-2022
    HE_F = 'HE=F'  # Lean Hogs Futures,Dec-2021
    LE_F = 'LE=F'  # Live Cattle Futures,Dec-2021
    CC_F = 'CC=F'  # Cocoa Mar 22
    KC_F = 'KC=F'  # Coffee Mar 22
    CT_F = 'CT=F'  # Cotton Mar 22
    LBS_F = 'LBS=F'  # Lumber Jan 22
    OJ_F = 'OJ=F'  # Orange Juice Jan 22
    SB_F = 'SB=F'  # Sugar #11 Mar 22


class OvrEtf(enum.Enum):
    DIA = 'DIA'
    SPY = 'SPY'
    QQQ = 'QQQ'
    IBB = 'IBB'
    XLV = 'XLV'
    IWM = 'IWM'
    EEM = 'EEM'
    EFA = 'EFA'
    XLP = 'XLP'
    XLY = 'XLY'
    ITB = 'ITB'
    XLU = 'XLU'
    XLF = 'XLF'
    VGT = 'VGT'
    VT = 'VT'
    FDN = 'FDN'
    IWO = 'IWO'
    IWN = 'IWN'
    IYF = 'IYF'
    XLK = 'XLK'
    XOP = 'XOP'
    USMV = 'USMV'
    BAB = 'BAB'
    GLD = 'GLD'
    VNQ = 'VNQ'
    SCHH = 'SCHH'
    IYR = 'IYR'
    XLRE = 'XLRE'
    AGG = 'AGG'
    BND = 'BND'
    LQD = 'LQD'
    VCSH = 'VCSH'
    VCIT = 'VCIT'
    JNK = 'JNK'
    JETS = 'JETS'


class BondYields(enum.Enum):
    TNX = '^TNX'
    FVX = '^FVX'
    TYX = '^TYX'


class ExchangeRate(enum.Enum):
    USD_JPY = 'JPY=X'
    EUR_USD = 'EURUSD=X'
    GBP_USD = 'GBPUSD=X'
    USD_CHF = 'CHF=X'
    AUD_USD = 'AUDUSD=X'
    NZD_USD = 'NZDUSD=X'
    USD_CAD = 'CAD=X'
    USD_CNH = 'CNH=X'


# xlsxから全銘柄リストを取得するURL
DOM_XLSX_URL: str = "https://www.mof.go.jp/policy/international_policy/gaitame_kawase/fdi/list.xlsx"


def load_tickers_from_xlsx(url: str) -> List[str]:
    """外部のxlsxファイルを取得し、ティッカー一覧を返す。

    シート「上場企業の銘柄リスト」の1行目をヘッダー、2行目以降をデータとして読み込む。
    「証券コード」列の値に `.T` を付加してyfinance形式のティッカーを生成する。

    Args:
        url: xlsxファイルのURL
    Returns:
        ティッカーシンボルのリスト（例: ["1301.T", "1332.T", ...]）
    """
    import pandas as pd
    df = pd.read_excel(url, sheet_name="上場企業の銘柄リスト", header=0)
    code_col = [c for c in df.columns if "証券コード" in c][0]
    codes = df[code_col].dropna().astype(str).str.strip()
    return [f"{code}.T" for code in codes if code]


# 全銘柄リスト（ticker指定なし時に使用）
ALL_TICKERS: List[str] = []


_DOMAIN_MAP = {
    "ovr-index":    OvrIndex,
    "cmd-future":   CmdFuture,
    "ovr-etf":      OvrEtf,
    "bond-yields":  BondYields,
    "exchange-rate": ExchangeRate,
}


def get_all_tickers(domain: str = "dom") -> List[str]:
    """全銘柄リストを返す。

    Args:
        domain: 取得対象ドメイン（デフォルト: "dom"）
                "dom"の場合はALL_TICKERSを返す。
                それ以外は_DOMAIN_MAPのenumクラスのvalueリストを返す。
    """
    if domain == "DOM":
        if DOM_XLSX_URL:
            return load_tickers_from_xlsx(DOM_XLSX_URL)
        return ALL_TICKERS
    enum_cls = _DOMAIN_MAP.get(domain)
    if enum_cls is None:
        raise ValueError(f"未対応のdomain: '{domain}'. 利用可能: DOM, {', '.join(_DOMAIN_MAP)}")
    return [e.value for e in enum_cls]


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, date)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS domain_fetch_log (
            domain TEXT PRIMARY KEY,
            fetched_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def save_domain_fetch_time(conn: sqlite3.Connection, domain: str) -> None:
    """domainの取得日時を現在時刻で保存（既存レコードは上書き）。"""
    conn.execute("""
        INSERT OR REPLACE INTO domain_fetch_log (domain, fetched_at)
        VALUES (?, datetime('now', 'localtime'))
    """, (domain,))
    conn.commit()


def _split_by_ticker(df: "pandas.DataFrame", tickers: List[str]) -> dict:
    """yfinance のダウンロード結果を {ticker: DataFrame} に正規化する。

    yfinance は単一ティッカーと複数ティッカーでカラム構造が異なる:
    - 単一: フラット列 (Open, High, Low, Close, Volume)
    - 複数: MultiIndex 列 (Price, Ticker) または (Ticker, Price)

    いずれの形式でも各ティッカーのフラットな DataFrame に変換して返す。
    """
    import pandas as pd

    if not isinstance(df.columns, pd.MultiIndex):
        # 単一ティッカー: そのまま返す
        return {tickers[0]: df}

    # MultiIndex の場合、どちらのレベルにティッカーがあるか判定する
    level0_vals = set(df.columns.get_level_values(0))
    is_ticker_at_level0 = any(t in level0_vals for t in tickers)

    result = {}
    for ticker in tickers:
        try:
            if is_ticker_at_level0:
                # (Ticker, Price) 形式
                ticker_df = df[ticker].copy()
            else:
                # (Price, Ticker) 形式 → xs でティッカー軸を抽出
                ticker_df = df.xs(ticker, axis=1, level=1).copy()
            if not ticker_df.empty:
                result[ticker] = ticker_df
        except KeyError:
            pass
    return result


def save_prices(conn: sqlite3.Connection, tickers: List[str], period: str) -> dict:
    """複数ティッカーの株価を一括取得してDBに保存する。

    Args:
        tickers: ティッカーシンボルのリスト
        period: 取得期間（例: 1mo, 3mo, 1y）
    Returns:
        {ticker: 保存件数} の辞書
    """
    import pandas as pd

    df = yf.download(tickers, period=period, auto_adjust=True, progress=False)
    if df.empty:
        return {}

    ticker_dfs = _split_by_ticker(df, tickers)
    counts = {}
    rows = []
    for ticker, tdf in ticker_dfs.items():
        for date, row in tdf.iterrows():
            rows.append((
                ticker,
                str(date.date()),
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                int(row["Volume"]),
            ))
        counts[ticker] = len(tdf)

    conn.executemany("""
        INSERT OR REPLACE INTO stock_prices (ticker, date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    return counts


def main():
    parser = argparse.ArgumentParser(description="yfinanceで株価を取得してSQLiteに保存")
    parser.add_argument("tickers", nargs="*", help="ティッカーシンボル（例: 7203.T）。省略時は全銘柄を取得")
    parser.add_argument("--db", default="finance-rate.db", help="SQLiteファイルパス（デフォルト: finance-rate.db）")
    parser.add_argument("--period", default="1mo", help="取得期間（例: 1mo, 3mo, 1y）デフォルト: 1mo")
    parser.add_argument("--domain", default="DOM", help="全銘柄取得時のドメイン（デフォルト: DOM）")
    args = parser.parse_args()

    # ticker未指定の場合は全銘柄を対象にする
    use_domain = not args.tickers
    tickers = args.tickers if args.tickers else get_all_tickers(args.domain)
    if not tickers:
        print("取得対象の銘柄がありません。ALL_TICKERSを設定するか、引数でティッカーを指定してください。")
        return

    conn = init_db(args.db)
    print(f"DB: {args.db} | 対象銘柄数: {len(tickers)}")

    counts = save_prices(conn, tickers, args.period)
    for ticker, count in counts.items():
        if count > 0:
            row = conn.execute(
                "SELECT date, close FROM stock_prices WHERE ticker=? ORDER BY date DESC LIMIT 1",
                (ticker,)
            ).fetchone()
            print(f"[{ticker}] {count}件保存 | 最新: {row[0]} close={row[1]:.2f}")

    # domain一括取得の場合のみ取得日時を記録
    if use_domain:
        save_domain_fetch_time(conn, args.domain)
        print(f"domain '{args.domain}' の取得日時を記録しました")

    conn.close()


if __name__ == "__main__":
    main()
