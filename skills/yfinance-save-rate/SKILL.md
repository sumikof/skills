---
name: yfinance-save-rate
description: "yfinanceで株価・指数・先物・ETF・債券利回り・為替レートを取得しSQLiteに保存するスキル。Use when: (1) 株価を定期的に記録したい, (2) 株価・レートをDBに蓄積したい, (3) 株価データをSQLiteに保存したい, (4) 株価の履歴をローカルに保管したい, (5) 指数・先物・ETF・為替レートを一括取得したい, (6) domain別に相場データを管理したい. Keywords: 株価保存, stock price save, sqlite, yfinance, 株価DB, 株価記録, price history, 株価履歴, 指数, index, 先物, futures, ETF, 為替, exchange rate, 債券利回り, bond yield"
---

# yfinance-save-rate

yfinanceで株価・各種レートを取得し、SQLiteデータベースに保存するスキル。

## 必須環境

```bash
pip install yfinance
```

## ワークフロー

1. **取得対象を決める** → ティッカー個別指定 or domainで一括指定
2. **最終取得日時を確認する** → domainを使う場合はスクリプトで確認する（DB・テーブル・レコード未存在も自動で考慮）
   ```bash
   python3 scripts/check_fetch_time.py <domain> [--db <DBパス>]
   ```
   - `未取得` と表示された場合、または `fetched_at` が古い場合 → 手順3へ
   - 十分新しい場合 → 取得不要
3. **スクリプト実行** → `python3 scripts/save_price.py [ティッカー...] [オプション]`
4. **結果確認** → 銘柄ごとの保存件数と最新値が表示される

## 使用例

```bash
# ティッカーを個別指定
python3 scripts/save_price.py 7203.T
python3 scripts/save_price.py 7203.T 6758.T 9984.T

# domain一括取得（ticker省略時）
python3 scripts/save_price.py --domain ovr-index
python3 scripts/save_price.py --domain exchange-rate

# 取得期間を指定（DBはデフォルトのfinance-rate.db）
python3 scripts/save_price.py --domain ovr-etf --period 3mo

# DBパスを明示指定する場合
python3 scripts/save_price.py --domain ovr-etf --db /path/to/my.db --period 3mo
```

## domainと取得対象

| domain | 内容 |
|--------|------|
| `dom`（デフォルト） | スクリプト内 `ALL_TICKERS` リスト |
| `ovr-index` | 主要株価指数（DJI, NDX, GSPC, N225 など） |
| `cmd-future` | 商品先物（原油, 金, 農産物 など） |
| `ovr-etf` | 主要ETF（SPY, QQQ, GLD など） |
| `bond-yields` | 米国債利回り（TNX, FVX, TYX） |
| `exchange-rate` | 主要為替レート（USD/JPY, EUR/USD など） |

domain一括取得を実行すると、完了後に `domain_fetch_log` テーブルへ取得日時が記録される。
ティッカー個別指定の場合は記録されない。

## DBスキーマ

```sql
-- 株価・レートデータ
CREATE TABLE stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date)  -- 同一銘柄・同一日付は上書き
);

-- domain別の最終取得日時
CREATE TABLE domain_fetch_log (
    domain TEXT PRIMARY KEY,
    fetched_at TEXT NOT NULL  -- ローカル時刻
);
```
