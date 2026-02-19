# トラブルシューティング (LangGraph 1.0+)

## 環境要件

- **Python 3.10以上**が必須（3.9以下はサポート外）
- LangGraph 1.0.0以上

## よくあるエラーと解決策

### ImportError: cannot import name 'create_react_agent'

```
ImportError: cannot import name 'create_react_agent' from 'langgraph.prebuilt'
```

**原因**: LangGraphのバージョンが古い

```bash
pip install --upgrade langgraph langchain-openai
# LangGraph 1.0以上を確認
python -c "import langgraph; print(langgraph.__version__)"
```

**LangGraph 1.0+の正しいインポート**:
```python
from langgraph.prebuilt import create_react_agent       # ReActエージェント
from langgraph.prebuilt import ToolNode, tools_condition # ツール統合
from langgraph.checkpoint.memory import InMemorySaver    # メモリチェックポインター
from langgraph.graph import StateGraph, START, END       # グラフ構築
from langgraph.graph import MessagesState                # メッセージステート
from langgraph.types import interrupt, Command           # HITL・状態更新
```

### AuthenticationError / API Key

```
openai.AuthenticationError: Incorrect API key provided
```

```python
import os
os.environ["OPENAI_API_KEY"] = "sk-..."  # 直接設定

# または .env から読み込み
from dotenv import load_dotenv
load_dotenv()
```

### RecursionError / GraphRecursionError

```
langgraph.errors.GraphRecursionError: Recursion limit of 25 reached
```

**原因**: グラフが無限ループしている

```python
# 再帰制限を増やす（根本解決ではない）
app.invoke(state, {"recursion_limit": 50})

# 根本対策: ループの終了条件を確認
def should_continue(state):
    if len(state["messages"]) > 10:  # 上限を設ける
        return END
    return "model"
```

### TypeError: State キーが見つからない

```
KeyError: 'messages'
```

**原因**: 初期ステートに必要なキーがない

```python
# 必要なキーをすべて含めて初期化
result = app.invoke({
    "messages": [],  # 空リストでも必要
    "user_name": "",
    "step_count": 0,
})
```

**ヒント**: `MessagesState` を使う場合、`messages` 以外のカスタムフィールドは `state.get("key", default)` で安全にアクセスする。

### ツールが呼ばれない

**確認事項**:
```python
# 1. モデルにツールをバインドしているか（カスタムグラフの場合）
model_with_tools = model.bind_tools(tools)  # ← 忘れがち
# ※ create_react_agent の場合は自動でバインドされる

# 2. ツールのdocstringが明確か（モデルがツールを選択する判断材料）
@tool
def search(query: str) -> str:
    """ウェブで情報を検索する。質問への回答に必要な情報を取得するために使用。"""  # ← 具体的に
    ...

# 3. temperature=0 で確定的な動作に
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

### チェックポインターのスレッドID忘れ

```python
# ❌ 毎回新しいスレッドになる（会話が引き継がれない）
app.invoke(state, {"configurable": {}})

# ✅ 同じthread_idで会話を維持
config = {"configurable": {"thread_id": "user-session-123"}}
app.invoke(state, config)
```

### interrupt() が動作しない

```python
# ❌ チェックポインターなしでは interrupt() は機能しない
app = graph.compile()  # チェックポインターが未設定

# ✅ チェックポインターを設定する
app = graph.compile(checkpointer=InMemorySaver())

# ❌ interrupt() を try/except で囲んではいけない
def bad_node(state):
    try:
        result = interrupt("確認してください")  # 例外が捕捉されてしまう
    except:
        pass

# ✅ interrupt() はそのまま使う
def good_node(state):
    result = interrupt("確認してください")
    return {"approved": result}
```

## バージョン情報と非推奨の注意

### LangGraph 0.x → 1.0 の主な変更

| 0.x | 1.0+ |
|---|---|
| `from langgraph.checkpoint import MemorySaver` | `from langgraph.checkpoint.memory import InMemorySaver` |
| `graph.__call__(state)` | `graph.invoke(state)` |
| 静的ブレークポイント | `interrupt()` 関数 |

### 非推奨の注意 (langgraph.prebuilt)

`langgraph.prebuilt` の一部は将来的に `langchain.agents` に移行予定。ただし LangGraph 2.0 までは引き続き動作する。

| 現在（動作する） | 将来の移行先 |
|---|---|
| `langgraph.prebuilt.create_react_agent` | `langchain.agents.create_agent` |

**推奨**: 現時点では `langgraph.prebuilt.create_react_agent` を使い続けて問題ない。移行先の API はまだ安定していない可能性がある。

### チェックポインター名の変更

`MemorySaver` と `InMemorySaver` は同じクラスのエイリアス。最新ドキュメントでは `InMemorySaver` が正式名称。

```python
# どちらも動作する（同じクラス）
from langgraph.checkpoint.memory import MemorySaver      # 旧名
from langgraph.checkpoint.memory import InMemorySaver    # 正式名称（推奨）
```

## デバッグ方法

```python
# ストリームで各ステップを確認（updatesモード推奨）
for step in app.stream(initial_state, stream_mode="updates"):
    for node_name, output in step.items():
        print(f"[{node_name}] {output}")

# debugモードで最大限の情報を取得
for event in app.stream(initial_state, stream_mode="debug"):
    print(event)

# ロギングを有効化
import logging
logging.basicConfig(level=logging.DEBUG)

# グラフ構造をASCIIで確認
print(app.get_graph().draw_ascii())
```

## 依存関係の確認

```bash
pip list | grep -E "langgraph|langchain"
# 期待されるバージョン:
# langgraph          >= 1.0.0
# langchain-openai   >= 0.3.0
# langchain-core     >= 0.3.0
#
# マルチエージェント（必要な場合のみ）:
# langgraph-supervisor >= 0.1.0
# langgraph-swarm      >= 0.1.0
#
# 永続チェックポインター（必要な場合のみ）:
# langgraph-checkpoint-sqlite   >= 3.0.0
# langgraph-checkpoint-postgres >= 3.0.0
```
