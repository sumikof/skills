# ヒアリング→プレゼン引き渡しフォーマット Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `presentation-hearing` が出力する YAML ヒアリング結果を `html-presentation` がそのまま読み込んでスライド生成できるよう、共有の入力契約を定義し両スキルを配線する。

**Architecture:** 消費者である `html-presentation` 側に入力契約の正典 `references/input-format.md`(YAML スキーマ・3層構造への対応・pattern 正典キー表)を新設。`html-presentation/SKILL.md` は「構造化 YAML を受け取ったら契約に従う、無ければ従来どおり自由形式」という非破壊の分岐を追加。`presentation-hearing/SKILL.md` は出力を JSON から YAML に差し替え、pattern 値を正典キーに統一する。

**Tech Stack:** Markdown スキルファイル(日本語)。コードやパーサは無し。検証は grep とファイル読みで行う。ビルド/テストランナー無し。

**Spec:** `docs/superpowers/specs/2026-07-15-hearing-to-presentation-handoff-design.md`

**Note:** これは skill(ドキュメント)編集タスク。従来の pytest 型 TDD は適用不可なため、各タスクの「検証」は grep による整合性チェックに読み替える。作業ブランチ `feat/hearing-presentation-handoff` で実施(spec コミット済み)。

---

### Task 1: 入力契約の正典ファイルを新設

**Files:**
- Create: `skills/html-presentation/references/input-format.md`

- [ ] **Step 1: ファイルを作成し、以下の全内容を書き込む**

````markdown
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
````

- [ ] **Step 2: pattern キーが slide-patterns.md の11型と過不足なく対応することを検証**

Run: `grep -nE '^## [0-9]+\. ' skills/html-presentation/references/slide-patterns.md`
Expected: 11 行(1.表紙 〜 11.課題・施策対応表 / 考察)が出力され、input-format.md の正典キー表の11型(`おまかせ` を除く)と1対1で対応していること。

- [ ] **Step 3: コミット**

```bash
git add skills/html-presentation/references/input-format.md
git commit -m "$(cat <<'EOF'
html-presentation: 構造化入力契約(input-format.md)を追加

ヒアリング出力YAMLを受理する任意の入力形式を正典化。
YAMLスキーマ・3層構造への対応・pattern正典キー表を定義。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SjSyorrtzsrXQULZhkqvxt
EOF
)"
```

---

### Task 2: html-presentation/SKILL.md を配線(非破壊の分岐追加)

**Files:**
- Modify: `skills/html-presentation/SKILL.md`(構成ファイル一覧 + ワークフロー2)

- [ ] **Step 1: 構成ファイル一覧に input-format.md を追記**

`references/slide-patterns.md` の行の直後に追記する。置換対象(現行):

```
└── references/slide-patterns.md  # 定番11パターンのHTMLスケルトン集
```

置換後:

```
├── references/slide-patterns.md  # 定番11パターンのHTMLスケルトン集
└── references/input-format.md    # 任意で受理する構造化入力(YAML)の契約
```

- [ ] **Step 2: ワークフロー「2. 入力確認」に構造化入力の分岐を追加**

現行の見出し「### 2. 入力確認」段落の**冒頭**に、以下の一文を段落として挿入する
(既存の「渡されたプレゼン内容を確認する。**入力にない事実…**」の直前)。

挿入する文:

```
渡された入力が **`.presentation.yaml`(または同等の構造化内容)** の場合は、`references/input-format.md` に従い各フィールドを3層構造へマップする(`presentation-hearing` 経由の入力がこれにあたる)。構造化入力が無ければ以降のとおり自由形式の内容から設計する。**この分岐は追加的で、単独呼び出し時の挙動は変えない。**
```

- [ ] **Step 3: 検証 — 追記が入り、既存の自由形式パスが保持されていること**

Run: `grep -n "input-format\|構造化\|入力にない事実" skills/html-presentation/SKILL.md`
Expected: input-format.md への参照(構成一覧＋ワークフロー2)と、既存の「入力にない事実・数値・文言を創作しない」の記述が**両方**残っている(非破壊)。

- [ ] **Step 4: コミット**

```bash
git add skills/html-presentation/SKILL.md
git commit -m "$(cat <<'EOF'
html-presentation: 構造化YAML入力を受理する分岐を追記(非破壊)

.presentation.yaml を受け取ったら input-format.md に従いマップ。
無ければ従来どおり自由形式。単独呼び出しの挙動は不変。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SjSyorrtzsrXQULZhkqvxt
EOF
)"
```

