# Functional API (LangGraph 1.0+)

`@entrypoint` と `@task` を使ったシンプルなワークフロー構築ガイド。StateGraphの代替として、通常のPython制御フローでワークフローを定義できる。

## StateGraph との使い分け

| 特徴 | StateGraph | Functional API |
|---|---|---|
| 定義方法 | グラフ（ノード＋エッジ） | 通常のPython関数 |
| 状態管理 | TypedDict + リデューサー | 関数のローカル変数 |
| 可視化 | `draw_ascii()` / `draw_mermaid()` | 不可（動的なため） |
| 適した場面 | 複雑な分岐・ループ・並列処理 | シンプルな順次処理 |
| チェックポイント | ノード単位で自動 | `@task` の結果を自動保存 |

## 基本構造

```python
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver

@task
def fetch_data(url: str) -> str:
    """データを取得する（チェックポイントされる）。"""
    import httpx
    response = httpx.get(url)
    return response.text

@task
def process_data(data: str) -> str:
    """データを処理する。"""
    return data.upper()

@entrypoint(checkpointer=InMemorySaver())
def workflow(url: str) -> str:
    """メインのワークフロー。"""
    data = fetch_data(url).result()      # .result() で結果を取得
    processed = process_data(data).result()
    return processed

# 実行
config = {"configurable": {"thread_id": "t1"}}
result = workflow.invoke("https://example.com/data", config)
print(result)
```

## @task デコレータ

`@task` で修飾した関数は：
- 結果が自動的にチェックポイントされる
- 再実行時にキャッシュから結果を返す（べき等性を保証）
- `.result()` で結果を取得する

```python
@task
def step1(input: str) -> str:
    return f"処理1: {input}"

@task
def step2(input: str) -> str:
    return f"処理2: {input}"

@entrypoint(checkpointer=InMemorySaver())
def pipeline(data: str) -> str:
    r1 = step1(data).result()
    r2 = step2(r1).result()
    return r2
```

## Human-in-the-loop（interrupt）

Functional APIでも `interrupt()` が使える。

```python
from langgraph.func import entrypoint, task
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

@task
def write_essay(topic: str) -> str:
    """エッセイを書く。"""
    return f"{topic}についてのエッセイ: ..."

@entrypoint(checkpointer=InMemorySaver())
def workflow(topic: str) -> dict:
    essay = write_essay(topic).result()

    # 人間の承認を待つ
    is_approved = interrupt({
        "message": "以下のエッセイを確認してください",
        "essay": essay,
    })

    return {"essay": essay, "approved": is_approved}

# 実行（interrupt で一時停止）
config = {"configurable": {"thread_id": "t1"}}
result = workflow.invoke("AI倫理", config)
# → __interrupt__ が返る

# 承認して再開
result = workflow.invoke(Command(resume=True), config)
```

## 返り値とチェックポイントの分離（entrypoint.final）

ワークフローの返り値とチェックポイントに保存する値を分離できる。

```python
from langgraph.func import entrypoint

@entrypoint(checkpointer=InMemorySaver())
def workflow(query: str) -> entrypoint.final[str, dict]:
    """返り値は str、チェックポイントには dict を保存。"""
    result = process(query)
    history = {"query": query, "result": result, "timestamp": "..."}

    # value=ユーザーへの返り値, save=チェックポイントに保存する値
    return entrypoint.final(value=result, save=history)
```

## 並列実行

複数のタスクを並列に実行する場合。

```python
@task
def analyze_sentiment(text: str) -> str:
    return "positive"

@task
def extract_keywords(text: str) -> list[str]:
    return ["AI", "LangGraph"]

@entrypoint(checkpointer=InMemorySaver())
def parallel_workflow(text: str) -> dict:
    # タスクを同時に起動
    sentiment_future = analyze_sentiment(text)
    keywords_future = extract_keywords(text)

    # 結果を待つ
    return {
        "sentiment": sentiment_future.result(),
        "keywords": keywords_future.result(),
    }
```

## Functional API を使うべき場面

- シンプルな順次処理（A → B → C）
- 通常のPythonの `if/for/while` で十分な制御フロー
- グラフの可視化が不要
- 既存のPythonコードをワークフロー化したい

## StateGraph を使うべき場面

- 複雑な条件分岐・ルーティング
- 動的なグラフ構造が必要
- グラフの可視化でデバッグしたい
- マルチエージェントパターン
- ToolNode / tools_condition を使いたい
