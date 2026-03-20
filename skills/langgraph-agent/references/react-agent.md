# ReActエージェント (LangGraph 1.0+)

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

## モデルの文字列指定

モデルオブジェクトの代わりに `"provider:model"` 形式の文字列で指定できる。

```python
# 文字列でモデルを指定
agent = create_react_agent("openai:gpt-4o-mini", tools)

# 他のプロバイダーの例
agent = create_react_agent("anthropic:claude-sonnet-4-5-20250929", tools)
```

## システムプロンプトの設定

```python
# 文字列で指定（推奨）
agent = create_react_agent(
    model,
    tools,
    prompt="あなたは日本語で回答するAIアシスタントです。",
)

# SystemMessageで指定
from langchain_core.messages import SystemMessage

agent = create_react_agent(
    model,
    tools,
    prompt=SystemMessage(content="あなたは日本語で回答するAIアシスタントです。"),
)
```

## 会話履歴の保持

```python
from langgraph.checkpoint.memory import InMemorySaver

memory = InMemorySaver()
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
# メッセージ単位のストリーミング（LLMトークンをリアルタイムに取得）
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "東京の天気を調べて"}]},
    config=config,
    stream_mode="messages",
):
    msg, metadata = chunk
    if msg.content and metadata.get("langgraph_node") == "agent":
        print(msg.content, end="", flush=True)

# ステップ単位のストリーミング
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "東京の天気を調べて計算して"}]},
    config=config,
    stream_mode="updates",
):
    print(chunk)
```

## ツール定義のパターン

### 基本的なツール
```python
@tool
def search(query: str) -> str:
    """ウェブで情報を検索する。質問への回答に必要な情報を取得するために使用。"""
    return f"検索結果: {query}"
```

### 外部API呼び出し（非同期）
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

### グラフのステートを更新するツール（Command）
```python
from langgraph.types import Command

@tool
def set_language(language: str) -> Command:
    """ユーザーの言語設定を変更する。"""
    return Command(update={"language": language})
```

### ステートを参照するツール（InjectedState）
```python
from langgraph.prebuilt import InjectedState
from typing import Annotated

@tool
def get_context(
    query: str,
    state: Annotated[dict, InjectedState],  # LLMからは見えない
) -> str:
    """コンテキストに基づいて情報を取得する。"""
    context = state.get("context", "")
    return f"コンテキスト: {context}, クエリ: {query}"
```

## 構造化出力（response_format）

エージェントの最終回答を特定の構造に強制する。

```python
from pydantic import BaseModel

class WeatherResponse(BaseModel):
    city: str
    temperature: float
    condition: str

agent = create_react_agent(
    model,
    tools,
    response_format=WeatherResponse,
)

result = agent.invoke({"messages": [{"role": "user", "content": "東京の天気は？"}]})
# result["structured_response"] に WeatherResponse が入る
```

## pre_model_hook / post_model_hook

エージェントのモデル呼び出しの前後にカスタム処理を挟む。

```python
def filter_messages(state):
    """モデルに渡すメッセージを最新10件に制限する。"""
    return {"messages": state["messages"][-10:]}

def log_response(state):
    """モデルの回答をログに記録する。"""
    last = state["messages"][-1]
    print(f"[LOG] {last.content[:100]}")
    return state

agent = create_react_agent(
    model,
    tools,
    pre_model_hook=filter_messages,
    post_model_hook=log_response,
)
```

## 状態の確認

```python
# 最終状態を取得
state = agent.get_state(config)
print(state.values["messages"])  # 全メッセージ履歴
```

## create_react_agent のパラメータ一覧

| パラメータ | 型 | 説明 |
|---|---|---|
| `model` | `str` / `LanguageModelLike` | モデル（文字列 or オブジェクト） |
| `tools` | `Sequence[BaseTool]` | ツールのリスト |
| `prompt` | `str` / `SystemMessage` / `Callable` | システムプロンプト |
| `response_format` | `type[BaseModel]` | 構造化出力のスキーマ |
| `pre_model_hook` | `RunnableLike` | モデル呼び出し前の処理 |
| `post_model_hook` | `RunnableLike` | モデル呼び出し後の処理 |
| `state_schema` | `type[TypedDict]` | カスタムステートスキーマ |
| `checkpointer` | `BaseCheckpointSaver` | 会話履歴の保存先 |
| `store` | `BaseStore` | スレッド横断の永続ストレージ |
| `interrupt_before` | `list[str]` | 指定ノード実行前に中断 |
| `interrupt_after` | `list[str]` | 指定ノード実行後に中断 |
| `name` | `str` | グラフの識別名 |
