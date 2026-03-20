"""
ReActエージェント テンプレート (LangGraph 1.0+)

使い方:
  1. OPENAI_API_KEY を環境変数に設定
  2. ツールをカスタマイズ（search, calculate など）
  3. python react_agent.py で実行

依存関係:
  pip install langgraph langchain-openai langchain-core python-dotenv

必須: Python 3.10+
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

# 環境変数を読み込む
load_dotenv()

# ---- ツール定義 ----
# ユーザの要件に合わせてツールを追加・変更してください


@tool
def search(query: str) -> str:
    """指定したクエリでウェブ検索を行い、情報を取得する。"""
    # TODO: 実際の検索APIに置き換える（例: Tavily, SerpAPI など）
    return f"「{query}」の検索結果: サンプルデータです。実際の検索APIを接続してください。"


@tool
def calculate(expression: str) -> str:
    """数式を計算して結果を返す。例: '10 * 3 + 5'"""
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"計算結果: {expression} = {result}"
    except Exception as e:
        return f"計算エラー: {e}"


# ---- エージェント設定 ----


def create_agent():
    """ReActエージェントを作成して返す。"""
    model = ChatOpenAI(
        model="gpt-4o-mini",  # 必要に応じて "gpt-4o" に変更
        temperature=0,
    )

    tools = [search, calculate]

    # 会話履歴を保持するメモリ（開発用）
    # 本番では SqliteSaver や PostgresSaver を使用
    memory = InMemorySaver()

    agent = create_react_agent(
        model=model,
        tools=tools,
        checkpointer=memory,
        # システムプロンプトを設定する場合:
        # prompt="あなたは日本語で回答するAIアシスタントです。",
    )

    return agent


# ---- 実行 ----


def main():
    agent = create_agent()
    thread_id = "session-1"  # 会話セッションID
    config = {"configurable": {"thread_id": thread_id}}

    print("エージェントが起動しました。'quit' で終了します。")
    print("-" * 50)

    while True:
        user_input = input("You: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit", "終了"):
            print("終了します。")
            break

        # ストリーミングでリアルタイム出力
        print("Agent: ", end="", flush=True)
        for chunk in agent.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            stream_mode="messages",
        ):
            msg, metadata = chunk
            if msg.content and metadata.get("langgraph_node") == "agent":
                print(msg.content, end="", flush=True)
        print("\n")


if __name__ == "__main__":
    main()
