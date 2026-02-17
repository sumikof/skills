# LangGraph Advanced Patterns (v1.0.8)

## Table of Contents

1. [Subgraphs](#subgraphs)
2. [Send API (Dynamic Fan-Out / Map-Reduce)](#send-api)
3. [Store (Cross-Thread Memory)](#store)
4. [Command (Advanced Usage)](#command-advanced)
5. [Recursion Limit](#recursion-limit)
6. [Graph Visualization](#graph-visualization)
7. [State Design Best Practices](#state-design-best-practices)
8. [Error Handling & Retry](#error-handling--retry)
9. [Message Trimming](#message-trimming)

---

## Subgraphs

Compose graphs within graphs by adding a compiled graph as a node.

### Same state schema (parent and child share state)

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]
    summary: str

# Child graph
def summarize(state: State) -> dict:
    return {"summary": f"Summary of {len(state['messages'])} messages"}

child_builder = StateGraph(State)
child_builder.add_node("summarize", summarize)
child_builder.add_edge(START, "summarize")
child_builder.add_edge("summarize", END)
child_graph = child_builder.compile()

# Parent graph — add compiled child as a node
def chat(state: State) -> dict:
    return {"messages": [{"role": "assistant", "content": "Hello!"}]}

parent_builder = StateGraph(State)
parent_builder.add_node("chat", chat)
parent_builder.add_node("child", child_graph)  # compiled graph as node
parent_builder.add_edge(START, "chat")
parent_builder.add_edge("chat", "child")
parent_builder.add_edge("child", END)

graph = parent_builder.compile()
```

### Different state schemas (state transformation)

When parent and child have different schemas, use a wrapper node to transform state:

```python
class ParentState(TypedDict):
    messages: Annotated[list, add_messages]
    context: str

class ChildState(TypedDict):
    input_text: str
    result: str

child_builder = StateGraph(ChildState)
child_builder.add_node("process", lambda s: {"result": s["input_text"].upper()})
child_builder.add_edge(START, "process")
child_builder.add_edge("process", END)
child_graph = child_builder.compile()

# Wrapper node to bridge state schemas
def call_child(state: ParentState) -> dict:
    child_input = {"input_text": state["context"], "result": ""}
    child_output = child_graph.invoke(child_input)
    return {"messages": [{"role": "assistant", "content": child_output["result"]}]}

parent_builder = StateGraph(ParentState)
parent_builder.add_node("call_child", call_child)
parent_builder.add_edge(START, "call_child")
parent_builder.add_edge("call_child", END)
```

---

## Send API

`Send` enables dynamic fan-out: spawn parallel node executions at runtime based on data.

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

class State(TypedDict):
    topics: list[str]
    results: Annotated[list, lambda a, b: a + b]

# This node is called once per topic (parallel)
def research_topic(state: dict) -> dict:
    # state here is the payload from Send, not the graph state
    return {"results": [f"Research on: {state['topic']}"]}

def fan_out_topics(state: State) -> list[Send]:
    # Return a Send for each topic — all run in parallel
    return [Send("research", {"topic": t}) for t in state["topics"]]

def aggregate(state: State) -> dict:
    return {"results": [f"Aggregated {len(state['results'])} results"]}

builder = StateGraph(State)
builder.add_node("research", research_topic)
builder.add_node("aggregate", aggregate)
builder.add_conditional_edges(START, fan_out_topics)
builder.add_edge("research", "aggregate")
builder.add_edge("aggregate", END)

graph = builder.compile()
result = graph.invoke({"topics": ["AI", "ML", "NLP"], "results": []})
# research runs 3 times in parallel, then aggregate runs once
```

**Key points:**

- `Send(node_name, payload)` — payload becomes the node's input state
- Return `list[Send]` from conditional edge function for parallel execution
- Use a reducer on the collecting field (e.g., `Annotated[list, lambda a, b: a + b]`)
- The Send node receives its own isolated state, not the full graph state

---

## Store

Cross-thread long-term memory via `InMemoryStore` (dev) or a persistent store.

### Setup

```python
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver

store = InMemoryStore()
checkpointer = InMemorySaver()

graph = builder.compile(checkpointer=checkpointer, store=store)
```

### Accessing Store in nodes

```python
from langgraph.store.base import BaseStore

# Option 1: store parameter (injected automatically)
def my_node(state: State, *, store: BaseStore) -> dict:
    # Read
    items = store.search(("memories", "user-123"))
    existing = store.get(("memories", "user-123"), "preference")

    # Write
    store.put(("memories", "user-123"), "preference", {"theme": "dark"})

    # Delete
    store.delete(("memories", "user-123"), "old-key")

    return {"messages": [...]}
```

### Store operations

```python
# put(namespace: tuple, key: str, value: dict)
store.put(("users", "alice"), "profile", {"name": "Alice", "role": "engineer"})

# get(namespace: tuple, key: str) -> Optional[Item]
item = store.get(("users", "alice"), "profile")
if item:
    print(item.value)  # {"name": "Alice", "role": "engineer"}

# search(namespace: tuple, query: str = None) -> list[Item]
items = store.search(("users", "alice"))  # all items in namespace
items = store.search(("users",), query="engineer")  # semantic search

# delete(namespace: tuple, key: str)
store.delete(("users", "alice"), "profile")
```

### Namespace patterns

```python
("memories", user_id)         # per-user memories
("sessions", thread_id)       # per-session data
("facts", user_id, "prefs")   # nested namespace for categories
```

---

## Command Advanced

`Command` enables combined state update + routing from within a node.

### Import and type hints

```python
from typing import Literal
from langgraph.types import Command

# Type hint tells graph/studio which nodes this can route to
def my_node(state: State) -> Command[Literal["node_a", "node_b"]]:
    if state["score"] > 0.8:
        return Command(goto="node_a", update={"status": "high"})
    return Command(goto="node_b", update={"status": "low"})
```

### Command parameters

```python
Command(
    goto="node_name",         # str | list[str] — next node(s)
    update={"key": "value"},  # dict — state update (like returning dict)
    resume="value",           # any — resume an interrupted graph
)
```

### Multi-agent handoff with Command

```python
def agent_a(state: State) -> Command[Literal["agent_b", END]]:
    response = model_a.invoke(state["messages"])
    if needs_specialist(response):
        return Command(
            goto="agent_b",
            update={"messages": [response], "handoff_reason": "needs specialist"}
        )
    return Command(goto=END, update={"messages": [response]})
```

### Command to parent graph (subgraph exit)

```python
from langgraph.types import Command

def child_node(state: ChildState) -> Command:
    # Route back to a node in the parent graph
    return Command(
        goto="parent_node_name",
        update={"result": state["output"]},
        graph=Command.PARENT,  # signal to route in parent graph
    )
```

---

## Recursion Limit

Default: 25 supersteps. A superstep = one node execution.

```python
# Increase for complex multi-step agents
result = graph.invoke(input, config={"recursion_limit": 50})

# Handle gracefully
from langgraph.errors import GraphRecursionError

try:
    result = graph.invoke(input, config={"recursion_limit": 10})
except GraphRecursionError:
    print("Agent exceeded max iterations")
    # Return partial result or ask user to refine
```

---

## Graph Visualization

```python
# Get graph representation
graph_repr = graph.get_graph()

# Mermaid diagram source (paste into mermaid.live or render in markdown)
mermaid_str = graph_repr.draw_mermaid()
print(mermaid_str)

# ASCII art (terminal-friendly, no dependencies)
ascii_str = graph_repr.draw_ascii()
print(ascii_str)

# PNG image (requires internet — uses Mermaid.Ink API by default)
graph_repr.draw_mermaid_png(output_file_path="graph.png")

# In Jupyter notebook
from IPython.display import Image
Image(graph_repr.draw_mermaid_png())
```

---

## State Design Best Practices

### Use reducers for concurrent writes

```python
from operator import add

class State(TypedDict):
    messages: Annotated[list, add_messages]     # built-in message reducer
    results: Annotated[list, lambda a, b: a + b]  # list append reducer
    count: Annotated[int, add]                  # numeric accumulator
```

### Separate ephemeral vs. persistent state

```python
class State(TypedDict):
    # Persistent (accumulates across steps)
    messages: Annotated[list, add_messages]
    final_answer: str

    # Ephemeral (used for routing, overwritten each step)
    current_step: str
    should_retry: bool
```

### Use references, not large objects

```python
# Bad: large content in state bloats checkpoints
class State(TypedDict):
    file_content: bytes  # could be megabytes

# Good: store reference, fetch when needed
class State(TypedDict):
    file_path: str  # lightweight reference
```

### Keep state flat

```python
# Bad: nested objects are hard to update partially
class State(TypedDict):
    user: dict  # {"name": ..., "prefs": {"theme": ...}}

# Good: flat keys
class State(TypedDict):
    user_name: str
    user_theme: str
```

---

## Error Handling & Retry

### RetryPolicy on nodes

```python
from langgraph.types import RetryPolicy

builder.add_node(
    "api_call",
    call_external_api,
    retry_policy=RetryPolicy(
        max_attempts=3,
        initial_interval=1.0,  # seconds
        backoff_factor=2.0,    # exponential backoff
    ),
)
```

### Manual error handling in nodes

```python
def resilient_node(state: State) -> dict:
    try:
        result = call_external_service(state["query"])
        return {"result": result, "error": ""}
    except Exception as e:
        return {"result": "", "error": str(e)}

def route_after_call(state: State) -> str:
    if state["error"]:
        return "fallback"
    return "next_step"

builder.add_conditional_edges("api_call", route_after_call)
```

### Tool error handling

```python
from langchain_core.messages import ToolMessage

def tool_node(state: State) -> dict:
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        try:
            result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
            content = json.dumps(result)
        except Exception as e:
            content = f"Error calling {tool_call['name']}: {e}"
        outputs.append(ToolMessage(
            content=content,
            name=tool_call["name"],
            tool_call_id=tool_call["id"],
        ))
    return {"messages": outputs}
```

---

## Message Trimming

Prevent unbounded message growth in long-running agents:

```python
from langchain_core.messages import trim_messages

def call_model(state: State) -> dict:
    trimmed = trim_messages(
        state["messages"],
        max_tokens=4000,
        token_counter=model,  # uses model's tokenizer
        strategy="last",      # keep most recent messages
        include_system=True,  # always keep system message
    )
    response = model.invoke(trimmed)
    return {"messages": [response]}
```

Alternative: summarize old messages instead of trimming:

```python
def maybe_summarize(state: State) -> dict:
    msgs = state["messages"]
    if len(msgs) > 20:
        summary = model.invoke(
            f"Summarize this conversation:\n{msgs[:15]}"
        )
        # Replace old messages with summary + keep recent
        return {"messages": [summary] + msgs[15:]}
    return {}
```
