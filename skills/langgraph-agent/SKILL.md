---
name: langgraph-agent
description: "Create and customize AI agents using LangGraph 1.0+ (Python). Sets up a Python project with pip/venv, then builds agents. Use when the user wants to: (1) create a new AI agent or chatbot, (2) build a ReAct agent with tool use, (3) design a custom multi-step graph workflow, (4) use the Functional API (@entrypoint/@task) for simple workflows, (5) set up a new LangGraph project from scratch, (6) customize or modify an existing LangGraph graph based on user instructions, (7) implement patterns like multi-agent supervisor/swarm, human-in-the-loop, RAG pipeline, conditional routing, or iterative loops, (8) add nodes or edges to an existing graph ('〜の処理を追加したい', '〜の前後に処理を入れたい', '〜の場合は〜に進ませたい'). Supports ReAct pattern (prebuilt), custom StateGraph construction, and Functional API."
---

# LangGraph Agent

LangGraph 1.0+を使ったAIエージェントをPythonで構築するスキル。プロジェクトのセットアップからエージェント実装まで一貫してサポートする。

**必須環境**: Python 3.10以上

## ワークフロー

1. **プロジェクトセットアップ** → pip/venv環境を構築し依存関係をインストール
2. **エージェントパターンの選択** → ユーザの目的に応じて最適なパターンを選ぶ
3. **エージェント実装** → 選択したパターンに基づきコードを生成
4. **動作確認** → エージェントを実行してテスト

## プロジェクトセットアップ

**プロジェクトのルートディレクトリで実行すること。**

```bash
# 仮想環境を作成・有効化
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 基本依存関係をインストール
pip install langgraph langchain-openai langchain-core python-dotenv

# マルチエージェントが必要な場合:
# pip install langgraph-supervisor  # Supervisorパターン
# pip install langgraph-swarm       # Swarmパターン

# .envファイルを作成
echo "OPENAI_API_KEY=your-key-here" > .env
```

`.env`の読み込み:
```python
from dotenv import load_dotenv
load_dotenv()
# または os.environ["OPENAI_API_KEY"] = "..."
```

## エージェントパターンの選択

| ユーザの目的 | 推奨パターン | 参照ファイル |
|---|---|---|
| ツール呼び出しで情報取得・タスク実行 | **ReActエージェント** | `references/react-agent.md` |
| 複数ステップの独自ロジック・分岐フロー | **カスタムグラフ** | `references/custom-graph.md` |
| シンプルなワークフロー（Pythonの制御フローで十分） | **Functional API** | `references/functional-api.md` |

迷ったら**ReActエージェント**から始めること。シンプルで拡張しやすい。

## LangGraph 1.0+ 共通事項

### モデルの指定方法

```python
# 方法1: モデルオブジェクト（従来の方法）
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 方法2: 文字列指定（create_react_agentで利用可能）
agent = create_react_agent("openai:gpt-4o-mini", tools)
```

対応するモデル文字列の例:
- `"openai:gpt-4o"`, `"openai:gpt-4o-mini"`
- `"anthropic:claude-sonnet-4-5-20250929"`

### ステート管理

- `StateGraph` + `MessagesState` が基本構造
- ノードは `state` を受け取り `dict` を返す純粋な関数
- エッジで制御フローを定義（固定 or 条件分岐）
- `graph.compile()` で実行可能なアプリを生成

### 会話履歴の保持（チェックポインター）

```python
from langgraph.checkpoint.memory import InMemorySaver  # 開発用

memory = InMemorySaver()
app = graph.compile(checkpointer=memory)

# スレッドIDで会話を管理
config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke({"messages": [...]}, config=config)
```

| チェックポインター | 用途 |
|---|---|
| `InMemorySaver` | 開発・テスト用（プロセス終了でデータ消失） |
| `SqliteSaver` | ローカル開発（ファイルに永続化） |
| `PostgresSaver` | 本番運用推奨 |

### ストリーミング

5つのストリームモードが利用可能。詳細は `references/streaming.md` を参照。

| モード | 説明 |
|---|---|
| `"values"` | 各ステップ後の完全なステート |
| `"updates"` | ステートの差分のみ |
| `"messages"` | LLMトークンをリアルタイムに取得 |
| `"custom"` | ノード内から任意のデータを送信 |
| `"debug"` | 最大限の実行詳細 |

## テンプレートファイル

