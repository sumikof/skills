---
name: reverse-engineer-design
description: "リポジトリのソースコードを解析してシステム設計書を自動生成するリバースエンジニアリングスキル。SQLiteに解析結果を随時保存してコンテキストを常にクリーンに保ち、複数の並列エージェントで効率的に解析する。Use when: (1) 既存のリポジトリやコードベースからシステム設計書・仕様書を作成したい, (2) ソースコードを読んでアーキテクチャや構成を理解したい, (3) プロジェクトの全体像をドキュメント化したい, (4) APIエンドポイント一覧やデータモデルを整理したい, (5) 画面一覧や機能一覧を洗い出したい, (6) 新しいチームメンバーのためにシステムの概要ドキュメントを作りたい, (7) レガシーコードの理解・引き継ぎ資料を作りたい, (8) 大規模リポジトリをコンテキスト超過なく解析したい。このスキルはユーザーが「設計書を作って」「コードを分析して」「リバースエンジニアリングして」「このリポジトリの全体像を教えて」「ドキュメントを生成して」「仕様書を起こして」などと言ったときに必ず使用すること。Keywords: reverse engineering, system design, documentation, architecture, sqlite, parallel agents, context management, リバースエンジニアリング, 設計書, 仕様書, ドキュメント生成, アーキテクチャ分析, コード解析, API一覧, 画面一覧, ER図, データモデル, 並列解析, コンテキスト管理"
---

# リバースエンジニアリング設計書ジェネレーター

ソースコードを解析し、体系化されたシステム設計書を自動生成する。

**設計思想：解析結果はDBに即保存してコンテキストから破棄。常に軽量なコンテキストを維持する。**

## 概要

このスキルは、リポジトリのソースコードを包括的に分析し、以下を含むシステム設計書を `docs/design/` ディレクトリに自動生成する：

- **システム概要・アーキテクチャ**（技術スタック、全体構成図）
- **API/エンドポイント一覧**（リクエスト/レスポンス例付き）
- **データモデル**（ER図、テーブル定義）
- **機能別詳細ドキュメント**（画面・API・DBを包括的に記述）

すべてのドキュメントは日本語で記述し、図表にはMermaidダイアグラムを積極的に使用する。

---

## コンテキスト管理の原則

**以下を必ず守ること：**

1. **読んだら保存して捨てる** — ファイルを読んだらサマリーをDBに保存し、生の内容はコンテキストに残さない
2. **DBを一次ストレージとして扱う** — 解析結果の正本はDB。コンテキストは作業メモに過ぎない
3. **再読み込みをしない** — `file exists` コマンドでキャッシュ済みを確認し、済みなら再読みしない
4. **DBから情報を引く** — 他エージェントの結果や自分の過去の結果はDBから参照する

---

## ワークフロー

### 事前準備: 解析DBのセットアップ

**解析開始前に毎回実行する：**

```bash
# 1. re_db.py のパスを確認（複数の候補パスを検索）
RE_DB=$(find ~/.claude /home /root -name "re_db.py" -path "*/reverse-engineer-design/*" 2>/dev/null | head -1)
echo "re_db path: $RE_DB"

# 2. 解析対象リポジトリのルートに移動（ユーザーが指定したパス）
cd /path/to/target/repo

# 3. DBを初期化（冪等 — 既存DBがあっても安全）
python $RE_DB --db .re_analysis.db init

# 4. セッションを作成（既存セッションがあればそのIDを返す）
python $RE_DB --db .re_analysis.db session create \
    --repo-path $(pwd) \
    --repo-name $(basename $(pwd))
# → {"session_id": 1, "is_new": true, "status": "in_progress"}
# SESSION_ID=1 として以降の全コマンドで使用する

# 5. 未完了ステップを確認（再開時は既完了ステップをスキップ）
python $RE_DB --db .re_analysis.db step pending --session-id $SESSION_ID
```

> **変数として記録する:** `RE_DB` と `SESSION_ID` はこのセッション中ずっと使用する。

---

### Phase 1: リポジトリスキャン

目的：プロジェクトの全体像を素早く把握し、結果をDBに保存する。

**各ステップの後にDBに保存してコンテキストから捨てる。**

#### 1-1. プロジェクト設定ファイルを読む

対象: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `Gemfile`, `composer.json` 等