---

### Task 3: presentation-hearing/SKILL.md の出力を YAML に差し替え

**Files:**
- Modify: `skills/presentation-hearing/SKILL.md`(Stage 4・出力仕様・pattern 値・description)

- [ ] **Step 0: 本文冒頭・フロー図・Stage 4 見出しの "JSON" 表記を YAML に更新**

3箇所を置換する。

置換対象A(intro 段落, 現行):

```
ない内容を**ヒアリングで引き出し、ユーザが承認した文言だけ**でプレゼン入力ドキュメント
(JSON)を組み立てることである。
```

置換後A:

```
ない内容を**ヒアリングで引き出し、ユーザが承認した文言だけ**でプレゼン入力ドキュメント
(YAML)を組み立てることである。
```

置換対象B(全体フロー図, 現行):

```
Stage 4  JSON保存 → ユーザ確認 → html-presentation でスライド生成
```

置換後B:

```
Stage 4  YAML保存 → ユーザ確認 → html-presentation でスライド生成
```

置換対象C(Stage 4 見出し, 現行):

```
## Stage 4: JSON化・確認・スライド生成
```

置換後C:

```
## Stage 4: YAML化・確認・スライド生成
```

置換対象D(Stage 3 の注意書き, 現行):

```
と言った箇所は、ドラフト文言を提示して承認を得る(承認前の文言をJSONに入れない)
```

置換後D:

```
と言った箇所は、ドラフト文言を提示して承認を得る(承認前の文言をYAMLに入れない)
```

- [ ] **Step 1: Stage 4 の保存ファイル名を YAML に変更**

置換対象(現行, 82-84行付近):

```
1. 下記仕様のJSONを組み立て、作業ディレクトリに `<資料名スラッグ>.presentation.json`
   として保存する
```

置換後:

```
1. 下記仕様のYAMLを組み立て、作業ディレクトリに `<資料名スラッグ>.presentation.yaml`
   として保存する
```

- [ ] **Step 2: Stage 4 の引き渡し記述を YAML 前提に更新**

置換対象(現行, 87-89行付近):

```
   生成する(JSONの `pattern` はスライド型の指定として、`content` は入力原稿として
   そのまま渡る)。html-presentation 側の確認(マッピング提示)は済んでいる内容なので
```

置換後:

```
   生成する(YAMLの `pattern` はスライド型の指定として、`content` は入力原稿として
   そのまま渡る。html-presentation は `references/input-format.md` の契約で読む)。
   html-presentation 側の確認(マッピング提示)は済んでいる内容なので
```

- [ ] **Step 3: 「## 出力JSON仕様」セクション全体を YAML 仕様に差し替え**

見出し「## 出力JSON仕様」から、その下の ```json コードブロックと直後の箇条書き3項目
(``- `pages[].no` …`` / ``- `meta` の3要素…`` / ``- `purpose` / `key_message`…``)までを、
以下で丸ごと置換する:

````markdown
## 出力YAML仕様

出力形式は `html-presentation/references/input-format.md` の契約に準拠する。

```yaml
title: 地域中小企業のDX推進実態調査 報告書
meta:
  audience: 経済産業省 御中
  author: ○○総合研究所
  date: 2026年7月
purpose: 調査結果を報告し、次年度施策の方向性について合意を得る
key_message: DX停滞の主因は人材不足であり、伴走支援型の施策が必要
pages:
  - no: 1
    pattern: 表紙
    title: 地域中小企業のDX推進実態調査 報告書
    content: |
      副題: 令和8年度○○委託事業
  - no: 2
    pattern: 目的・背景
    title: 調査の背景と目的
    message: 補助金施策にもかかわらず中小企業のDXは停滞している
    content: |
      背景: 補助金施策にもかかわらず中小企業のDXは停滞している。
      目的: 停滞要因の構造把握と次年度施策の立案。
    source: 令和7年度○○調査
```

- `pages[].no` / `title` / `content` / `pattern` は必須。`content` はそのページに
  載せる内容の文章・箇条書き(ブロックスカラー `|` で複数行)。ヒアリングで確認の
  取れた文言のみを書く
