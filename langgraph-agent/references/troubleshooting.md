# LangGraph Troubleshooting & Debugging (v1.0.8)

## Table of Contents
1. [Common Errors](#common-errors)
2. [Debugging Techniques](#debugging-techniques)
3. [Performance Tuning](#performance-tuning)
4. [State Design Pitfalls](#state-design-pitfalls)
5. [Checkpointer Issues](#checkpointer-issues)
6. [Streaming Pitfalls](#streaming-pitfalls)

---

## Common Errors

### `ValueError: Checkpointer required`

```
ValueError: This graph requires a checkpointer to use interrupt()
```

**Cause**: `interrupt()` used without a checkpointer in `compile()`.
**Fix**:
```python
from langgraph.checkpoint.memory import InMemorySaver
graph = builder.compile(checkpointer=InMemorySaver())
```

### `GraphRecursionError: Recursion limit reached`

```
GraphRecursionError: Recursion limit of 25 reached without hitting a stop condition
```

**Cause**: Agent loop iterating too many times (infinite tool-call loop, or complex workflow).
**Fix**:
```python
# Increase limit
result = graph.invoke(input, config={"recursion_limit": 50})

# Or fix the root cause: ensure the routing function eventually returns END
def should_continue(state):
    if len(state["messages"]) > 20:  # safety cap
        return END
    return "tools" if state["messages"][-1].tool_calls else END
```

### `InvalidUpdateError: Expected dict, got ...`

**Cause**: Node returned something other than a `dict`.
**Fix**: Ensure every node returns `dict` with state keys:
```python
# Wrong
def my_node(state):
    return "done"

# Correct
def my_node(state):
    return {"result": "done"}
```

### `KeyError` in State access

**Cause**: Accessing a state key that wasn't initialized.
**Fix**: Provide defaults in initial state, or use `.get()`:
```python
# Option 1: Initialize all keys
graph.invoke({"messages": [], "count": 0, "result": ""})

# Option 2: Use Optional in TypedDict
class State(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    result: str  # optional, may not exist
```

### `ToolException: Tool ... not found`

**Cause**: LLM generated a tool call for a tool not registered in the graph.
**Fix**:
```python
# Verify tool names match
print([t.name for t in tools])  # check registered names

# Add error handling in tool node
def tool_node(state):
    for tool_call in state["messages"][-1].tool_calls:
        if tool_call["name"] not in tools_by_name:
            return {"messages": [ToolMessage(
                content=f"Error: Unknown tool '{tool_call['name']}'",
                tool_call_id=tool_call["id"],
            )]}
        ...
```

### `interrupt()` inside try/except silently fails

**Cause**: `interrupt()` raises a special exception internally. Catching it prevents the pause.
**Fix**: Never wrap `interrupt()` in try/except:
```python
# Wrong
def review(state):
    try:
        decision = interrupt({"draft": state["draft"]})
    except Exception:
        decision = {"approved": False}

# Correct
def review(state):
    decision = interrupt({"draft": state["draft"]})
    ...
```

---

## Debugging Techniques

### Enable debug mode

```python
# At compile time
graph = builder.compile(debug=True)

# Or per-invocation via config
graph.invoke(input, config={"debug": True})
```
Debug mode logs each node execution, state transitions, and routing decisions.

### Graph visualization

```python
# Mermaid diagram (paste into mermaid.live)
print(graph.get_graph().draw_mermaid())

# ASCII art (terminal-friendly)
print(graph.get_graph().draw_ascii())

# PNG image (requires graphviz + pygraphviz or grandalf)
graph.get_graph().draw_mermaid_png(output_file_path="graph.png")
```

### Inspect state at any point

```python
config = {"configurable": {"thread_id": "debug-session"}}
graph = builder.compile(checkpointer=InMemorySaver())

# After invocation
state = graph.get_state(config)
print("Current values:", state.values)
print("Next nodes:", state.next)
print("Tasks:", state.tasks)

# Full execution history
for snapshot in graph.get_state_history(config):
    print(f"Checkpoint: {snapshot.config['configurable']['checkpoint_id']}")
    print(f"  Values: {snapshot.values}")
    print(f"  Next: {snapshot.next}")
    print()
```

### Step-by-step streaming

```python
# stream_mode="updates" shows per-node output
for step in graph.stream(input, config, stream_mode="updates"):
    node_name = list(step.keys())[0]
    node_output = step[node_name]
    print(f"[{node_name}] -> {node_output}")
```

### Add logging to nodes

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("langgraph")

def my_node(state):
    logger.debug(f"Entering my_node with state keys: {list(state.keys())}")
    logger.debug(f"Messages count: {len(state.get('messages', []))}")
    # ... node logic
    result = {"count": state["count"] + 1}
    logger.debug(f"my_node returning: {result}")
    return result
```

---

## Performance Tuning

### Recursion limit

Default is 25. Set based on expected max iterations:
```python
# For complex multi-tool agents that need many steps
config = {"recursion_limit": 100}
```

### Parallel tool execution

Tools are executed sequentially by default in manual graphs. For parallel:
```python
import asyncio

async def tool_node(state):
    tool_calls = state["messages"][-1].tool_calls
    tasks = [
        asyncio.to_thread(tools_by_name[tc["name"]].invoke, tc["args"])
        for tc in tool_calls
    ]
    results = await asyncio.gather(*tasks)
    return {"messages": [
        ToolMessage(content=json.dumps(r), name=tc["name"], tool_call_id=tc["id"])
        for r, tc in zip(results, tool_calls)
    ]}
```

Or use `create_react_agent` with `version="v1"` for built-in parallel tool execution.

### Reduce state size

Large states slow down checkpointing and serialization:
```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
    # Don't store large objects (file contents, images) in state.
    # Instead, store references (file paths, URLs).
    file_path: str  # good: reference
    # file_content: bytes  # bad: large blob in state
```

### Trim message history

Prevent unbounded message growth:
```python
from langchain_core.messages import trim_messages

def call_model(state):
    trimmed = trim_messages(
        state["messages"],
        max_tokens=4000,
        token_counter=model,
        strategy="last",
        include_system=True,
    )
    response = model.invoke(trimmed)
    return {"messages": [response]}
```

---

## State Design Pitfalls

### Reducer conflicts
```python
# Problem: Two parallel nodes both append to same list
# without a reducer → last-write-wins, data lost

# Solution: Use a reducer
class State(TypedDict):
    results: Annotated[list, lambda a, b: a + b]  # merge via concatenation
```

### Mutable default state
```python
# Problem: Sharing a mutable default
DEFAULT = {"items": []}  # shared reference!

# Solution: Create fresh state per invocation
graph.invoke({"items": []})  # new list each time
```

### Overly broad state
```python
# Problem: Everything in one flat state
class State(TypedDict):
    messages: ...
    user_name: str
    user_email: str
    draft: str
    search_results: list
    final_answer: str
    error: str
    retry_count: int
    # ... 20 more fields

# Better: Only include what's needed for routing and node communication
class State(TypedDict):
    messages: Annotated[list, add_messages]
    phase: str  # "research" | "draft" | "review"
    final_answer: str
```

---

## Checkpointer Issues

### State not persisting (InMemorySaver)

`InMemorySaver` is in-process only. State disappears when the process exits.
For persistence across restarts, use `SqliteSaver` or `PostgresSaver`.

### Thread ID collisions

Different users sharing the same `thread_id` will see each other's state:
```python
# Wrong: static thread_id
config = {"configurable": {"thread_id": "main"}}

# Correct: unique per user/session
import uuid
config = {"configurable": {"thread_id": f"user-{user_id}-{uuid.uuid4()}"}}
```

### PostgresSaver connection pool exhaustion

```python
# Use connection pooling for concurrent access
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

pool = ConnectionPool("postgresql://user:pass@localhost/db", min_size=2, max_size=10)
checkpointer = PostgresSaver(pool)
```

---

## Streaming Pitfalls

### `stream_mode` confusion

| Mode | Returns |
|------|---------|
| `"values"` | Full state after each node |
| `"updates"` | Only the changes from each node |
| `"messages"` | LLM token-level chunks |

```python
# Most common: see node-by-node progress
for chunk in graph.stream(input, stream_mode="updates"):
    print(chunk)

# For real-time LLM output to users
async for chunk in graph.astream(input, stream_mode="messages"):
    if hasattr(chunk[0], "content") and chunk[0].content:
        print(chunk[0].content, end="", flush=True)
```

### Missing async for astream

```python
# Wrong: using sync iteration with async stream
for chunk in graph.astream(input):  # won't work
    ...

# Correct
async for chunk in graph.astream(input):
    ...
```