```bash
# ステップ完了後
python $RE_DB --db .re_analysis.db step done \
    --session-id $SESSION_ID --phase 1 --step config_files \
    --summary "FastAPI + SQLAlchemy + PostgreSQL 使用"

# 技術スタックをセッションに記録
python $RE_DB --db .re_analysis.db session set-meta \
    --session-id $SESSION_ID \
    --tech-stack '{"language":"Python","framework":"FastAPI","db":"PostgreSQL"}' \
    --project-type "api"
```

#### 1-2. ディレクトリ構造を確認する

主要ディレクトリ（`src/`, `app/`, `pages/`, `api/`, `models/`, `views/`, `controllers/`, `services/`）の構成を把握する。

```bash
python $RE_DB --db .re_analysis.db step done \
    --session-id $SESSION_ID --phase 1 --step dir_structure \
    --summary "app/ 以下にrouter/model/schema層。Clean Architecture構成"

python $RE_DB --db .re_analysis.db session set-meta \
    --session-id $SESSION_ID --arch-pattern "Clean Architecture"
```

#### 1-3. README・既存ドキュメントを読む

```bash
python $RE_DB --db .re_analysis.db step done \
    --session-id $SESSION_ID --phase 1 --step readme \
    --summary "TODOアプリ。ユーザー認証付きタスク管理API"

# 読んだファイルをキャッシュに記録
python $RE_DB --db .re_analysis.db file add \
    --session-id $SESSION_ID --path README.md \
    --category other --summary "プロジェクト概要: タスク管理API"
```

#### 1-4. エントリーポイントを特定する

アプリの起動ポイントとルーティング定義ファイルを特定する。

```bash
python $RE_DB --db .re_analysis.db step done \
    --session-id $SESSION_ID --phase 1 --step entry_points \
    --summary "app/main.py がエントリーポイント。app/api/v1/ にルーター"

python $RE_DB --db .re_analysis.db session set-meta \
    --session-id $SESSION_ID \
    --entry-points '["app/main.py","app/api/v1/router.py"]'
```

---

### Phase 2: 詳細分析（並列エージェントで実行）

**Phase 1が完了したら、以下の分析ステップを Agent ツールで並列起動する。**

各エージェントは独立して動作し、DBを共有ストレージとして使う。

#### 並列起動するエージェント一覧

| エージェントID | 担当フェーズ2ステップ | 書き込み先テーブル |
|---|---|---|
| `agent_arch` | `architecture` | `architecture_notes` |
| `agent_routing` | `routing` | `endpoints` |
| `agent_models` | `data_models` | `data_models` |
| `agent_frontend` | `frontend` | `functional_domains`（画面情報）|

`agent_domains` は上記4つが完了後に起動し、DBのデータを統合してドメイン紐付けを行う。

#### 各エージェントへの指示テンプレート

```
あなたはリバースエンジニアリング解析の担当エージェントです。

## セットアップ情報
- 解析対象: {repo_path}
- RE_DB スクリプト: {re_db_path}
- SESSION_ID: {session_id}
- DB: {repo_path}/.re_analysis.db
- 担当ステップ: Phase 2 / {step_name}
- エージェントID: {agent_id}

## 最初に実行すること
# ステップをclaimする（自分の担当ステップを宣言）
python {re_db_path} --db .re_analysis.db step claim \
    --session-id {session_id} --phase 2 --agent-id {agent_id}

# セッション情報を確認
python {re_db_path} --db .re_analysis.db context summary --session-id {session_id}

## コンテキスト管理の原則
- ファイルを読んだら内容のサマリーをDBに保存し、生の内容はコンテキストから捨てる
- ファイルを読む前に `file exists` でキャッシュ済みか確認する
- 結果はDBに随時保存（10件ずつなど小分けに）

## 担当タスク
{specific_instructions}

## 完了時
python {re_db_path} --db .re_analysis.db step done \
    --session-id {session_id} --phase 2 --step {step_name} \
    --summary "{result_summary}"
```

#### agent_arch（アーキテクチャ分析）の specific_instructions

```
以下を分析してarchitecture_notesテーブルに保存せよ：
- アプリケーション種別（Webアプリ/API/CLI/ライブラリ等）
- レイヤー構成（プレゼンテーション/ビジネスロジック/データアクセス層）
- 採用デザインパターン（MVC/Clean Architecture/DDD等）
- 外部サービス連携
- 認証・認可の仕組み

保存コマンド例：
python $RE_DB --db .re_analysis.db note add \
    --session-id $SESSION_ID \
    --category pattern \
    --title "Clean Architecture採用" \
    --content "domain/usecase/infrastructure層に分離。依存の方向は内側のみ"
```

