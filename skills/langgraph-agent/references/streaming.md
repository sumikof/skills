# ストリーミング (LangGraph 1.0+)

LangGraphのストリーミングAPIの使い方ガイド。

## ストリームモード一覧

| モード | 説明 | 主な用途 |
|---|---|---|
| `"values"` | 各ステップ後の完全なステート | デバッグ、全体の状態確認 |
| `"updates"` | ステートの差分のみ | ノードごとの出力確認 |
| `"messages"` | LLMトークンをリアルタイムに取得 | チャットUI、リアルタイム表示 |
| `"custom"` | ノード内から任意のデータを送信 | 進捗バー、カスタム通知 |
| `"debug"` | 最大限の実行詳細 | 詳細デバッグ |

## values モード

各ステップ実行後の完全なステートを取得する。

```python
for state in app.stream(
    {"messages": [{"role": "user", "content": "こんにちは"}]},
    config=config,
    stream_mode="values",
):
    # state は完全なステートオブジェクト
    print(state["messages"][-1].content)
```

## updates モード

各ノードが返した差分のみを取得する。ノード名がキーになる。

```python
for step in app.stream(
    {"messages": [{"role": "user", "content": "こんにちは"}]},
    config=config,
    stream_mode="updates",
):
    for node_name, output in step.items():
        print(f"[{node_name}] {output}")
```

## messages モード

LLMのトークンをリアルタイムに取得する。チャットUIに最適。

```python
for chunk in app.stream(
    {"messages": [{"role": "user", "content": "こんにちは"}]},
    config=config,
    stream_mode="messages",
):
    msg, metadata = chunk
    # metadata["langgraph_node"] でどのノードからの出力か判別
    if msg.content and metadata.get("langgraph_node") == "agent":
        print(msg.content, end="", flush=True)
```

## custom モード

ノード内から `get_stream_writer()` を使って任意のデータを送信する。

```python
from langgraph.config import get_stream_writer

def processing_node(state):
    writer = get_stream_writer()

    # 進捗を通知
    writer({"progress": "ステップ1完了", "percent": 33})
    result1 = do_step1()

    writer({"progress": "ステップ2完了", "percent": 66})
    result2 = do_step2()

    writer({"progress": "完了", "percent": 100})
    return {"result": result2}

# custom モードでストリーミング
for chunk in app.stream(
    initial_state,
    config=config,
    stream_mode="custom",
):
    print(chunk)  # {"progress": "ステップ1完了", "percent": 33} など
```

## 複数モードの同時使用

複数のストリームモードを同時に指定すると、タプルで `(mode, chunk)` が返る。

```python
for mode, chunk in app.stream(
    {"messages": [{"role": "user", "content": "こんにちは"}]},
    config=config,
    stream_mode=["updates", "messages"],
):
    if mode == "messages":
        msg, metadata = chunk
        if msg.content:
            print(msg.content, end="", flush=True)
    elif mode == "updates":
        for node_name, output in chunk.items():
            print(f"\n[{node_name}] completed")
```

## サブグラフのストリーミング

`subgraphs=True` を指定すると、サブグラフ内のイベントも取得できる。

```python
for chunk in app.stream(
    initial_state,
    config=config,
    stream_mode="updates",
    subgraphs=True,
):
    # namespace でサブグラフの階層が分かる
    print(chunk)
```

## 非同期ストリーミング

```python
async for chunk in app.astream(
    {"messages": [{"role": "user", "content": "こんにちは"}]},
    config=config,
    stream_mode="messages",
):
    msg, metadata = chunk
    if msg.content:
        print(msg.content, end="", flush=True)
```

## ストリームモードの選び方

| 目的 | 推奨モード |
|---|---|
| チャットUIでリアルタイム表示 | `"messages"` |
| 各ノードの処理結果を確認 | `"updates"` |
| デバッグ時に全体の状態を確認 | `"values"` or `"debug"` |
| カスタム進捗表示 | `"custom"` |
| 本番のチャットUI + 進捗 | `["messages", "custom"]` |
