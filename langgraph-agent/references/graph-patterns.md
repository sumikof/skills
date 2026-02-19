# グラフパターンライブラリ (LangGraph 1.0+)

ユーザーの要件に合わせてグラフを設計するためのパターン集。

## 目次
1. [要件 → パターン選択](#要件--パターン選択)
2. [シーケンシャルパイプライン](#シーケンシャルパイプライン)
3. [条件分岐ルーター](#条件分岐ルーター)
4. [ループ・反復処理](#ループ反復処理)
5. [マルチエージェント (Supervisor)](#マルチエージェント-supervisor)
6. [マルチエージェント (Swarm)](#マルチエージェント-swarm)
7. [Human-in-the-loop](#human-in-the-loop)
8. [サブグラフ](#サブグラフ)
9. [RAGパイプライン](#ragパイプライン)

---

## 要件 → パターン選択

| ユーザーの要件 | 推奨パターン |
|---|---|
| 「手順A→B→Cの順で処理したい」 | シーケンシャルパイプライン |
| 「内容によって処理を切り替えたい」 | 条件分岐ルーター |
| 「十分な結果が出るまで繰り返したい」 | ループ・反復処理 |
| 「複数の専門エージェントに振り分けたい」 | マルチエージェント (Supervisor) |
| 「エージェント同士で直接タスクを受け渡したい」 | マルチエージェント (Swarm) |
| 「途中で人間の確認を入れたい」 | Human-in-the-loop |
| 「同じ処理を複数の場所で再利用したい」 | サブグラフ |
| 「ドキュメントを検索して回答したい」 | RAGパイプライン |

---

## シーケンシャルパイプライン

**用途**: 処理を固定した順番で実行する（前処理 → 分析 → 後処理など）

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class PipelineState(TypedDict):
    input: str
    step1_result: str
    step2_result: str
    output: str

def step1(state: PipelineState) -> dict:
    return {"step1_result": f"A処理: {state['input']}"}

def step2(state: PipelineState) -> dict:
    return {"step2_result": f"B処理: {state['step1_result']}"}

def step3(state: PipelineState) -> dict:
    return {"output": f"完成: {state['step2_result']}"}

graph = StateGraph(PipelineState)
graph.add_node("step1", step1)
graph.add_node("step2", step2)
graph.add_node("step3", step3)
graph.add_edge(START, "step1")
graph.add_edge("step1", "step2")
graph.add_edge("step2", "step3")
graph.add_edge("step3", END)
app = graph.compile()
```

**簡略版（add_sequence）**:
```python
graph = StateGraph(PipelineState)
graph.add_sequence([step1, step2, step3])
app = graph.compile()
```

---

## 条件分岐ルーター

**用途**: ユーザー入力や状態の内容に応じて、異なるノードに処理を振り分ける

```python
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class RouterState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    category: str  # "technical" | "general" | "sales"

def classify(state: RouterState) -> dict:
    """LLMで入力を分類する。"""
    last = state["messages"][-1].content
    result = model.invoke(f"次を分類せよ (technical/general/sales): {last}")
    return {"category": result.content.strip()}

def route(state: RouterState) -> str:
    """分類結果に基づいて次のノードを返す。"""
    return state["category"]

def handle_technical(state: RouterState) -> dict:
    resp = model.invoke("技術的な観点で回答: " + state["messages"][-1].content)
    return {"messages": [resp]}

def handle_general(state: RouterState) -> dict:
    resp = model.invoke(state["messages"])
    return {"messages": [resp]}

def handle_sales(state: RouterState) -> dict:
    resp = model.invoke("営業的観点で回答: " + state["messages"][-1].content)
    return {"messages": [resp]}

graph = StateGraph(RouterState)
graph.add_node("classify", classify)
graph.add_node("technical", handle_technical)
graph.add_node("general", handle_general)
graph.add_node("sales", handle_sales)

graph.add_edge(START, "classify")
graph.add_conditional_edges(
    "classify",
    route,
    {"technical": "technical", "general": "general", "sales": "sales"},
)
graph.add_edge("technical", END)
graph.add_edge("general", END)
graph.add_edge("sales", END)
```

---

## ループ・反復処理

**用途**: 評価→改善のサイクルを繰り返す（品質チェック、自己修正など）

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class IterativeState(TypedDict):
    task: str
    draft: str
    feedback: str
    iteration: int
    max_iterations: int

def generate(state: IterativeState) -> dict:
    """ドラフトを生成する。"""
    prompt = state["task"]
    if state.get("feedback"):
        prompt += f"\n\n前回のフィードバック: {state['feedback']}\n改善してください。"
    result = model.invoke(prompt)
    return {"draft": result.content, "iteration": state.get("iteration", 0) + 1}

def evaluate(state: IterativeState) -> dict:
    """ドラフトを評価してフィードバックを返す。"""
    result = model.invoke(
        f"以下の品質を評価し、改善点を指摘してください:\n{state['draft']}\n\nOKなら'APPROVED'と返してください。"
    )
    return {"feedback": result.content}

def should_continue(state: IterativeState) -> str:
    """承認済みか最大反復回数に達したら終了。"""
    if "APPROVED" in state["feedback"]:
        return "done"
    if state.get("iteration", 0) >= state.get("max_iterations", 3):
        return "done"
    return "retry"

graph = StateGraph(IterativeState)
graph.add_node("generate", generate)
graph.add_node("evaluate", evaluate)
graph.add_edge(START, "generate")
graph.add_edge("generate", "evaluate")
graph.add_conditional_edges(
    "evaluate",
    should_continue,
    {"retry": "generate", "done": END},
)
```

---

## マルチエージェント (Supervisor)

**用途**: Supervisorが複数の専門エージェントに作業を割り振るパターン

`langgraph-supervisor` パッケージを使うことで簡潔に構築できる。

```bash
pip install langgraph-supervisor
```

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import InMemorySaver

model = ChatOpenAI(model="gpt-4o")

# 専門エージェントを作成
researcher = create_react_agent(
    model,
    tools=[search_tool],
    name="researcher",
    prompt="あなたは情報収集の専門家です。",
)
writer = create_react_agent(
    model,
    tools=[write_tool],
    name="writer",
    prompt="あなたはコンテンツ作成の専門家です。",
)

# Supervisorワークフローを作成
workflow = create_supervisor(
    agents=[researcher, writer],
    model=model,
    prompt="タスクを適切な専門家に振り分けてください。",
    output_mode="full_history",  # or "last_message"
)
app = workflow.compile(checkpointer=InMemorySaver())

# 実行
config = {"configurable": {"thread_id": "t1"}}
result = app.invoke(
    {"messages": [{"role": "user", "content": "AIの最新動向についてレポートを書いて"}]},
    config=config,
)
```

### 手動でSupervisorを構築する場合

パッケージを使わず自分でSupervisorグラフを構築することもできる。

```python
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.graph.message import add_messages

class SupervisorState(MessagesState):
    next_agent: str  # "researcher" | "writer" | "FINISH"

SUPERVISOR_PROMPT = """あなたはスーパーバイザーです。
以下のエージェントを管理します:
- researcher: 情報収集を担当
- writer: コンテンツ作成を担当
タスクを完了するには "FINISH" と返してください。"""

def supervisor(state: SupervisorState) -> dict:
    result = model.invoke(
        [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"]
    )
    next_agent = result.content.strip()
    return {"next_agent": next_agent, "messages": [result]}

def run_researcher(state: SupervisorState) -> dict:
    result = researcher.invoke({"messages": state["messages"]})
    return {"messages": result["messages"]}

def run_writer(state: SupervisorState) -> dict:
    result = writer.invoke({"messages": state["messages"]})
    return {"messages": result["messages"]}

def route_to_agent(state: SupervisorState) -> str:
    return "end" if state["next_agent"] == "FINISH" else state["next_agent"]

graph = StateGraph(SupervisorState)
graph.add_node("supervisor", supervisor)
graph.add_node("researcher", run_researcher)
graph.add_node("writer", run_writer)
graph.add_edge(START, "supervisor")
graph.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {"researcher": "researcher", "writer": "writer", "end": END},
)
graph.add_edge("researcher", "supervisor")
graph.add_edge("writer", "supervisor")
```

---

## マルチエージェント (Swarm)

**用途**: エージェント同士が直接タスクをハンドオフするパターン（Supervisorなし）

```bash
pip install langgraph-swarm
```

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_swarm, create_handoff_tool
from langgraph.checkpoint.memory import InMemorySaver

model = ChatOpenAI(model="gpt-4o")

# ハンドオフツール付きのエージェントを作成
alice = create_react_agent(
    model,
    name="Alice",
    tools=[
        search_tool,
        create_handoff_tool(agent_name="Bob", description="データ分析が必要な場合はBobに引き継ぐ"),
    ],
    prompt="あなたは情報収集担当のAliceです。",
)

bob = create_react_agent(
    model,
    name="Bob",
    tools=[
        analyze_tool,
        create_handoff_tool(agent_name="Alice", description="追加情報が必要な場合はAliceに引き継ぐ"),
    ],
    prompt="あなたはデータ分析担当のBobです。",
)

# Swarmを作成
workflow = create_swarm(
    agents=[alice, bob],
    default_active_agent="Alice",
)
app = workflow.compile(checkpointer=InMemorySaver())

# 実行
config = {"configurable": {"thread_id": "t1"}}
result = app.invoke(
    {"messages": [{"role": "user", "content": "AIの市場規模を調べて分析して"}]},
    config=config,
)
```

**Supervisor vs Swarm**:
- **Supervisor**: 中央の管理者がタスクを振り分ける。制御しやすいが、トークン消費が多い
- **Swarm**: エージェント同士が直接ハンドオフ。レスポンスが速く、トークン効率が良い

---

## Human-in-the-loop

**用途**: 重要なステップで人間の確認・承認・修正を挟むパターン

```python
from typing_extensions import TypedDict
from typing import Annotated
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

class HumanLoopState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    plan: str
    human_approved: bool

def create_plan(state: HumanLoopState) -> dict:
    """実行計画を作成する。"""
    result = model.invoke("以下のタスクの実行計画を作成: " + state["messages"][-1].content)
    return {"plan": result.content}

def human_review(state: HumanLoopState) -> dict:
    """人間に計画を提示して承認を求める。"""
    # interrupt() でグラフを一時停止し、人間の入力を待つ
    human_input = interrupt({
        "message": "以下の計画を確認してください",
        "plan": state["plan"],
    })
    # human_input は Command(resume=...) で渡された値
    approved = human_input.get("approved", False)
    return {"human_approved": approved}

def execute_plan(state: HumanLoopState) -> dict:
    if not state["human_approved"]:
        return {"messages": [AIMessage(content="計画がキャンセルされました。")]}
    result = model.invoke(f"以下の計画を実行してください:\n{state['plan']}")
    return {"messages": [result]}

graph = StateGraph(HumanLoopState)
graph.add_node("create_plan", create_plan)
graph.add_node("human_review", human_review)
graph.add_node("execute", execute_plan)
graph.add_edge(START, "create_plan")
graph.add_edge("create_plan", "human_review")
graph.add_edge("human_review", "execute")
graph.add_edge("execute", END)

# チェックポインターが必須（中断状態を保存するため）
app = graph.compile(checkpointer=InMemorySaver())

# 実行（interrupt() で一時停止）
config = {"configurable": {"thread_id": "t1"}}
result = app.invoke(
    {"messages": [{"role": "user", "content": "レポートを作成して"}]},
    config=config,
)
# → result に __interrupt__ 情報が含まれる

# 人間が確認後、resume で再開
result = app.invoke(Command(resume={"approved": True}), config)
```

**interrupt() の注意事項**:
- **try/exceptで囲まない** → 例外を伝播させる必要がある
- **チェックポインターが必須** → `InMemorySaver()` または永続チェックポインター
- **thread_idが必須** → 中断状態の復元に使用
- **JSON シリアライズ可能な値のみ** → interrupt() に渡す値
- **interrupt() 前のコードは再実行される** → べき等な処理にすること

---

## サブグラフ

**用途**: 共通の処理フローを再利用可能なサブグラフとして定義する

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# --- サブグラフ定義 ---
class SubState(TypedDict):
    input: str
    result: str

def process_a(state: SubState) -> dict:
    return {"result": f"処理A: {state['input']}"}

def process_b(state: SubState) -> dict:
    return {"result": f"処理B: {state['result']}"}

sub_graph = StateGraph(SubState)
sub_graph.add_node("a", process_a)
sub_graph.add_node("b", process_b)
sub_graph.add_edge(START, "a")
sub_graph.add_edge("a", "b")
sub_graph.add_edge("b", END)
sub_app = sub_graph.compile()

# --- メイングラフで使用 ---
class MainState(TypedDict):
    query: str
    result1: str
    result2: str

def call_sub_for_item1(state: MainState) -> dict:
    result = sub_app.invoke({"input": state["query"], "result": ""})
    return {"result1": result["result"]}

def call_sub_for_item2(state: MainState) -> dict:
    result = sub_app.invoke({"input": state["result1"], "result": ""})
    return {"result2": result["result"]}

main_graph = StateGraph(MainState)
main_graph.add_node("step1", call_sub_for_item1)
main_graph.add_node("step2", call_sub_for_item2)
main_graph.add_edge(START, "step1")
main_graph.add_edge("step1", "step2")
main_graph.add_edge("step2", END)
```

---

## RAGパイプライン

**用途**: ドキュメントを検索して文脈に基づいた回答を生成する

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class RAGState(TypedDict):
    question: str
    retrieved_docs: list[str]
    answer: str

def retrieve(state: RAGState) -> dict:
    """ベクトルDBからドキュメントを検索する。"""
    # 例: FAISS, Chroma, Pinecone など
    # docs = vectorstore.similarity_search(state["question"], k=3)
    docs = [f"検索結果1: {state['question']}に関連する情報"]  # TODO: 実際のVectorStoreに置換
    return {"retrieved_docs": docs}

def generate(state: RAGState) -> dict:
    """検索結果を基に回答を生成する。"""
    context = "\n".join(state["retrieved_docs"])
    prompt = f"""以下のコンテキストを基に質問に回答してください。

コンテキスト:
{context}

質問: {state["question"]}"""
    result = model.invoke(prompt)
    return {"answer": result.content}

graph = StateGraph(RAGState)
graph.add_node("retrieve", retrieve)
graph.add_node("generate", generate)
graph.add_edge(START, "retrieve")
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", END)
app = graph.compile()

result = app.invoke({"question": "LangGraphとは？"})
print(result["answer"])
```