#### agent_routing（ルーティング・エンドポイント分析）の specific_instructions

```
すべてのAPIエンドポイントを洗い出しendpointsテーブルに保存せよ：
- HTTPメソッドとパス
- ハンドラーファイル・関数名
- 認証要否
- リクエスト/レスポンス形式

ファイルを読む前に必ずキャッシュ確認：
python $RE_DB --db .re_analysis.db file exists --session-id $SESSION_ID --path <path>

保存コマンド例（10件ずつ処理する）：
python $RE_DB --db .re_analysis.db endpoint add --session-id $SESSION_ID \
    --json '{"method":"GET","path":"/api/users","description":"ユーザー一覧","auth_required":1,"handler_file":"app/api/users.py","handler_func":"get_users"}'
```

#### agent_models（データモデル分析）の specific_instructions

```
ORM定義・マイグレーション・スキーマを読み、data_modelsテーブルに保存せよ：
- モデル名・テーブル名・ソースファイル
- フィールド（名前・型・制約）
- リレーション（has_many/belongs_to等）
- インデックス

保存コマンド例：
python $RE_DB --db .re_analysis.db model add --session-id $SESSION_ID \
    --json '{
      "model_name": "User",
      "table_name": "users",
      "source_file": "app/models/user.py",
      "description": "認証ユーザー",
      "fields": [
        {"name":"id","type":"INTEGER","pk":true,"nullable":false},
        {"name":"email","type":"TEXT","nullable":false},
        {"name":"created_at","type":"DATETIME","nullable":false}
      ],
      "relations": [{"type":"has_many","target":"Task","fk":"user_id"}],
      "indexes": [{"name":"idx_user_email","columns":["email"],"unique":true}]
    }'
```

#### agent_frontend（フロントエンド・画面分析）の specific_instructions

```
フロントエンドが存在する場合、画面構成を分析してfunctional_domainsに保存せよ。
フロントエンドがない場合は即座にskipする：
python $RE_DB --db .re_analysis.db step skip --session-id $SESSION_ID --phase 2 --step frontend

存在する場合：
- ページ/画面一覧（名前・パス・説明）
- 画面遷移
- 状態管理方式

保存コマンド例：
python $RE_DB --db .re_analysis.db domain add \
    --session-id $SESSION_ID --name auth \
    --json '{
      "description": "認証・ログイン",
      "screens": [
        {"name":"ログイン画面","path":"/login","description":"メール+パスワード認証"},
        {"name":"ユーザー登録画面","path":"/register","description":"新規ユーザー登録"}
      ],
      "screen_transitions": [
        {"from":"ログイン画面","to":"ダッシュボード","trigger":"ログイン成功"}
      ]
    }'
```

#### agent_domains（統合・ドメイン紐付け）— 上記4エージェント完了後に起動

```
DBに蓄積されたエンドポイント・モデル・画面データを参照し、
機能ドメインを特定してdomainsステップを完了させよ：

# 現状確認
python $RE_DB --db .re_analysis.db endpoint list --session-id $SESSION_ID
python $RE_DB --db .re_analysis.db model list --session-id $SESSION_ID
python $RE_DB --db .re_analysis.db domain list --session-id $SESSION_ID

# エンドポイントにドメインを紐付け
python $RE_DB --db .re_analysis.db endpoint set-domain \
    --session-id $SESSION_ID --method GET --path /api/users --domain auth

# ドメインにビジネスルールを追加
python $RE_DB --db .re_analysis.db domain update \
    --session-id $SESSION_ID --name auth \
    --json '{"business_rules":["パスワードは8文字以上","メールは一意制約"]}'
```

---

### Phase 3: ドキュメント生成

**DBから情報を取得してドキュメントを生成する。コードを再読しない。**

```bash
# 蓄積データを確認
python $RE_DB --db .re_analysis.db context summary --session-id $SESSION_ID

# 各セクションのデータをエクスポート
python $RE_DB --db .re_analysis.db context export --session-id $SESSION_ID --section endpoints
python $RE_DB --db .re_analysis.db context export --session-id $SESSION_ID --section models
python $RE_DB --db .re_analysis.db context export --session-id $SESSION_ID --section domains
python $RE_DB --db .re_analysis.db context export --session-id $SESSION_ID --section architecture
```

