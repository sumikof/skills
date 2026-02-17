---
name: langgraph-agent
description: >
  Expert guide for building AI agents with LangGraph Python library v1.0.8.
  Use this skill when the user wants to build, design, or debug AI agents using LangGraph.
  Covers: StateGraph construction, ReAct agents (prebuilt and manual), human-in-the-loop
  workflows with interrupt/Command, multi-agent systems (supervisor/swarm), subgraphs,
  Send API, Store, checkpointing, functional API, and debugging/troubleshooting.
  Triggers: "LangGraph", "langgraph agent", "StateGraph", "ReAct agent", "HITL workflow",
  "interrupt()", "checkpointer", "create_react_agent", "LangGraph graph", "AI agent graph",
  "multi-agent", "supervisor agent", "swarm agent", "agent handoff", "LangGraph debug".
---

# LangGraph Agent Skill (v1.0.8)

## Requirements

```bash
pip install langgraph==1.0.8 langchain-openai
# Multi-agent:
pip install langgraph-supervisor langgraph-swarm
# Persistence:
pip install langgraph-checkpoint-sqlite   # dev
pip install langgraph-checkpoint-postgres # prod
```

Python 3.10+ required.

## Reference Guides

| Topic | File | When to read |
| --- | --- | --- |
| StateGraph API | [graph-construction.md](references/graph-construction.md) | Building any graph: nodes, edges, compile, execution, functional API |
| ReAct agents | [react-agent.md](references/react-agent.md) | Tool-calling agents (prebuilt or manual), LLM providers, ToolNode, streaming |
| Human-in-the-loop | [human-in-the-loop.md](references/human-in-the-loop.md) | interrupt(), Command(resume=), approval workflows, checkpointers |
| Multi-agent systems | [multi-agent.md](references/multi-agent.md) | Supervisor, swarm, manual handoff, hierarchical teams, shared state |
| Advanced patterns | [advanced-patterns.md](references/advanced-patterns.md) | Subgraphs, Send API (map-reduce), Store, Command, visualization, state design |
| Troubleshooting | [troubleshooting.md](references/troubleshooting.md) | Errors, debugging, performance, common pitfalls |

## Workflow Decision Tree

**What kind of agent are you building?**

1. **Simple tool-calling agent** → `create_react_agent` (prebuilt)
   - [react-agent.md](references/react-agent.md) § Prebuilt

2. **Custom agent loop** → Manual StateGraph
   - [graph-construction.md](references/graph-construction.md) + [react-agent.md](references/react-agent.md) § Manual

3. **Human approval/review** → interrupt() + checkpointer
   - [human-in-the-loop.md](references/human-in-the-loop.md)

4. **Multiple specialist agents** → Supervisor or Swarm
   - [multi-agent.md](references/multi-agent.md) — Supervisor for centralized routing, Swarm for peer-to-peer

5. **Dynamic parallel processing** → Send API (map-reduce)
   - [advanced-patterns.md](references/advanced-patterns.md) § Send API

6. **Imperative workflow** → Functional API (@entrypoint + @task)
   - [graph-construction.md](references/graph-construction.md) § Functional API

7. **Cross-thread memory** → Store
   - [advanced-patterns.md](references/advanced-patterns.md) § Store

**Debugging?** → [troubleshooting.md](references/troubleshooting.md)

## Core Pattern (Minimal Example)

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

def agent(state: State) -> dict:
    # Your logic here
    return {"messages": [{"role": "assistant", "content": "Hello!"}]}

builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)
graph = builder.compile()

result = graph.invoke({"messages": [{"role": "user", "content": "Hi"}]})
```

## Key Concepts

- **State**: TypedDict shared between nodes. Use `Annotated[list, add_messages]` for message lists. Nodes return partial updates.
- **Reducer**: Controls how concurrent updates merge. Without one, last-write-wins.
- **Checkpointer**: Enables persistence, HITL, time-travel. Required for `interrupt()`.
- **Command**: Combined state update + routing. Essential for multi-agent handoff.
- **Send**: Dynamic fan-out for parallel processing (map-reduce).
- **Store**: Cross-thread long-term memory (separate from checkpointer).
- **thread_id**: Session identifier: `config={"configurable": {"thread_id": "..."}}`

## Code Templates

Ready-to-use templates in `assets/templates/`:

| Template | Description |
| --- | --- |
| `react_agent.py` | Prebuilt ReAct agent with tools and chat loop |
| `react_agent_manual.py` | Manual ReAct loop with full StateGraph control |
| `human_in_the_loop.py` | interrupt()-based approval workflow with revision loop |
| `multi_agent_supervisor.py` | Supervisor coordinating specialist agents |
