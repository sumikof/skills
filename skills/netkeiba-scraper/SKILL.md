---
name: netkeiba-scraper
description: "netkeibaをスクレイピングして日本競馬の情報を取得するスキル。Use when: (1) 競馬のレース出走表を調べる, (2) 出走馬の情報を取得する, (3) 馬の過去成績・戦績を確認する, (4) 騎手・調教師の情報を調べる, (5) レース結果を取得する, (6) 馬の血統情報を調べる, (7) 特定日程の開催レース一覧を取得する. Keywords: netkeiba, 競馬, horse racing, 出走表, race entry, 出走馬, racehorse, 馬情報, horse info, 過去成績, race history, 騎手, jockey, 調教師, trainer, レース結果, race result, 血統, pedigree, JRA, 中央競馬, 地方競馬, 開催, race schedule, オッズ, odds, 斤量, weight, 馬体重, horse weight"
---

# netkeiba-scraper

netkeibaをスクレイピングして日本競馬の出走情報・馬情報・レース結果を取得するスキル。

## 必須環境

```bash
pip install requests beautifulsoup4 lxml pandas
```

## ワークフロー

1. **目的を確認** → 下表から目的に合うスクリプトを選ぶ
2. **IDを特定** → レースID・馬IDの形式は `references/id_format.md` を参照
3. **スクリプト実行** → `python3 scripts/<スクリプト名>.py <引数>`
4. **結果確認** → 出力されたテーブル・JSON を読み取る

## 機能選択テーブル

| 目的 | スクリプト | 使用例 |
|------|-----------|--------|
| 特定日の開催レース一覧 | `get_race_list.py` | `python3 scripts/get_race_list.py 20250601` |
| レースの出走表を取得 | `get_race_entry.py` | `python3 scripts/get_race_entry.py 202506010101` |
| 馬の基本情報を取得 | `get_horse_info.py` | `python3 scripts/get_horse_info.py 2020104308` |
| 馬の過去成績を取得 | `get_horse_results.py` | `python3 scripts/get_horse_results.py 2020104308` |
| レース結果を取得 | `get_race_result.py` | `python3 scripts/get_race_result.py 202506010101` |

## ID形式の基本

- **レースID**: `YYYYMMDDVVRR`（例: `202506010101` = 2025年6月1日・東京1回1日目・1R）
- **競馬場コード**: `01`=札幌 `02`=函館 `03`=福島 `04`=新潟 `05`=東京 `06`=中山 `07`=中京 `08`=京都 `09`=阪神 `10`=小倉
- **馬ID**: 10桁の数字（netkeibaのURLから取得）
- 詳細は `references/id_format.md` を参照

## 各スクリプトの使用例

### 特定日の開催レース一覧（get_race_list.py）

```bash
# 2025年6月1日の全開催レース
python3 scripts/get_race_list.py 20250601

# 特定競馬場のみ（東京=05）
python3 scripts/get_race_list.py 20250601 --venue 05
```

出力: 競馬場・レース番号・レース名・距離・条件の一覧

### レース出走表（get_race_entry.py）

```bash
# レースIDで出走表を取得
python3 scripts/get_race_entry.py 202506010101

# CSV出力
python3 scripts/get_race_entry.py 202506010101 --format csv
```

出力: 枠番・馬番・馬名・性齢・斤量・騎手・調教師・馬体重・オッズ

### 馬の基本情報（get_horse_info.py）

```bash
# 馬IDで基本情報を取得
python3 scripts/get_horse_info.py 2020104308

# 血統情報も含めて表示
python3 scripts/get_horse_info.py 2020104308 --pedigree
```

出力: 馬名・生年月日・性別・毛色・父・母・馬主・生産者・調教師

### 馬の過去成績（get_horse_results.py）

```bash
# 全過去成績
python3 scripts/get_horse_results.py 2020104308

# 直近N戦のみ
python3 scripts/get_horse_results.py 2020104308 --last 5

# CSV保存
python3 scripts/get_horse_results.py 2020104308 --output results.csv
```

出力: 日付・競馬場・レース名・距離・着順・タイム・騎手・賞金

### レース結果（get_race_result.py）

```bash
# レース結果を取得
python3 scripts/get_race_result.py 202506010101
```

出力: 着順・馬番・馬名・タイム・着差・人気・単勝オッズ・騎手・馬体重

## 注意事項

- netkeibaへのアクセスは**適切なインターバル（1秒以上）**を設けること
- User-Agentを設定してリクエストを送ること
- 取得したデータは**個人利用の範囲内**で使用すること
- ページ構造変更によりパーシングが失敗することがある
- 詳細は `references/scraping_notes.md` を参照

## 参照ファイル一覧

| ファイル | 内容 |
|----------|------|
| `references/id_format.md` | レースID・馬IDの形式と競馬場コード一覧 |
| `references/scraping_notes.md` | スクレイピング上の注意点・ページ構造の説明 |
