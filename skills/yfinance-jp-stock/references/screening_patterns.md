# スクリーニングパターン集

## 基本パターン

スクリーニングの基本フロー:
1. 銘柄リストを読み込む
2. 各銘柄のデータを取得
3. 条件でフィルタ
4. 結果を表示

## 共通コードテンプレート

```python
import pandas as pd
import yfinance as yf

# 銘柄リストを読み込む
def load_tickers(filepath):
    """stock_listsファイルからティッカーを読み込む"""
    tickers = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                tickers.append(line)
    return tickers

# バッチでデータ取得（推奨: yf.download()を使用）
def get_batch_info(tickers):
    """複数銘柄の情報を一括取得"""
    results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            results.append({
                "ticker": ticker,
                "name": info.get("shortName", ticker),
                "price": info.get("regularMarketPrice"),
                "per": info.get("trailingPE"),
                "pbr": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "roe": info.get("returnOnEquity"),
                "market_cap": info.get("marketCap"),
                "volume": info.get("volume"),
            })
        except Exception:
            continue
    return pd.DataFrame(results)

# 銘柄リストのパス（スキルディレクトリからの相対パス）
# tickers = load_tickers("assets/stock_lists/nikkei225.txt")
# tickers = load_tickers("assets/stock_lists/topix100.txt")
```

## パターン別コード例

### 1. 高配当スクリーニング

配当利回りが指定値以上の銘柄を抽出。

```python
tickers = load_tickers("assets/stock_lists/nikkei225.txt")
df = get_batch_info(tickers)

# 配当利回り > 3%
threshold = 0.03
high_div = df[df["dividend_yield"] > threshold].copy()
high_div["配当利回り"] = high_div["dividend_yield"].map(lambda x: f"{x*100:.2f}%")
high_div = high_div.sort_values("dividend_yield", ascending=False)

print(high_div[["ticker", "name", "配当利回り", "per", "pbr"]].to_string(index=False))
```

### 2. 割安株スクリーニング

PER・PBRが基準値以下の銘柄を抽出。

```python
df = get_batch_info(tickers)

# PER < 15 かつ PBR < 1.0
value = df[(df["per"] < 15) & (df["per"] > 0) & (df["pbr"] < 1.0)].copy()
value = value.sort_values("pbr")

print(value[["ticker", "name", "per", "pbr", "dividend_yield"]].to_string(index=False))
```

### 3. 出来高急増スクリーニング

直近の出来高が20日平均のN倍以上の銘柄。

```python
tickers = load_tickers("assets/stock_lists/nikkei225.txt")

# バッチで株価データをダウンロード（推奨）
data = yf.download(tickers, period="1mo", interval="1d", group_by="ticker", threads=True)

results = []
for ticker in tickers:
    try:
        vol = data[ticker]["Volume"].dropna()
        if len(vol) < 5:
            continue
        avg_vol = vol[:-1].mean()  # 直近を除く平均
        latest_vol = vol.iloc[-1]
        ratio = latest_vol / avg_vol if avg_vol > 0 else 0
        if ratio >= 2.0:  # 2倍以上
            results.append({
                "ticker": ticker,
                "latest_volume": int(latest_vol),
                "avg_volume": int(avg_vol),
                "ratio": f"{ratio:.1f}x",
            })
    except Exception:
        continue

result_df = pd.DataFrame(results).sort_values("ratio", ascending=False)
print(result_df.to_string(index=False))
```

### 4. 移動平均乖離スクリーニング

25日移動平均線からの乖離率でフィルタ。

```python
tickers = load_tickers("assets/stock_lists/nikkei225.txt")
data = yf.download(tickers, period="2mo", interval="1d", group_by="ticker", threads=True)

results = []
for ticker in tickers:
    try:
        close = data[ticker]["Close"].dropna()
        if len(close) < 25:
            continue
        ma25 = close.rolling(25).mean().iloc[-1]
        latest = close.iloc[-1]
        deviation = (latest / ma25 - 1) * 100
        if abs(deviation) >= 5.0:  # 5%以上乖離
            results.append({
                "ticker": ticker,
                "price": f"{latest:,.1f}",
                "ma25": f"{ma25:,.1f}",
                "乖離率": f"{deviation:+.2f}%",
            })
    except Exception:
        continue

result_df = pd.DataFrame(results)
result_df["乖離率_num"] = result_df["乖離率"].str.replace("%", "").astype(float)
result_df = result_df.sort_values("乖離率_num")
print(result_df[["ticker", "price", "ma25", "乖離率"]].to_string(index=False))
```

### 5. 時価総額フィルタ

時価総額で銘柄を絞り込む。

```python
df = get_batch_info(tickers)

# 時価総額1000億円以上5000億円以下（中型株）
min_cap = 1000 * 1e8  # 1000億円
max_cap = 5000 * 1e8  # 5000億円
mid_cap = df[(df["market_cap"] >= min_cap) & (df["market_cap"] <= max_cap)].copy()
mid_cap["時価総額（億円）"] = mid_cap["market_cap"].map(lambda x: f"{x/1e8:,.0f}")
mid_cap = mid_cap.sort_values("market_cap", ascending=False)

print(mid_cap[["ticker", "name", "時価総額（億円）", "per", "pbr"]].to_string(index=False))
```

## レート制限の注意事項

- yfinanceはYahoo Finance APIを利用しており、短時間の大量リクエストはレート制限を受ける可能性がある
- **推奨**: `yf.download()` でバッチ取得（`threads=True`で並列化）
- 全225銘柄の`.info`を個別取得すると数分かかる場合がある
- 大量取得時は`time.sleep(0.5)`等で間隔を空けることを推奨
- エラーが発生した場合は`try/except`で個別にスキップする
