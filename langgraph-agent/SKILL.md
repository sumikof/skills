---
name: langgraph-agent
description: "Create AI agents using LangGraph 1.0 (Python) with OpenAI models. Sets up a Python project with pip/venv, then builds agents. Use when the user wants to: (1) create a new AI agent or chatbot, (2) build a ReAct agent with tool use, (3) design a custom multi-step graph workflow, (4) set up a new LangGraph project from scratch. Supports ReAct pattern (prebuilt) and custom StateGraph construction."
---

# LangGraph Agent

LangGraph 1.0を使ったAIエージェントをPythonで構築するスキル。プロジェクトのセットアップからエージェント実装まで一貫してサポートする。

## ワークフロー

1. **プロジェクトセットアップ** → pip/venv環境を構築し依存関係をインストール
2. **エージェントパターンの選択** → ユーザの目的に応じて最適なパターンを選ぶ
3. **エージェント実装** → 選択したパターンに基づきコードを生成
4. **動作確認** → エージェントを実行してテスト

## プロジェクトセットアップ

```bash
# プロジェクトディレクトリを作成
mkdir my-agent && cd my-agent

# 仮想環境を作成・有効化
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係をインストール
pip install langgraph langchain-openai langchain-core

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

迷ったら**ReActエージェント**から始めること。シンプルで拡張しやすい。

## LangGraph 1.0 共通事項

- `StateGraph` + `MessagesState` が基本構造
- ノードは `state` を受け取り `dict` を返す純粋な関数
- エッジで制御フローを定義（固定 or 条件分岐）
- `graph.compile()` で実行可能なアプリを生成
- 会話履歴の保持には `MemorySaver` チェックポインターを使用

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = graph.compile(checkpointer=memory)

# スレッドIDで会話を管理
config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke({"messages": [...]}, config=config)
```

## テンプレートファイル

- `assets/templates/react_agent.py` - ReActエージェントの完全なサンプル
- `assets/templates/custom_graph.py` - カスタムグラフの完全なサンプル

各テンプレートはそのまま実行可能。ユーザの要件に合わせてカスタマイズすること。

## 詳細リファレンス

- **ReActエージェント実装**: `references/react-agent.md`
- **カスタムグラフ実装**: `references/custom-graph.md`
- **トラブルシューティング**: `references/troubleshooting.md`
