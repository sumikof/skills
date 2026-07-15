# presentation-hearing → html-presentation 引き渡しフォーマット設計

日付: 2026-07-15

## 目的

`presentation-hearing` スキルが出力するヒアリング結果ドキュメントを、`html-presentation`
スキルが**そのまま読み込んでスライド生成できる**ようにする。ドキュメントは構造化された
最適フォーマットで出力する。

## 背景 / 現状の課題

- `presentation-hearing` は既に `<スラッグ>.presentation.json` を出力する仕様を持つ
  (`title` / `meta` / `purpose` / `key_message` / `pages[].{no,pattern,title,content}`)。
- しかし `html-presentation` 側には**この出力をどう読むかの契約が一切ない**。
  ワークフローの「入力確認」は自由形式の内容を前提とし、フィールドの対応が未定義。
- `pattern` の語彙が両スキルで不一致(例: ヒアリング側 `タスク分解` / パターン集
  `調査内容・タスク分解`、`分析サマリー`↔`分析結果サマリー`、`対応表・考察`↔
  `課題・施策対応表 / 考察`)。
- 現行 JSON は複数行 `content` を `\n` エスケープで表現するため、レビュー時の人間の
  編集が困難でコメントも書けない。

## 制約 / 前提

- **`html-presentation` はヒアリングなしでも単独で呼ばれる**。構造化入力は必須ではなく
  **追加的にサポートする一形態**。単独呼び出し時の既存の自由形式パスと挙動は非破壊で維持する。
- 中間ドキュメントの消費者は「スキル実行中の Claude」と「レビューする人間」であり、
  厳密なパーサではない。パーサ実装は不要。
- スキルはすべて日本語(CLAUDE.md 準拠)。skill パッケージ化は行わない。

## 決定事項

### 1. フォーマット: YAML

出力ファイルを `<スラッグ>.presentation.yaml` とする。

理由: ブロックスカラー `|` で複数行 `content`(散文＋箇条書き)をエスケープ無しに書ける。
コメント可・構造明確・機械可読で、レビュー時の人間編集も容易。JSON の `\n` 問題を解消する。

### 2. 契約の正典は html-presentation 側に置く

新規 `html-presentation/references/input-format.md` に入力契約の正典(YAML スキーマ、
各フィールド → 3層構造への対応、pattern 正典キー表、`slide-patterns.md` へのリンク)を置く。

理由: パターン定義(`slide-patterns.md`)が既に html-presentation にあり、**消費者側が
形式の権威を持つ**のが自然。ヒアリング側は「この契約に準拠して出力する」と参照する。

### 3. YAML スキーマ

```yaml
title:  資料タイトル                 # 必須
meta:                                # 表紙用。未確認要素は値を ●●● にする
  audience: 提出先
  author:   作成者
  date:     日付
purpose:      …                      # 任意。トーン判断材料(スライドに直接は載らなくてよい)
key_message:  …                      # 任意。強調(<strong>)判断材料
pages:
  - no: 1                            # 必須
    pattern: 表紙                     # 必須。正典キー(下表)
    title:   …                       # 必須
    chapter: …                       # 任意。章扉/上部ラベル(3層構造の最上位)
    message: …                       # 任意。キーメッセージ行(3層構造の中段)
    content: |                       # 必須。ボディ(散文＋ "- " 箇条書き)
      背景: …
      - 論点1 …
    source:  …                       # 任意。出典(.source)
```

- 現行 JSON に対する唯一の機能拡張は **任意フィールド `chapter` / `message` / `source`**。
  html-presentation の3層構造(チャプター / タイトル・メッセージ / ボディ)へ推測なしで
  流し込めるようにするため。付与はヒアリングで確認が取れた場合のみ(創作しない原則を維持)。
- それ以外のフィールドは現行 JSON と1対1対応。

### 4. pattern 正典キー表(語彙統一)

input-format.md に以下を正典として置き、両スキルをこれに揃える。

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
| `おまかせ` | html-presentation が content から適切な型を選ぶ |

## 変更対象

1. **新規** `html-presentation/references/input-format.md` — 上記スキーマ・マッピング・
   正典キー表。「html-presentation が受理する構造化入力形式(任意)」として記述。
2. **`html-presentation/SKILL.md`** — 構成ファイル一覧に input-format.md を追記。
   ワークフロー2「入力確認」に分岐を追加: 「`.presentation.yaml`(構造化入力)を
   受け取った場合は input-format.md に従いフィールドを3層構造へマップ。無ければ従来どおり
   自由形式の内容から設計」。非破壊・追加的である旨を明記。
3. **`presentation-hearing/SKILL.md`** — 出力仕様を JSON→YAML に差し替え
   (`## 出力YAML仕様`)。拡張子 `.presentation.yaml`。任意フィールド `chapter`/`message`/
   `source` を追記。pattern 値は「input-format.md の正典キー準拠」と明記。Stage 4 の
   保存・引き渡し記述を YAML に更新。

## 非対象 (YAGNI)

- 発表者ノート等の新フィールド。
- YAML パーサの実装(Claude が読むため不要)。
- 複数デザイン対応やエンジン改修。
- examples ディレクトリへの新サンプル追加(必要になれば別途)。

## 検証

- input-format.md の pattern 正典キーが `slide-patterns.md` の11パターンと過不足なく対応。
- presentation-hearing の pattern 値一覧が正典キー表と一致。
- html-presentation の単独(YAML なし)フローの記述が従来から変わっていない(非破壊)。
- YAML スキーマ例が両 SKILL.md 間で矛盾しない。
