# スクレイピング上の注意事項

## 基本方針

- **アクセス間隔**: 最低1秒以上のインターバルを設けること（`_scraper.py` の `fetch()` にデフォルト設定済み）
- **User-Agent**: ブラウザのUser-Agentを設定してリクエストを送ること（設定済み）
- **利用規約**: 取得データは個人利用の範囲内で使用すること
- **負荷軽減**: 短時間に大量のリクエストを送らないこと

## netkeibaのページ構造

### 出走表ページ
- URL: `https://race.netkeiba.com/race/shutuba.html?race_id={race_id}`
- テーブルクラス: `Shutuba_Table`
- 主要クラス:
  - `WakuNum` / `Waku` - 枠番
  - `HorseNum` / `Umaban` - 馬番
  - `HorseName` - 馬名（`/horse/{horse_id}/` へのリンク）
  - `Jockey` - 騎手（`/jockey/{jockey_id}/` へのリンク）
  - `Trainer` - 調教師
  - `Weight` - 斤量
  - `HorseWeight` / `Weight_Horses` - 馬体重

### レース結果ページ
- URL: `https://db.netkeiba.com/race/{race_id}/`
- テーブルクラス: `race_table_01`
- 列順（一般的）: 着順・枠番・馬番・馬名・性齢・斤量・騎手・タイム・着差・人気・オッズ・後3F・通過順・調教師・馬体重・賞金

### 馬情報ページ
- URL: `https://db.netkeiba.com/horse/{horse_id}/`
- プロフィールテーブルクラス: `db_prof_table`
- 血統テーブルクラス: `blood_table`

### 馬成績ページ
- URL: `https://db.netkeiba.com/horse/result/{horse_id}/`
- テーブルクラス: `db_h_race_results`

## よくあるエラーと対処法

### スクレイピング失敗（テーブルが見つからない）

netkeibaはページレイアウトを変更することがある。

対処法:
1. ブラウザで対象URLを開き、デベロッパーツールでHTMLを確認する
2. `_scraper.py` の `fetch()` でスープを取得して `soup.prettify()` で構造を確認する
3. テーブルのクラス名やIDを更新する

### 文字化け

`_scraper.py` では `resp.encoding = resp.apparent_encoding` で自動検出している。
それでも文字化けする場合は明示的に `encoding='euc-jp'` や `encoding='utf-8'` を試す。

### 接続エラー・タイムアウト

- アクセス間隔を2〜3秒に増やす
- `fetch()` の `timeout` パラメータを増やす（デフォルト15秒）
- ネットワーク状況を確認する

## デバッグ方法

```python
# _scraper.py の fetch() を使って生HTMLを確認
from _scraper import fetch
soup = fetch("https://race.netkeiba.com/race/shutuba.html?race_id=202506010101")
print(soup.prettify()[:3000])  # 最初の3000文字を表示

# テーブル一覧を確認
for i, t in enumerate(soup.find_all("table")):
    print(f"Table {i}: class={t.get('class')}, id={t.get('id')}")
    headers = [th.get_text(strip=True) for th in t.find_all("th")[:5]]
    print(f"  Headers: {headers}")
```

## 参考リンク

- netkeiba: https://www.netkeiba.com/
- netkeiba DB: https://db.netkeiba.com/
- JRA公式: https://www.jra.go.jp/
