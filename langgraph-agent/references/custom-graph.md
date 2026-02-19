# カスタムグラフ (LangGraph 1.0+)

`StateGraph` を使った柔軟なカスタムグラフの実装ガイド。

## 基本構造

```python
from typing import Annotated
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# 1. ステート定義
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    # 追加フィールドも定義可能
    user_name: str
    step_count: int

# 2. ノード関数を定義
model = ChatOpenAI(model="gpt-4o-mini")

def call_model(state: State) -> dict:
    response = model.invoke(state["messages"])
    return {"messages": [response], "step_count": state.get("step_count", 0) + 1}

def process_input(state: State) -> dict:
    # 前処理ロジック
    return {"step_count": 0}

# 3. グラフを構築
graph = StateGraph(State)
graph.add_node("preprocess", process_input)
graph.add_node("model", call_model)

# 4. エッジを定義
graph.add_edge(START, "preprocess")
graph.add_edge("preprocess", "model")
graph.add_edge("model", END)

# 5. コンパイル
app = graph.compile()

# 6. 実行
result = app.invoke({
    "messages": [{"role": "user", "content": "こんにちは"}],
    "user_name": "太郎",
    "step_count": 0
})
```

## MessagesState の使用（推奨）

`MessagesState` を継承すると `messages` フィールド（`add_messages`リデューサー付き）が自動で含まれる。追加フィールドのみ定義すればよい。

```python
from langgraph.graph import MessagesState

class State(MessagesState):
    # messagesはすでに定義済み（add_messagesリデューサー付き）
    user_context: str  # 追加フィールドのみ定義
```

## シーケンシャルな処理（add_sequence）

固定順序のノードを簡潔に定義できる。

```python
graph = StateGraph(State)
graph.add_sequence([step1, step2, step3])  # 関数を順番に実行
# ↑ は以下と等価:
# graph.add_node("step1", step1)
# graph.add_node("step2", step2)
# graph.add_node("step3", step3)
# graph.add_edge(START, "step1")
# graph.add_edge("step1", "step2")
# graph.add_edge("step2", "step3")
# graph.add_edge("step3", END)

app = graph.compile()
```

## 条件分岐 (Conditional Edges)

```python
from langgraph.graph import StateGraph, START, END

def route_message(state: State) -> str:
    """ルーティングロジック：次のノード名を返す。"""
    last_message = state["messages"][-1]
    if "天気" in last_message.content:
        return "weather_node"
    elif "計算" in last_message.content:
        return "calc_node"
    else:
        return "general_node"

graph.add_conditional_edges(
    "router",           # 分岐元ノード
    route_message,      # ルーティング関数
    {
        "weather_node": "weather_node",  # 戻り値 → ノード名
        "calc_node": "calc_node",
        "general_node": "general_node",
    }
)
```

## ツールノードの組み込み

```python
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool

@tool
def search(query: str) -> str:
    """検索ツール。"""
    return f"検索結果: {query}"

tools = [search]
model_with_tools = model.bind_tools(tools)

def call_model(state: State) -> dict:
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}

tool_node = ToolNode(tools)

graph = StateGraph(State)
graph.add_node("model", call_model)
graph.add_node("tools", tool_node)

graph.add_edge(START, "model")
graph.add_conditional_edges(
    "model",
    tools_condition,  # ツール呼び出しがあれば"tools"、なければEND
)
graph.add_edge("tools", "model")  # ツール実行後モデルに戻る

app = graph.compile()
```

## 複数ノードのパイプライン

```python
class PipelineState(TypedDict):
    raw_input: str
    cleaned_input: str
    analysis: str
    final_response: str

def clean_input(state: PipelineState) -> dict:
    return {"cleaned_input": state["raw_input"].strip().lower()}

def analyze(state: PipelineState) -> dict:
    result = model.invoke(f"分析してください: {state['cleaned_input']}")
    return {"analysis": result.content}

def generate_response(state: PipelineState) -> dict:
    result = model.invoke(f"分析結果をもとに回答: {state['analysis']}")
    return {"final_response": result.content}

graph = StateGraph(PipelineState)
graph.add_node("clean", clean_input)
graph.add_node("analyze", analyze)
graph.add_node("respond", generate_response)

graph.add_edge(START, "clean")
graph.add_edge("clean", "analyze")
graph.add_edge("analyze", "respond")
graph.add_edge("respond", END)

app = graph.compile()
result = app.invoke({"raw_input": "AIエージェントとは？"})
print(result["final_response"])
```

## ループ・反復処理

```python
def should_continue(state: State) -> str:
    """最大5回ループして終了。"""
    if state.get("step_count", 0) >= 5:
        return "end"
    return "continue"

graph.add_conditional_edges(
    "model",
    should_continue,
    {"continue": "model", "end": END}
)
```

## ステートの確認

```python
# ストリーミングで各ステップの出力を確認
for step in app.stream(initial_state, stream_mode="updates"):
    for node_name, output in step.items():
        print(f"[{node_name}] {output}")

# チェックポインター使用時の状態取得
from langgraph.checkpoint.memory import InMemorySaver
memory = InMemorySaver()
app = graph.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "t1"}}
app.invoke(initial_state, config=config)
state = app.get_state(config)
print(state.values)
```

## グラフの可視化

```python
# ASCII表示
print(app.get_graph().draw_ascii())

# Mermaid形式
print(app.get_graph().draw_mermaid())
```

## StateGraph のパラメータ一覧

| パラメータ | 型 | 説明 |
|---|---|---|
| `state_schema` | `type[TypedDict]` | ステート定義（必須） |
| `input_schema` | `type[TypedDict]` | 入力スキーマ（省略時はstate_schema） |
| `output_schema` | `type[TypedDict]` | 出力スキーマ（省略時はstate_schema） |

### compile() のパラメータ

| パラメータ | 型 | 説明 |
|---|---|---|
| `checkpointer` | `BaseCheckpointSaver` | 会話履歴の保存先 |
| `store` | `BaseStore` | スレッド横断の永続ストレージ |
| `interrupt_before` | `list[str]` | 指定ノード実行前に中断 |
| `interrupt_after` | `list[str]` | 指定ノード実行後に中断 |
| `name` | `str` | グラフの識別名 |
