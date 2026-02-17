# ReActエージェント (LangGraph 1.0)

`create_react_agent` を使ったprebuilt ReActエージェントの実装ガイド。

## 基本構造

```python
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# 1. ツールを定義
@tool
def get_weather(city: str) -> str:
    """指定した都市の天気を取得する。"""
    return f"{city}の天気: 晴れ、25°C"

@tool
def calculate(expression: str) -> str:
    """数式を計算する。例: '2 + 2'"""
    return str(eval(expression))

# 2. モデルとツールを設定
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
tools = [get_weather, calculate]

# 3. エージェントを作成
agent = create_react_agent(model, tools)

# 4. 実行
result = agent.invoke({
    "messages": [{"role": "user", "content": "東京の天気は？"}]
})
print(result["messages"][-1].content)
```

## システムプロンプトの設定

```python
from langchain_core.messages import SystemMessage

agent = create_react_agent(
    model,
    tools,
    prompt=SystemMessage(content="あなたは日本語で回答するAIアシスタントです。")
)
```

## 会話履歴の保持

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
agent = create_react_agent(model, tools, checkpointer=memory)

config = {"configurable": {"thread_id": "session-1"}}

# 1回目
agent.invoke({"messages": [{"role": "user", "content": "私の名前は太郎です"}]}, config=config)

# 2回目（前の会話を覚えている）
result = agent.invoke({"messages": [{"role": "user", "content": "私の名前は？"}]}, config=config)
print(result["messages"][-1].content)  # "太郎"
```

## ストリーミング出力

```python
# メッセージをストリーミング
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "東京の天気を調べて計算して"}]},
    stream_mode="values"
):
    chunk["messages"][-1].pretty_print()
```

## ツール定義のパターン

### 外部API呼び出し
```python
import httpx

@tool
async def search_web(query: str) -> str:
    """ウェブ検索を実行する。"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/search?q={query}")
        return response.json()["results"]
```

### 入力スキーマ付き
```python
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="検索クエリ")
    limit: int = Field(default=5, description="取得件数")

@tool(args_schema=SearchInput)
def search(query: str, limit: int = 5) -> str:
    """ドキュメントを検索する。"""
    return f"検索結果: {query} ({limit}件)"
```

## 状態の確認

```python
# 最終状態を取得
state = agent.get_state(config)
print(state.values["messages"])  # 全メッセージ履歴
```

## カスタマイズポイント

| 項目 | 方法 |
|---|---|
| モデル変更 | `ChatOpenAI(model="gpt-4o")` |
| 温度設定 | `ChatOpenAI(temperature=0)` |
| ツール追加 | `tools` リストに追加 |
| プロンプト変更 | `prompt=` 引数 |
| 再帰制限 | `create_react_agent(model, tools, max_iterations=10)` |