エクスポート結果を元に以下の順序で `docs/design/` 配下にドキュメントを生成する：

#### 生成するファイル一覧

| ファイル | 内容 | 参照するDBセクション |
|---------|------|---------------------|
| `README.md` | 目次・プロジェクト概要 | session情報、architecture |
| `system-overview.md` | システム概要・アーキテクチャ | architecture_notes |
| `api-endpoints.md` | 全エンドポイント一覧 | endpoints |
| `data-model.md` | 全体ER図・テーブル定義 | data_models |
| `features/<domain>.md` | 機能ドメインごとの詳細 | functional_domains + endpoints + data_models |

各ステップ完了後にDBに記録する：
```bash
python $RE_DB --db .re_analysis.db step done \
    --session-id $SESSION_ID --phase 3 --step api_doc \
    --summary "24エンドポイントを api-endpoints.md に出力"
```

---

## ドキュメント仕様

### system-overview.md に含めること

- **システム構成図**（Mermaid `graph` を使用）
- **技術スタック一覧**（カテゴリ別テーブル：言語、フレームワーク、DB、インフラ等）
- **ディレクトリ構成**（主要ディレクトリの役割を説明したツリー図）
- **アーキテクチャパターン**（採用しているデザインパターンの説明）
- **外部サービス連携**（連携先とその目的）

### api-endpoints.md の記述パターン

各エンドポイントについて：

```markdown
### POST /api/users

ユーザーを新規作成する。

**リクエストボディ:**
\`\`\`json
{"name": "田中太郎", "email": "tanaka@example.com", "password": "..."}
\`\`\`

**レスポンス (201 Created):**
\`\`\`json
{"id": 1, "name": "田中太郎", "email": "tanaka@example.com", "created_at": "..."}
\`\`\`

**認証:** 不要
```

### data-model.md に含めること

- **全体ER図**（Mermaid `erDiagram`）
- **テーブル定義**（テーブルごとに：名前・説明・カラム一覧・インデックス・リレーション）

### features/<domain>.md に含めること

- **機能概要**
- **画面/ページ一覧**と**画面遷移図**（Mermaid `stateDiagram-v2`）
- **関連APIエンドポイント**（一覧 → api-endpoints.md にリンク）
- **関連データモデル**（機能固有ER図）
- **主要な処理フロー**（Mermaid `sequenceDiagram`）
- **ビジネスルール・バリデーション**

---

## Mermaid ダイアグラム ガイドライン

| 用途 | ダイアグラム種類 | 記法 |
|------|-----------------|------|
| システム全体構成 | フローチャート | `graph TB` or `graph LR` |
| 画面遷移 | 状態遷移図 | `stateDiagram-v2` |
| 処理フロー | シーケンス図 | `sequenceDiagram` |
| ER図 | ER図 | `erDiagram` |
| クラス構成 | クラス図 | `classDiagram` |
| デプロイ構成 | フローチャート | `graph TB` |

- ダイアグラム内ラベルは日本語、ノードIDは英語
- 1ダイアグラムあたりのノード数は15個以内
- 大きすぎる場合はドメインごとに分割

---

## 分析対象にAPIやフロントエンドが存在しない場合

- **CLIツール**: 画面一覧の代わりにコマンド一覧・サブコマンド体系を記述する
- **ライブラリ**: APIエンドポイントの代わりにパブリックAPI（公開関数/クラス）を記述する
- **バッチ処理**: 処理フロー・スケジュール定義・入出力を中心に記述する
- **インフラ（IaC）**: リソース構成図・環境別設定を中心に記述する

存在しないステップは `step skip` で記録し、そのリポジトリの本質に合ったセクションを設ける。

---

## 品質チェックリスト

ドキュメント生成後、以下を確認する：

- [ ] `context summary` で全Phaseステップが completed または skipped になっている
- [ ] README.md の目次リンクがすべて正しいファイルを指している
- [ ] Mermaid ダイアグラムの構文が正しい（` ```mermaid ` で囲まれている）
- [ ] API エンドポイントにリクエスト/レスポンスのJSON例が含まれている
- [ ] ER図が主要なテーブルとリレーションを網羅している
- [ ] 各機能詳細ファイルに画面・API・DBの情報が揃っている
- [ ] ファイル間のクロスリファレンスリンクが正しい
- [ ] 日本語で統一されている（コード内の英語はそのまま残す）
