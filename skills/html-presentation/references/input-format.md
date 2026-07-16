# 入力形式 (input-format) — html-presentation が受理する構造化入力(任意)

html-presentation は**自由形式のプレゼン内容でも動作する**。本ファイルは、より効果的な
スライド生成のために**任意で**受理する構造化入力(YAML)の仕様である。`presentation-hearing`
スキルはこの契約に準拠した `<スラッグ>.presentation.yaml` を出力する。

この形式で入力が渡された場合、html-presentation は下記フィールドを3層構造
(チャプター / タイトル・メッセージ / ボディ)へマップしてスライドを設計する。渡されない
場合は従来どおり自由形式の内容から設計してよい(本ファイルは強制ではない)。

## YAML スキーマ

```yaml
title:  資料タイトル                 # 必須。カバー/各スライドのタイトル基準
meta:                                # 表紙(.cover)用。未確認の要素は値を ●●● にする
  audience: 提出先
  author:   作成者
  date:     日付
purpose:      …                      # 任意。トーン判断材料(スライドに直接は載らなくてよい)
key_message:  …                      # 任意。強調(<strong>)判断材料
pages:                               # 1要素=1スライド。配列順が表示順
  - no: 1                            # 必須。スライド番号(.slide-no)
    pattern: 表紙                     # 必須。下の正典キー表から選ぶ
    title:   …                       # 必須。スライドタイトル(.slide-title)
    chapter: …                       # 任意。章扉/上部ラベル(.chapter, 3層の最上位)
    message: …                       # 任意。キーメッセージ行(.message, 3層の中段)
    content: |                       # 必須。ボディ(.slide-body)。散文＋ "- " 箇条書き
      背景: …
      - 論点1 …
    source:  …                       # 任意。出典(.source)
```

## フィールド → 3層構造の対応

| YAML フィールド | スライド上の対応 | 備考 |
|---|---|---|
| `title`(トップ) | 資料タイトル / 表紙 | base.html の `===TITLE===` |
| `meta.{audience,author,date}` | 表紙(.cover)の提出先・作成者・日付 | 未確認は ●●● |
| `pages[].chapter` | `.chapter`(3層の最上位) | 任意。無ければ省略 |
| `pages[].title` | `.slide-title` | 必須 |
| `pages[].message` | `.message`(タイトル罫線直下の1行) | 任意。枠囲みにしない |
| `pages[].content` | `.slide-body` | 必須。要約・箇条書き化は可、創作は不可 |
| `pages[].source` | `.source`(脚注/出典) | 任意 |
| `pages[].pattern` | 使用するスライド型 | 正典キー表を参照 |

`purpose` / `key_message` はスライドに直接載せず、トーンや `<strong>` 強調の判断材料に使う。

## pattern 正典キー表

`pages[].pattern` の値は下表の**正典キー**を使う。各キーは `slide-patterns.md` の型に対応する。

| 正典キー | slide-patterns.md の対応 |
|---|---|
| `表紙` | 1. 表紙 |
| `目的・背景` | 2. 目的・背景 |
| `タスク分解` | 3. 調査内容・タスク分解 |
| `矢羽スケジュール` | 4. 矢羽スケジュール |
| `論点整理` | 5. 論点整理 |
| `スコープ定義` | 6. スコープ定義 |
| `分析サマリー` | 7. 分析結果サマリー |
| `分析詳細` | 8. 分析詳細 |
| `2軸マトリックス` | 9. 2軸マトリックス |
| `課題整理` | 10. 課題整理 |
| `対応表・考察` | 11. 課題・施策対応表 / 考察 |
| `おまかせ` | content から適切な型を html-presentation が選ぶ |

## 取り扱いの原則

- **創作しない**: `content` にない事実・数値を足さない。`chapter`/`message`/`source` は
  入力に無ければ付けない(省略する)。`meta` の未確認要素のみ ●●● プレースホルダ可。
- **ヒアリング済みの合図**: presentation-hearing 経由の入力はマッピング確認が済んでいる。
  「一気通貫で生成してよい」と指示された場合はマッピング提示と同時に生成へ進む。
- YAML パーサは不要。Claude がファイルを読んで解釈する。