- `assets/templates/react_agent.py` - ReActエージェントの完全なサンプル
- `assets/templates/custom_graph.py` - カスタムグラフの完全なサンプル

各テンプレートはそのまま実行可能。ユーザの要件に合わせてカスタマイズすること。

## ユーザー要件からグラフを設計する

ユーザーの自然言語による指示を基にグラフを設計・生成・カスタマイズする場合、以下のステップで進める。

### ステップ1: 要件ヒアリング

まず以下を確認する:
- **目的**: 何を達成したいか？（例:「文書を要約して翻訳したい」）
- **フロー**: 処理の流れに条件分岐・ループ・人間の確認は必要か？
- **入出力**: 何を入力し、何を出力するか？
- **状態**: 処理間で引き継ぐデータは何か？

### ステップ2: パターン選択

要件に最適なパターンを `references/graph-patterns.md` から選ぶ。

| 要件のキーワード | パターン |
|---|---|
| 「順番に」「手順A→B→C」 | シーケンシャルパイプライン |
| 「内容によって」「振り分け」「分類」 | 条件分岐ルーター |
| 「繰り返す」「満足するまで」「改善」 | ループ・反復処理 |
| 「複数の専門家」「役割分担」 | マルチエージェント (Supervisor/Swarm) |
| 「人間の確認」「承認が必要」「中断」 | Human-in-the-loop |
| 「共通処理を再利用」「モジュール化」 | サブグラフ |
| 「ドキュメント検索」「RAG」「知識ベース」 | RAGパイプライン |
| 「シンプルなフロー」「通常のPythonで十分」 | Functional API |

複数のパターンを組み合わせることも可能（例:「分類→専門エージェント」）。

### ステップ3: グラフの設計と実装

選択したパターンを基に:
1. **State** を定義（処理間で共有するデータ構造）
2. **ノード関数** を実装（各処理ステップ）
3. **エッジ** でフローを接続（固定 or 条件分岐）
4. `graph.compile()` でアプリ化

ユーザーが既存のグラフの変更を要求した場合:
- 既存コードを読み込んで理解する
- 変更箇所（ノード追加・エッジ変更・State拡張）を特定する
- 最小限の変更で要件を満たす

## ユーザー指示に基づくノード・エッジの追加

ユーザーが「〜の処理を追加したい」「〜の前後に処理を入れたい」などを指示した場合、以下の手順で対応する。詳細なコード例は `references/graph-editing.md` を参照。

### 手順

1. **既存コードを読み込む** → ノード・エッジ・Stateの現在の構造を把握する
2. **指示を操作に変換する**（下表を参考）
3. **必要なら Stateにフィールドを追加** する
4. **ノード関数を実装** して `graph.add_node()` で登録する
5. **エッジを追加または変更** する（固定 or 条件分岐）

### 指示 → 操作の対応表

| ユーザーの指示 | 操作 |
|---|---|
| 「〜する処理を追加したい」 | ノード追加 + エッジ接続 |
| 「〜の前に処理を入れたい」 | ノード追加 + エッジを差し替え（旧接続を削除して新ノードを挿入） |
| 「〜の後に処理を追加したい」 | ノード追加 + 末尾エッジを付け替え |
| 「〜の場合は〜に進ませたい」 | 固定エッジ → 条件分岐エッジに変更 |
| 「〜のデータを引き継ぎたい」 | Stateフィールド追加 |
| 「満足するまで繰り返したい」 | 条件分岐エッジでループバック追加 |
| 「複数アイテムを並列処理したい」 | Send API でファンアウト |

### エッジ変更の注意点

- LangGraph 1.0では `add_edge` を後から上書きできない。compile前にグラフ定義を整理すること。
- 中間にノードを挿入する場合は、旧エッジをコメントアウトして新エッジを追加する。
- 条件分岐エッジの分岐先を追加する場合は、ルーティング関数と mapping dictの両方を更新する。

## 詳細リファレンス

- **ReActエージェント実装**: `references/react-agent.md`
- **カスタムグラフ実装**: `references/custom-graph.md`
- **Functional API**: `references/functional-api.md`
- **ストリーミング**: `references/streaming.md`
- **グラフパターンライブラリ**: `references/graph-patterns.md`（パターン別の完全なコード例）
- **グラフ編集ガイド**: `references/graph-editing.md`（ノード・エッジ追加の具体的なコード例）
- **トラブルシューティング**: `references/troubleshooting.md`
