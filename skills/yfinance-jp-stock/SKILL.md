---
name: yfinance-jp-stock
description: "yfinanceを使った日本株の株価・財務情報取得スキル。Use when: (1) 株価を調べる, (2) 財務諸表を取得, (3) PER/PBR/配当利回りを確認, (4) 配当履歴を調べる, (5) 日経平均・TOPIXの推移を確認, (6) 複数銘柄を比較, (7) 条件で銘柄をスクリーニング. Keywords: stock price, 株価, 日本株, yfinance, 財務諸表, financial statements, PER, PBR, 配当, dividend, 日経平均, Nikkei225, TOPIX, screening, スクリーニング, 企業情報, company info, バリュエーション, valuation, 時価総額, market cap, 指数, index"
---

# yfinance-jp-stock

yfinanceを使って日本株の株価・財務・バリュエーション情報をターミナルで取得するスキル。

## 必須環境

```bash
pip install yfinance pandas
```

## ワークフロー

1. **ティッカー特定** → 証券コードに`.T`を付ける（例: トヨタ → `7203.T`）。詳細は`references/ticker_guide.md`参照
2. **機能選択** → 下表から目的に合うスクリプトを選ぶ
3. **スクリプト実行** → `python3 scripts/<スクリプト名>.py <引数>`
4. **結果解釈** → 出力されたテーブル・サマリーを読み取る

## 機能選択テーブル

| 目的 | スクリプト | 使用例 |
|------|-----------|--------|
| 株価を調べる | `get_price.py` | `python3 scripts/get_price.py 7203.T` |
| 企業情報・バリュエーション | `get_company_info.py` | `python3 scripts/get_company_info.py 6758.T` |
| 財務諸表を見る | `get_financials.py` | `python3 scripts/get_financials.py 7203.T --type balance` |
| 配当履歴を確認 | `get_dividends.py` | `python3 scripts/get_dividends.py 8306.T` |
| 指数の推移を見る | `get_index.py` | `python3 scripts/get_index.py 日経平均` |
| 複数銘柄を比較 | `compare_stocks.py` | `python3 scripts/compare_stocks.py 7203.T 7267.T 7269.T` |

## ティッカー記法の基本

- 日本株: `{証券コード}.T`（例: `7203.T`）
- 数字のみ入力すると自動で`.T`を付与（例: `7203` → `7203.T`）
- 指数: `^N225`（日経平均）、TOPIX は `1306.T`（ETF代替）
- 詳細は `references/ticker_guide.md` を参照

## 各スクリプトの使用例

### 株価取得（get_price.py）

```bash
# 直近1ヶ月の日次株価（デフォルト）
python3 scripts/get_price.py 7203.T

# 1年間の週次データ
python3 scripts/get_price.py 7203.T --period 1y --interval 1wk

# 日付範囲指定
python3 scripts/get_price.py 7203.T --start 2025-01-01 --end 2025-12-31

# 証券コードのみでもOK
python3 scripts/get_price.py 7203
```

### 企業情報（get_company_info.py）

```bash
# 企業概要・バリュエーション一括表示
python3 scripts/get_company_info.py 6758.T
```

出力: 企業概要（セクター、業種、時価総額）+ 株価情報 + バリュエーション（PER, PBR, 配当利回り, EPS, ROE, 52週高値/安値）

### 財務諸表（get_financials.py）

```bash
# 損益計算書（デフォルト）
python3 scripts/get_financials.py 7203.T

# 貸借対照表
python3 scripts/get_financials.py 7203.T --type balance

# キャッシュフロー計算書
python3 scripts/get_financials.py 7203.T --type cashflow

# 四半期データ
python3 scripts/get_financials.py 7203.T --quarterly
```

### 配当情報（get_dividends.py）

```bash
python3 scripts/get_dividends.py 8306.T
```

出力: 配当履歴テーブル + サマリー（直近配当額、年間配当、配当利回り）

### 指数（get_index.py）

```bash
# 日経平均（エイリアス使用可）
python3 scripts/get_index.py 日経平均
python3 scripts/get_index.py ^N225

# TOPIX（ETF代替）
python3 scripts/get_index.py TOPIX

# 期間・間隔指定
python3 scripts/get_index.py 日経平均 --period 1y --interval 1wk
```

利用可能なエイリアス: 日経平均, 日経225, nikkei, TOPIX, マザーズ, グロース, ダウ, S&P500, NASDAQ, REIT

### 銘柄比較（compare_stocks.py）

```bash
# デフォルト指標で比較
python3 scripts/compare_stocks.py 7203.T 7267.T 7269.T

# 指標を指定
python3 scripts/compare_stocks.py 7203.T 6758.T --metrics price,per,pbr,roe,market_cap
```

利用可能な指標: `price`, `per`, `forward_per`, `pbr`, `eps`, `dividend_yield`, `roe`, `market_cap`, `52w_high`, `52w_low`, `volume`

## スクリーニング

銘柄リストを使った条件スクリーニングはPythonコードで実行する。
パターン別のコード例とテンプレートは `references/screening_patterns.md` を参照。

対応パターン:
- 高配当スクリーニング（配当利回り > X%）
- 割安株（PER < X, PBR < Y）
- 出来高急増（N日平均のX倍以上）
- 移動平均乖離（25日MAからX%以上乖離）
- 時価総額フィルタ

銘柄リスト:
- `assets/stock_lists/nikkei225.txt` — 日経225採用銘柄
- `assets/stock_lists/topix100.txt` — TOPIX100構成銘柄

## 参照ファイル一覧

| ファイル | 内容 |
|----------|------|
| `references/ticker_guide.md` | ティッカー記法・主要指数・セクターETF一覧 |
| `references/screening_patterns.md` | スクリーニングパターン集・コードテンプレート |
| `assets/stock_lists/nikkei225.txt` | 日経225採用銘柄リスト |
| `assets/stock_lists/topix100.txt` | TOPIX100構成銘柄リスト |
