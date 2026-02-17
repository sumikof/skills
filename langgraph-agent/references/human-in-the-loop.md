# Human-in-the-Loop Guide (LangGraph v1.0.8)

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [Pattern A: interrupt() inside a node](#pattern-a-interrupt-inside-a-node)
3. [Pattern B: interrupt_before / interrupt_after](#pattern-b-interrupt_before--interrupt_after)
4. [Resuming with Command](#resuming-with-command)
5. [State Inspection and Time-Travel](#state-inspection-and-time-travel)
6. [Production Checkpointers](#production-checkpointers)
7. [HITL Rules and Pitfalls](#hitl-rules-and-pitfalls)

---

## Core Concepts

| Concept | Description |
|---------|-------------|
| `interrupt(value)` | Pauses graph at call site; surfaces `value` to caller |
| `Command(resume=value)` | Resumes paused graph; `value` is returned by `interrupt()` |
| `checkpointer` | **Required** for HITL; persists state between pause/resume |
| `thread_id` | Session identifier: `config={"configurable": {"thread_id": "..."}}` |
| `InMemorySaver` | In-process checkpointer for dev/testing |
| `PostgresSaver` | Distributed checkpointer for production |

---

## Pattern A: interrupt() inside a node

Pause mid-node to collect human input:

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    draft: str
    approved: bool
    feedback: str
    final: str

def generate(state: State) -> dict:
    return {"draft": "AI-generated content here."}

def human_review(state: State) -> dict:
    # interrupt() pauses here and returns to caller
    # The dict passed is what the caller sees (e.g., in stream output)
    decision = interrupt({
        "question": "Approve this draft?",
        "draft": state["draft"],
    })
    # decision = whatever was passed in Command(resume=...)
    return {
        "approved": decision.get("approved", False),
        "feedback": decision.get("feedback", ""),
    }

def finalize(state: State) -> dict:
    return {"final": f"[PUBLISHED] {state['draft']}" if state["approved"] else "REJECTED"}

builder = StateGraph(State)
builder.add_node("generate", generate)
builder.add_node("review", human_review)
builder.add_node("finalize", finalize)
builder.add_edge(START, "generate")
builder.add_edge("generate", "review")
builder.add_edge("review", "finalize")
builder.add_edge("finalize", END)

graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "doc-001"}}

# --- First run: pauses at interrupt() ---
for event in graph.stream({"draft": "", "approved": False, "feedback": "", "final": ""}, config):
    print(event)
# Includes: {'__interrupt__': ({'question': ..., 'draft': ...},)}

# --- Resume with human decision ---
for event in graph.stream(Command(resume={"approved": True}), config):
    print(event)
```

---

## Pattern B: interrupt_before / interrupt_after

Pause at node boundary without touching node code:

```python
graph = builder.compile(
    checkpointer=InMemorySaver(),
    interrupt_before=["human_review"],  # pause BEFORE node runs
    # interrupt_after=["draft_node"],   # pause AFTER node runs
)

config = {"configurable": {"thread_id": "session-1"}}

# Run until pause
graph.invoke(initial_state, config)

# Inspect what's paused
state = graph.get_state(config)
print(state.values)                    # current state
print(state.next)                      # which nodes will run next

# Optionally edit state before continuing
graph.update_state(config, {"draft": "Human-edited version"})

# Resume (None = continue from where paused)
graph.invoke(None, config)
```

---

## Resuming with Command

```python
from langgraph.types import Command

# Resume with a value (used with interrupt())
graph.invoke(Command(resume={"approved": True, "feedback": "Looks good"}), config)

# Resume AND update state simultaneously
graph.invoke(Command(resume=True, update={"notes": "Extra context"}), config)

# Jump to a specific node
graph.invoke(Command(goto="specific_node"), config)

# Resume from node in a subgraph's parent
from langgraph.types import Command
Command(goto="parent_node", graph=Command.PARENT)
```

---

## State Inspection and Time-Travel

```python
config = {"configurable": {"thread_id": "session-1"}}

# Current state
state = graph.get_state(config)
print(state.values)     # dict of current state
print(state.next)       # list of next nodes
print(state.tasks)      # pending tasks

# Manually update state between runs
graph.update_state(config, {"count": 0})

# Update state AS IF a specific node ran it
graph.update_state(config, {"draft": "Updated"}, as_node="generate")

# View full history of all checkpoints
for snapshot in graph.get_state_history(config):
    cid = snapshot.config["configurable"]["checkpoint_id"]
    print(f"Checkpoint: {cid}, Values: {snapshot.values}, Next: {snapshot.next}")

# Resume from a specific past checkpoint (time-travel)
past_config = {
    "configurable": {
        "thread_id": "session-1",
        "checkpoint_id": "<id-from-history>",
    }
}
graph.invoke(None, past_config)
```

---

## Production Checkpointers

```python
# SQLite — lightweight, single-server production
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("./checkpoints.db") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    graph.invoke(initial_state, config)

# PostgreSQL — distributed, multi-server production
# pip install langgraph-checkpoint-postgres psycopg
from langgraph.checkpoint.postgres import PostgresSaver

DSN = "postgresql://user:password@localhost:5432/dbname"
with PostgresSaver.from_conn_string(DSN) as checkpointer:
    checkpointer.setup()  # creates tables on first use
    graph = builder.compile(checkpointer=checkpointer)
    graph.invoke(initial_state, config)

# PostgreSQL with connection pool (concurrent access)
from psycopg_pool import ConnectionPool
pool = ConnectionPool(DSN, min_size=2, max_size=10)
checkpointer = PostgresSaver(pool)
```

---

## HITL Rules and Pitfalls

**Required:**
- Checkpointer MUST be set in `compile()` before `interrupt()` can work
- Same `thread_id` MUST be used to resume a paused graph
- Code before `interrupt()` re-executes on resume — make it **idempotent**

**Never do:**
```python
# WRONG: interrupt() raises internally — catching it silently aborts the pause
def review(state):
    try:
        decision = interrupt({"draft": state["draft"]})
    except Exception:
        decision = {"approved": False}  # this runs if interrupt is caught!
```

**Always do:**
```python
# CORRECT
def review(state):
    decision = interrupt({"draft": state["draft"]})
    return {"approved": decision.get("approved", False)}
```

**Multiple interrupts per node:**
```python
def multi_step_review(state: State) -> dict:
    # Each interrupt() is sequential; maintain consistent order across runs
    title = interrupt({"field": "title", "current": state["title"]})
    body = interrupt({"field": "body", "current": state["body"]})
    return {
        "title": title.get("edit", state["title"]),
        "body": body.get("edit", state["body"]),
    }
```

**HITL in async context:**
```python
async def run_with_hitl(initial_state, human_response):
    config = {"configurable": {"thread_id": "async-001"}}

    # First run (pauses)
    async for event in graph.astream(initial_state, config):
        if "__interrupt__" in event:
            break

    # Resume
    async for event in graph.astream(Command(resume=human_response), config):
        print(event)
```
