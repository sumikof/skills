"""
カスタムグラフ テンプレート (LangGraph 1.0)

このテンプレートは以下のパターンを示します:
  - カスタムステート定義
  - 複数ノードのパイプライン
  - 条件分岐エッジ
  - ツールノードの統合

使い方:
  1. OPENAI_API_KEY を環境変数に設定
  2. State と各ノード関数をカスタマイズ
  3. python custom_graph.py で実行

依存関係:
  pip install langgraph langchain-openai langchain-core python-dotenv
"""

from typing import Annotated, Literal
from typing_extensions import TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# ---- ステート定義 ----
# ユーザの要件に合わせてフィールドを追加・変更してください

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    # 追加フィールドの例:
    # user_intent: str       # ユーザの意図を分類
    # context: str           # 追加コンテキスト
    # iteration_count: int   # ループ回数管理


# ---- ツール定義 ----

@tool
def search(query: str) -> str:
    """指定したクエリで情報を検索する。"""
    # TODO: 実際の検索APIに置き換える
    return f"「{query}」の検索結果: サンプルデータです。"


@tool
def summarize(text: str) -> str:
    """長いテキストを要約する。"""
    return f"要約: {text[:100]}..." if len(text) > 100 else text


tools = [search, summarize]

# ---- モデル設定 ----

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
model_with_tools = model.bind_tools(tools)


# ---- ノード関数 ----

SYSTEM_PROMPT = """あなたは役立つAIアシスタントです。
ユーザの質問に対して、必要に応じてツールを使いながら丁寧に回答してください。"""

def call_model(state: State) -> dict:
    """LLMを呼び出すノード。"""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}


# ツールノード（ToolNodeはtool callを自動的に処理する）
tool_node = ToolNode(tools)


# ---- グラフ構築 ----

def build_graph() -> StateGraph:
    """グラフを構築してコンパイル済みアプリを返す。"""
    graph = StateGraph(State)

    # ノードを追加
    graph.add_node("model", call_model)
    graph.add_node("tools", tool_node)

    # エントリポイント
    graph.add_edge(START, "model")

    # 条件分岐: ツール呼び出しがあれば tools ノードへ、なければ終了
    graph.add_conditional_edges(
        "model",
        tools_condition,  # "tools" または END を返す
    )

    # ツール実行後はモデルに戻る
    graph.add_edge("tools", "model")

    return graph


def main():
    graph = build_graph()

    # チェックポインターで会話履歴を保持
    memory = MemorySaver()
    app = graph.compile(checkpointer=memory)

    # グラフ構造を確認（デバッグ用）
    print("グラフ構造:")
    print(app.get_graph().draw_ascii())
    print("-" * 50)

    thread_id = "session-1"
    config = {"configurable": {"thread_id": thread_id}}

    print("エージェントが起動しました。'quit' で終了します。")

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit", "終了"):
            print("終了します。")
            break

        result = app.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
        )

        print(f"Agent: {result['messages'][-1].content}")
        print()


if __name__ == "__main__":
    main()
