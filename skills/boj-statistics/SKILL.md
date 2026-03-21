---
name: boj-statistics
description: >
  日本銀行（BOJ）の時系列統計データ検索APIを使って経済・金融統計データを取得・分析するスキル。
  Use this skill whenever the user wants to retrieve Japanese economic or financial statistics,
  monetary data, or time-series data from the Bank of Japan.

  Use when:
  - 日銀統計データ・日銀API・BOJ APIを使ってデータを取得したい
  - 為替レート・金利・マネーストック・物価指数・短観データを取得したい
  - Exchange rates (USD/JPY etc.), interest rates, money supply, price indices, Tankan survey data
  - stat-search.boj.or.jp からデータを取得・分析したい
  - getDataCode / getDataLayer / getMetadata を使いたい
  - 経済指標・金融データ・マクロ統計の時系列を取得したい
  - Japanese macroeconomic statistics, monetary policy data, financial market data

  Keywords: 日銀API, 日銀統計, BOJ API, 時系列統計データ, 経済統計, 金融データ,
  為替レート, 金利, マネーストック, 物価指数, 短観, Tankan, 日本銀行,
  getDataCode, getDataLayer, getMetadata, stat-search.boj.or.jp
---

# 日銀時系列統計データ取得スキル

日本銀行の公式API（`stat-search.boj.or.jp`）を使って、為替・金利・マネーストック・物価指数・短観など多様な経済統計を取得する。

## 必須環境

```bash
source /home/user/skills/.venv/bin/activate
pip install requests pandas
```

## ワークフロー

```
ステップ1: 系列コードを調べる
  python skills/boj-statistics/scripts/search_series.py --db FM08 --keyword "USD"

ステップ2: 系列コードでデータを取得
  python skills/boj-statistics/scripts/get_data.py --db FM08 --code FXUSDM --start 202001 --end 202412

ステップ3: 必要に応じてCSV保存 or カテゴリ一括取得
  python skills/boj-statistics/scripts/get_data.py ... --output result.csv
  python skills/boj-statistics/scripts/get_layer.py --db FM08 --layer1 USD --frequency M
```

## 機能一覧

| やりたいこと | スクリプト | 使用例 |
|---|---|---|
| 系列コードを探す・一覧を見る | `search_series.py` | `--db FM08 --keyword "USD"` |
| 特定系列のデータを取得 | `get_data.py` | `--db FM08 --code FXUSDM --start 202401` |
| 複数系列を同時取得 | `get_data.py` | `--code FXUSDM,FXEURM --start 202001` |
| カテゴリ階層でまとめて取得 | `get_layer.py` | `--db FM08 --layer1 USD --frequency M` |

## スクリプト詳細

### `search_series.py` — 系列の探索

**使用API:** `getMetadata`

```bash
# FM08（外国為替）DB内のUSD関連系列を検索
python skills/boj-statistics/scripts/search_series.py --db FM08 --keyword "USD"

# DB内の全系列一覧（件数が多い場合は --keyword で絞り込む）
python skills/boj-statistics/scripts/search_series.py --db CO

# 英語表示
python skills/boj-statistics/scripts/search_series.py --db IR01 --keyword "overnight" --lang en
```

**出力:** 系列コード・名称・頻度・データ期間の表

### `get_data.py` — コード指定でデータ取得

**使用API:** `getDataCode`

```bash
# USD/JPY月次データ（2024年）
python skills/boj-statistics/scripts/get_data.py --db FM08 --code FXUSDM --start 202401 --end 202412

# 複数系列を同時取得
python skills/boj-statistics/scripts/get_data.py --db FM08 --code FXUSDM,FXEURM --start 202001

# CSV保存
python skills/boj-statistics/scripts/get_data.py --db MD02 --code MD02MABJMTA --output result.csv

# 英語表示
python skills/boj-statistics/scripts/get_data.py --db FM08 --code FXUSDM --lang en
```

**制限:** 1リクエスト最大250系列 / 60,000データポイント（自動ページネーション対応）

### `get_layer.py` — カテゴリ階層からデータ取得

**使用API:** `getDataLayer`

```bash
# FM08のUSDカテゴリ・月次データをまとめて取得
python skills/boj-statistics/scripts/get_layer.py --db FM08 --layer1 USD --frequency M

# 期間指定
python skills/boj-statistics/scripts/get_layer.py --db FM08 --layer1 USD --frequency M --start 202001 --end 202412

# 階層を深く指定
python skills/boj-statistics/scripts/get_layer.py --db FM08 --layer1 USD --layer2 Tokyo --frequency M

# CSV保存
python skills/boj-statistics/scripts/get_layer.py --db FM08 --layer1 USD --frequency M --output usd_data.csv
```

**制限:** 1リクエスト最大1,250系列（自動ページネーション対応）

## パラメータ共通仕様

| パラメータ | 形式 | 例 |
|---|---|---|
| `--db` | DBコード | FM08, CO, IR01, MD02 |
| `--start` / `--end` | YYYYMM | 202401, 202412 |
| `--lang` | jp または en | jp（デフォルト） |
| `--output` | ファイルパス | result.csv |
| `--frequency` | D/M/Q/CY | M=月次, Q=四半期 |

## 参照ファイル

DBコード・系列コード・周波数の詳細は `references/database_guide.md` を参照。
よく使うDB・系列コードの早見表が記載されている。
