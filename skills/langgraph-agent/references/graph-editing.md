# グラフ編集ガイド (LangGraph 1.0+)

ユーザー指示に基づいて既存のLangGraphグラフにノード・エッジを追加・変更する手順。

## 目次
1. [ユーザー指示の解釈](#ユーザー指示の解釈)
2. [既存グラフの把握](#既存グラフの把握)
3. [ノードの追加](#ノードの追加)
4. [固定エッジの追加・変更](#固定エッジの追加変更)
5. [条件分岐エッジの追加・変更](#条件分岐エッジの追加変更)
6. [Stateへのフィールド追加](#stateへのフィールド追加)
7. [よくある編集パターン](#よくある編集パターン)

---

## ユーザー指示の解釈

ユーザーの自然言語指示を以下の操作に対応させる。

| ユーザーの言葉 | 操作 |
|---|---|
| 「〜する処理を追加したい」「〜ステップを入れたい」 | ノード追加 |
| 「〜の前/後に処理を入れたい」 | ノード追加 + エッジ変更 |
| 「〜の場合は〜に進むようにしたい」 | 条件分岐エッジ追加 |
| 「〜と〜をつなげたい」 | 固定エッジ追加 |
| 「〜というデータを持ち回りたい」 | Stateフィールド追加 |
| 「〜を記録/保存したい」 | Stateフィールド追加 + ノード変更 |
| 「〜ノードをスキップしたい」 | 条件分岐エッジ変更 |

---

## 既存グラフの把握

編集前に必ず既存コードを読み込み、以下を確認する:

```python
# グラフ構造の確認（実行できる場合）
print(app.get_graph().draw_ascii())
print(app.get_graph().draw_mermaid())
```

コードから把握するポイント:
- `class State(TypedDict)` または `class State(MessagesState)` → 現在のStateフィールド一覧
- `graph.add_node("名前", 関数)` → 既存ノード一覧
- `graph.add_edge(A, B)` → 固定エッジ一覧
- `graph.add_conditional_edges(A, func, {...})` → 条件分岐一覧

---

## ノードの追加

### 基本: ノード関数を定義して登録する

```python
# 新しいノード関数を定義
def new_node(state: State) -> dict:
    """新しい処理の説明。"""
    # state から必要なデータを取得
    result = some_processing(state["input_field"])
    # 更新したいStateキーのみdictで返す
    return {"output_field": result}

# グラフに登録
graph.add_node("new_node", new_node)
```

### LLMを使うノード

```python
def llm_node(state: State) -> dict:
    """LLMで処理するノード。"""
    response = model.invoke(state["messages"])
    return {"messages": [response]}

graph.add_node("llm_node", llm_node)
```

### ツールを実行するノード

```python
from langgraph.prebuilt import ToolNode

tools = [search_tool, calc_tool]
tool_node = ToolNode(tools)
graph.add_node("tools", tool_node)  # ToolNodeはそのまま登録可能
```

### Command でステートを更新するノード

```python
from langgraph.types import Command

def routing_node(state: State) -> Command:
    """ステート更新と次のノード指定を同時に行う。"""
    category = classify(state["messages"][-1].content)
    return Command(
        update={"category": category},
        goto=category,  # 次のノード名を指定
    )

graph.add_node("router", routing_node)
# Command.goto を使う場合、add_conditional_edges の代わりになる
```

---

## 固定エッジの追加・変更

### 末尾にノードを追加（A → B → NEW → END）

```python
# 変更前: graph.add_edge("B", END)
# 変更後:
graph.add_edge("B", "new_node")   # BからNEWへ
graph.add_edge("new_node", END)   # NEWから終了へ
```

### 中間にノードを挿入（A → NEW → B）

```python
# 変更前: graph.add_edge("A", "B")
# 変更後: 古いエッジを削除して新しいエッジを張る
# ※ LangGraph 1.0では add_edge を上書きできない。
#    StateGraph をビルドし直す（compile前なら問題なし）

graph = StateGraph(State)
graph.add_node("A", node_a)
graph.add_node("new_node", new_node)  # 新ノード追加
graph.add_node("B", node_b)
graph.add_edge(START, "A")
graph.add_edge("A", "new_node")       # A → NEW
graph.add_edge("new_node", "B")       # NEW → B
graph.add_edge("B", END)
```

### 先頭にノードを追加（NEW → 既存START）

```python
# 変更前: graph.add_edge(START, "first_node")
# 変更後:
graph.add_node("preprocessor", preprocessor)
graph.add_edge(START, "preprocessor")      # 新エントリポイント
graph.add_edge("preprocessor", "first_node")  # 既存ノードへ接続
```

---

## 条件分岐エッジの追加・変更

### 固定エッジを条件分岐に変更

```python
# 変更前（固定）: graph.add_edge("model", END)
# 変更後（条件分岐）:

def should_use_tools(state: State) -> str:
    """ツール呼び出しが必要か判定する。"""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"

graph.add_conditional_edges(
    "model",           # 分岐元ノード
    should_use_tools,  # ルーティング関数（str を返す）
    {
        "tools": "tools",  # 戻り値 → 遷移先ノード
        "end": END,
    }
)
```

### 既存の条件分岐に分岐先を追加

```python
# 変更前:
# graph.add_conditional_edges("router", route, {"A": "node_a", "B": "node_b"})
# 変更後: 新しい分岐先 "C" を追加

def route(state: State) -> str:
    category = state["category"]
    if category == "A":
        return "A"
    elif category == "B":
        return "B"
    else:
        return "C"  # 新しいケースを追加

graph.add_conditional_edges(
    "router",
    route,
    {"A": "node_a", "B": "node_b", "C": "node_c"},  # "C" を追加
)
graph.add_node("node_c", node_c)  # 新ノードも登録
graph.add_edge("node_c", END)
```

### ループバックエッジの追加

```python
# "evaluate" ノードから "generate" に戻るループを追加

def check_quality(state: State) -> str:
    if "APPROVED" in state["feedback"]:
        return "done"
    if state.get("iteration", 0) >= 3:
        return "done"
    return "retry"

graph.add_conditional_edges(
    "evaluate",
    check_quality,
    {"retry": "generate", "done": END},  # retryでgenerateに戻る
)
```

---

## Stateへのフィールド追加

新しいデータを処理間で引き継ぐ場合、Stateにフィールドを追加する。

```python
# 変更前
class State(MessagesState):
    pass

# 変更後: フィールドを追加
class State(MessagesState):
    # 新フィールド（デフォルト値はノード内で state.get("key", default) で対応）
    user_intent: str        # ユーザーの意図を分類
    confidence: float       # 信頼スコア
    retry_count: int        # リトライ回数
    context: str            # 追加コンテキスト
```

**重要**: 新フィールドを使うノードでは `state.get("field", default)` で安全に取得する。

```python
def my_node(state: State) -> dict:
    count = state.get("retry_count", 0)  # デフォルト0
    return {"retry_count": count + 1}
```

### リデューサー付きフィールドの追加

リストを蓄積するフィールドにはリデューサーを指定する。

```python
import operator
from typing import Annotated

class State(MessagesState):
    results: Annotated[list[str], operator.add]  # 追加時にマージされる
```

---

## よくある編集パターン

### パターン1: 処理の前に前処理ノードを挿入

**ユーザー指示**: 「モデルを呼ぶ前に入力をバリデーションしたい」

```python
def validate_input(state: State) -> dict:
    """入力を検証し、不正な場合はエラーメッセージを返す。"""
    last = state["messages"][-1].content
    if len(last) < 2:
        return {"messages": [AIMessage(content="入力が短すぎます。")], "is_valid": False}
    return {"is_valid": True}

def route_after_validate(state: State) -> str:
    return "model" if state.get("is_valid", True) else END

# State に is_valid フィールドを追加
# graph にノードとエッジを追加:
graph.add_node("validate", validate_input)
graph.add_edge(START, "validate")
graph.add_conditional_edges("validate", route_after_validate, {"model": "model", END: END})
```

### パターン2: 処理の後に後処理ノードを追加

**ユーザー指示**: 「モデルの回答をログに保存したい」

```python
def log_response(state: State) -> dict:
    """レスポンスをログに記録する。"""
    last = state["messages"][-1].content
    with open("responses.log", "a") as f:
        f.write(f"{last}\n")
    return {}  # Stateは変更しない場合は空dictを返す

graph.add_node("logger", log_response)
# 変更前: graph.add_edge("model", END)
# 変更後:
graph.add_edge("model", "logger")
graph.add_edge("logger", END)
```

### パターン3: 並列処理ノードの追加（Send API）

**ユーザー指示**: 「複数のアイテムを並列で処理したい」

```python
import operator
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.types import Send
from langgraph.graph import StateGraph, START, END

class ParallelState(TypedDict):
    items: list[str]
    results: Annotated[list[str], operator.add]  # 並列結果をマージ

def process_item(state: dict) -> dict:
    """個別アイテムを処理する。"""
    return {"results": [f"処理済み: {state['item']}"]}

def fan_out(state: ParallelState) -> list[Send]:
    """各アイテムに Send を発行して並列実行。"""
    return [Send("process_item", {"item": item}) for item in state["items"]]

graph = StateGraph(ParallelState)
graph.add_node("process_item", process_item)
graph.add_conditional_edges(START, fan_out, ["process_item"])
graph.add_edge("process_item", END)
```

### パターン4: Command でルーティングとステート更新を同時に行う

**ユーザー指示**: 「分類結果に応じてノードを振り分けつつ、分類結果も保存したい」

```python
from langgraph.types import Command

def classifier(state: State) -> Command:
    """入力を分類し、結果を保存しつつ適切なノードに振り分ける。"""
    category = model.invoke(
        f"classify: {state['messages'][-1].content}"
    ).content.strip()
    return Command(
        update={"category": category},
        goto=category,  # "technical" / "general" / "sales"
    )

graph.add_node("classifier", classifier)
# Command.goto を使うため、add_conditional_edges は不要
graph.add_edge(START, "classifier")
```
