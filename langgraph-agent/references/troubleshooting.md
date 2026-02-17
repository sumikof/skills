# トラブルシューティング (LangGraph 1.0)

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

**LangGraph 1.0の正しいインポート**:
```python
from langgraph.prebuilt import create_react_agent  # ✅ 1.0
from langgraph.prebuilt import ToolNode, tools_condition  # ✅ 1.0
from langgraph.checkpoint.memory import MemorySaver  # ✅ 1.0
from langgraph.graph import StateGraph, START, END  # ✅ 1.0
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

### ツールが呼ばれない

**確認事項**:
```python
# 1. モデルにツールをバインドしているか
model_with_tools = model.bind_tools(tools)  # ← 忘れがち

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

## バージョン別の変更点

### LangGraph 0.x → 1.0 の主な変更

| 0.x | 1.0 |
|---|---|
| `from langgraph.checkpoint import MemorySaver` | `from langgraph.checkpoint.memory import MemorySaver` |
| `graph.add_node("node", func)` | 同じ（変更なし） |
| `StateGraph(State).compile()` | 同じ（変更なし） |
| `graph.__call__(state)` | `graph.invoke(state)` を推奨 |

## デバッグ方法

```python
# ストリームで各ステップを確認
for event in app.stream(initial_state, stream_mode="values"):
    print("=== Step ===")
    for key, val in event.items():
        print(f"{key}: {val}")

# ロギングを有効化
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 依存関係の確認

```bash
pip list | grep -E "langgraph|langchain"
# 期待されるバージョン:
# langgraph >= 1.0.0
# langchain-openai >= 0.1.0
# langchain-core >= 0.2.0
```
