# LangGraph StateGraph API Reference (v1.0.8)

## Table of Contents
1. [State Definition](#state-definition)
2. [StateGraph Builder](#stategraph-builder)
3. [add_node](#add_node)
4. [add_edge](#add_edge)
5. [add_conditional_edges](#add_conditional_edges)
6. [add_sequence](#add_sequence)
7. [compile](#compile)
8. [Execution Methods](#execution-methods)
9. [Functional API](#functional-api)

---

## State Definition

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from operator import add

class State(TypedDict):
    messages: Annotated[list, add_messages]       # reducer: dedup by ID, merge
    count: int                                     # no reducer: last-write-wins
    items: Annotated[list, lambda a, b: a + b]    # custom reducer: append
    total: Annotated[int, add]                     # numeric accumulator
```

Rules:
- Nodes return `dict` with **partial** state updates (only changed keys).
- `add_messages` deduplicates messages by ID and handles HumanMessage, AIMessage, ToolMessage correctly.
- Without a reducer, concurrent writes cause last-write-wins (data loss in parallel nodes).

---

## StateGraph Builder

```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(State)
# START = entry sentinel, END = exit sentinel
```

---

## add_node

```python
builder.add_node(node_or_name, action=None, *, retry_policy=None, cache_policy=None)
```

| Arg | Description |
|-----|-------------|
| `node_or_name` | Function (name inferred) or string name |
| `action` | Callable when first arg is a string |
| `retry_policy` | `RetryPolicy(max_attempts=3)` — auto-retry on exception |
| `cache_policy` | `CachePolicy()` — cache output by hashing inputs |

```python
from langgraph.types import RetryPolicy, CachePolicy

builder.add_node(my_fn)                                         # name = "my_fn"
builder.add_node("step1", my_fn)                               # explicit name
builder.add_node(my_fn, retry_policy=RetryPolicy(max_attempts=3, initial_interval=1.0))
builder.add_node(my_fn, cache_policy=CachePolicy())
```

**Node signatures:**
```python
# Basic
def my_node(state: State) -> dict:
    return {"count": state["count"] + 1}

# With runtime config (model name, user ID, etc.)
from langchain_core.runnables import RunnableConfig
def my_node(state: State, config: RunnableConfig) -> dict:
    model = config.get("configurable", {}).get("model", "gpt-4o")
    return {"result": call_model(state, model)}

# With Store (cross-thread memory)
from langgraph.store.base import BaseStore
def my_node(state: State, *, store: BaseStore) -> dict:
    items = store.search(("memories", "user-1"))
    store.put(("memories", "user-1"), "key", {"value": "data"})
    return {}
```

---

## add_edge

```python
builder.add_edge(start_key, end_key)
```

```python
builder.add_edge(START, "first_node")          # entry point
builder.add_edge("node_a", "node_b")           # simple chain
builder.add_edge("last_node", END)             # exit
builder.add_edge(["node_a", "node_b"], "merger")  # fan-in: wait for BOTH
```

---

## add_conditional_edges

```python
builder.add_conditional_edges(source, path_fn, path_map=None)
```

```python
# Single destination
def router(state: State) -> str:
    return "done" if state["count"] > 10 else "continue"

builder.add_conditional_edges("processor", router, {"done": END, "continue": "processor"})

# Fan-out: parallel execution
def fan_out(state: State) -> list[str]:
    return ["branch_a", "branch_b", "branch_c"]

builder.add_conditional_edges("dispatcher", fan_out)

# Using Command return type (no need for separate edge declaration)
from typing import Literal
from langgraph.types import Command

def smart_node(state: State) -> Command[Literal["node_a", "node_b"]]:
    if state["score"] > 0.8:
        return Command(goto="node_a", update={"tier": "high"})
    return Command(goto="node_b", update={"tier": "low"})
```

---

## add_sequence

Convenience method: chain a list of nodes in order.

```python
builder.add_sequence([step_one, step_two, step_three])
# Equivalent to: add_node(x) + add_edge for each
```

---

## compile

```python
graph = builder.compile(
    checkpointer=None,        # enables persistence + HITL
    store=None,               # cross-thread long-term memory
    interrupt_before=None,    # list[str]: pause BEFORE these nodes
    interrupt_after=None,     # list[str]: pause AFTER these nodes
    debug=False,              # verbose logging
    name=None,                # name for observability
)
```

**Checkpointers:**
```python
from langgraph.checkpoint.memory import InMemorySaver      # dev (in-process)
from langgraph.checkpoint.sqlite import SqliteSaver         # lightweight prod
from langgraph.checkpoint.postgres import PostgresSaver     # distributed prod

graph = builder.compile(checkpointer=InMemorySaver())
```

**interrupt_before / interrupt_after:**
```python
graph = builder.compile(
    checkpointer=InMemorySaver(),
    interrupt_before=["human_review"],  # pause before node runs
    # interrupt_after=["draft"],        # pause after node runs
)
```

---

## Execution Methods

```python
config = {"configurable": {"thread_id": "session-1"}}

# Synchronous
result = graph.invoke(initial_state, config)
result = graph.invoke(initial_state, config, {"recursion_limit": 50})

# Streaming
for chunk in graph.stream(initial_state, config, stream_mode="updates"):
    print(chunk)  # per-node output dicts

# Streaming modes:
# "values"  — full state after each node
# "updates" — only changes from each node (most useful for debugging)
# "messages" — token-level LLM output

# Async
result = await graph.ainvoke(initial_state, config)
async for chunk in graph.astream(initial_state, config):
    print(chunk)

# State inspection (requires checkpointer)
state = graph.get_state(config)            # current state snapshot
state.values                               # state dict
state.next                                 # next nodes to run
graph.update_state(config, {"count": 0})  # manually update state
graph.update_state(config, {"x": 1}, as_node="node_name")  # update as if node ran

# Time-travel
for snapshot in graph.get_state_history(config):
    print(snapshot.config["configurable"]["checkpoint_id"])

# Visualization
print(graph.get_graph().draw_mermaid())    # Mermaid diagram
print(graph.get_graph().draw_ascii())      # ASCII art
graph.get_graph().draw_mermaid_png(output_file_path="graph.png")
```

---

## Functional API

Alternative to graph builder. Better for imperative-style logic.

```python
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

@task
def fetch_data(query: str) -> str:
    """Discrete unit of async-safe work."""
    return f"data for: {query}"

@task
def process(data: str) -> str:
    return data.upper()

@entrypoint(checkpointer=InMemorySaver())
def workflow(query: str) -> dict:
    data = fetch_data(query).result()

    # HITL works inside @entrypoint too
    approval = interrupt({"data": data, "question": "Proceed?"})
    if not approval:
        return {"result": "cancelled"}

    result = process(data).result()
    return {"result": result}

config = {"configurable": {"thread_id": "func-001"}}
workflow.invoke("search query", config)           # runs until interrupt
workflow.invoke(Command(resume=True), config)     # resume after approval
```