- `chapter`(章扉/上部ラベル)/ `message`(キーメッセージ行)/ `source`(出典)は任意。
  ヒアリングで確認が取れた場合のみ付ける(無ければ省略。創作しない)
- `meta` の3要素は表紙用。未確認なら値を `●●●` にする
- `purpose` / `key_message` はスライドに直接載らなくてもよい。html-presentation が
  トーンや強調(`<strong>`)を判断する材料になる
- `pattern` の値は下記「スライド型(pattern)の値」= input-format.md の正典キーを使う
````

- [ ] **Step 4: 「### スライド型(pattern)の値」の正典キー参照を明記**

置換対象(現行, 128-129行付近の pattern 値の列挙):

```
`表紙` `目的・背景` `タスク分解` `矢羽スケジュール` `論点整理` `スコープ定義`
`分析サマリー` `分析詳細` `2軸マトリックス` `課題整理` `対応表・考察` `おまかせ`
```

置換後(値は現行と同一、参照先だけ明記):

```
`表紙` `目的・背景` `タスク分解` `矢羽スケジュール` `論点整理` `スコープ定義`
`分析サマリー` `分析詳細` `2軸マトリックス` `課題整理` `対応表・考察` `おまかせ`

これらは html-presentation の `references/input-format.md` の**正典キー**であり、各型の
中身は同スキルの `references/slide-patterns.md` を参照。
```

- [ ] **Step 5: description の "JSONドキュメント" を "YAMLドキュメント" に更新**

置換対象(現行 frontmatter, 3行目):

```
スライド型をJSONドキュメントにまとめ、html-presentationスキルへ引き渡すスキル。
```

置換後:

```
スライド型をYAMLドキュメントにまとめ、html-presentationスキルへ引き渡すスキル。
```

- [ ] **Step 6: 検証 — JSON 記述が残っていないこと & pattern 値の一致**

Run: `grep -ni "json" skills/presentation-hearing/SKILL.md`
Expected: 出力なし(JSON への言及が全て YAML に置換済み)。

Run: `grep -c "presentation.yaml" skills/presentation-hearing/SKILL.md`
Expected: 2 以上(Stage 4 の保存記述)。

- [ ] **Step 7: コミット**

```bash
git add skills/presentation-hearing/SKILL.md
git commit -m "$(cat <<'EOF'
presentation-hearing: 出力をJSONからYAMLに差し替え

.presentation.yaml で出力しinput-format.md契約に準拠。
任意フィールドchapter/message/sourceを追加、pattern正典キーを明記。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SjSyorrtzsrXQULZhkqvxt
EOF
)"
```

---

### Task 4: 全体整合性の最終検証

**Files:**
- 読み取りのみ(新規/変更なし)

- [ ] **Step 1: pattern 語彙が両スキルで一致することを検証**

Run: `grep -oE '\x60(表紙|目的・背景|タスク分解|矢羽スケジュール|論点整理|スコープ定義|分析サマリー|分析詳細|2軸マトリックス|課題整理|対応表・考察|おまかせ)\x60' skills/presentation-hearing/SKILL.md skills/html-presentation/references/input-format.md | sort -u`
Expected: 両ファイルから同じ12キー(11型＋おまかせ)が抽出され、正典表と一致。ズレていた旧語彙(`分析結果サマリー` を pattern 値として使う等)が presentation-hearing 側に残っていないこと。

- [ ] **Step 2: html-presentation の非破壊性を確認**

Run: `git diff main -- skills/html-presentation/SKILL.md`
Expected: 差分は「構成ファイル一覧への1行追加」と「ワークフロー2冒頭への分岐段落追加」のみ。既存のワークフロー各ステップ・よくある失敗表などが削除されていないこと。

- [ ] **Step 3: spec の変更対象・検証項目を1つずつ確認**

`docs/superpowers/specs/2026-07-15-hearing-to-presentation-handoff-design.md` の「変更対象」
(3項目)と「検証」(4項目)を読み、各項目に対応する実装/検証がこのプランで満たされて
いることを目視確認する。ギャップがあればタスクを追加。

- [ ] **Step 4: 完了コミット(検証ログ)**

検証で追加修正が発生した場合のみコミット。修正が無ければ本ステップはスキップし、
Task 1-3 のコミットで完了とする。

```bash
git status   # 変更が無ければ clean
```
