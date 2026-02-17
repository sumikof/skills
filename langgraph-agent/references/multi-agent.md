# Multi-Agent Systems (LangGraph v1.0.8)

## Table of Contents

1. [Overview](#overview)
2. [Supervisor Pattern](#supervisor-pattern)
3. [Swarm Pattern (Agent Handoff)](#swarm-pattern)
4. [Manual Multi-Agent with StateGraph](#manual-multi-agent-with-stategraph)
5. [Hierarchical Teams (Nested Supervisors)](#hierarchical-teams)
6. [Shared State Between Agents](#shared-state-between-agents)

---

## Overview

Three main multi-agent patterns in LangGraph:

| Pattern | When to use | Package |
| --- | --- | --- |
| **Supervisor** | Central coordinator routes to specialists | `langgraph-supervisor` |
| **Swarm** | Agents hand off to each other autonomously | `langgraph-swarm` |
| **Manual** | Full control over agent communication | Built-in StateGraph |

```bash
pip install langgraph-supervisor langgraph-swarm
```

---

## Supervisor Pattern

A central LLM (supervisor) routes user requests to specialist agents.

```python
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

model = ChatOpenAI(model="gpt-4o")

# --- Specialist agents ---

@tool
def web_search(query: str) -> str:
    """Search the web."""
    return f"Results for: {query}"

@tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

research_agent = create_react_agent(
    model=model,
    tools=[web_search],
    name="research_expert",
    prompt="You are a research expert with web search access.",
)

math_agent = create_react_agent(
    model=model,
    tools=[add, multiply],
    name="math_expert",
    prompt="You are a math expert. Always use one tool at a time.",
)

# --- Supervisor ---

workflow = create_supervisor(
    [research_agent, math_agent],
    model=model,
    prompt=(
        "You are a team supervisor managing a research expert and math expert. "
        "Route research questions to research_expert, math questions to math_expert."
    ),
)

app = workflow.compile()
result = app.invoke({
    "messages": [{"role": "user", "content": "What is 15 * 23?"}]
})
```

### Supervisor options

```python
workflow = create_supervisor(
    agents=[research_agent, math_agent],
    model=model,
    prompt="...",
    output_mode="full_history",  # "full_history" | "last_message"
    handoff_tool_prefix="delegate_to",  # custom tool naming
    add_handoff_messages=True,   # include handoff messages in history
)
```

### Custom handoff tools

```python
from langgraph_supervisor import create_handoff_tool

workflow = create_supervisor(
    [research_agent, math_agent],
    model=model,
    tools=[
        create_handoff_tool(
            agent_name="math_expert",
            name="ask_math_expert",
            description="Route math questions to the math specialist",
        ),
        create_handoff_tool(
            agent_name="research_expert",
            name="ask_research_expert",
            description="Route research questions to the research specialist",
        ),
    ],
)
```

---

## Swarm Pattern

Agents hand off to each other autonomously using `Command(goto=...)`. No central supervisor.

```python
from langgraph_swarm import create_swarm
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langgraph_swarm import create_handoff_tool

model = ChatOpenAI(model="gpt-4o")

# Each agent has handoff tools to transfer to other agents
transfer_to_research = create_handoff_tool(
    agent_name="research_agent",
    description="Transfer to research agent for web lookups",
)

transfer_to_math = create_handoff_tool(
    agent_name="math_agent",
    description="Transfer to math agent for calculations",
)

research_agent = create_react_agent(
    model=model,
    tools=[web_search, transfer_to_math],
    name="research_agent",
    prompt="You are a research agent. Hand off math questions to math_agent.",
)

math_agent = create_react_agent(
    model=model,
    tools=[add, multiply, transfer_to_research],
    name="math_agent",
    prompt="You are a math agent. Hand off research questions to research_agent.",
)

workflow = create_swarm(
    [research_agent, math_agent],
    default_active_agent="research_agent",  # starting agent
)

app = workflow.compile()
result = app.invoke({
    "messages": [{"role": "user", "content": "Search for AAPL stock price then multiply it by 100"}]
})
```

---

## Manual Multi-Agent with StateGraph

Full control over agent interaction. Use `Command` for routing + state update.

```python
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command

class State(TypedDict):
    messages: Annotated[list, add_messages]
    current_agent: str

model = ChatOpenAI(model="gpt-4o", temperature=0)

# --- Agent nodes ---

def researcher(state: State) -> Command[Literal["writer", END]]:
    response = model.invoke([
        SystemMessage("You are a researcher. Gather information, then hand off to the writer."),
        *state["messages"],
    ])
    # Decide: hand off to writer or finish
    if "HANDOFF_TO_WRITER" in response.content:
        return Command(
            goto="writer",
            update={"messages": [response], "current_agent": "writer"},
        )
    return Command(goto=END, update={"messages": [response]})


def writer(state: State) -> Command[Literal["researcher", END]]:
    response = model.invoke([
        SystemMessage("You are a writer. Use the research to write content."),
        *state["messages"],
    ])
    if "NEED_MORE_RESEARCH" in response.content:
        return Command(
            goto="researcher",
            update={"messages": [response], "current_agent": "researcher"},
        )
    return Command(goto=END, update={"messages": [response]})

# --- Graph ---

builder = StateGraph(State)
builder.add_node("researcher", researcher)
builder.add_node("writer", writer)
builder.add_edge(START, "researcher")
# No add_edge needed — Command handles routing

graph = builder.compile()
result = graph.invoke({
    "messages": [{"role": "user", "content": "Write an article about quantum computing"}],
    "current_agent": "researcher",
})
```

---

## Hierarchical Teams

Nest supervisors for complex organizational structures:

```python
from langgraph_supervisor import create_supervisor

# Level 1: Team supervisors
research_team = create_supervisor(
    [search_agent, analysis_agent],
    model=model,
    supervisor_name="research_supervisor",
    prompt="Manage the research team.",
).compile(name="research_team")

writing_team = create_supervisor(
    [drafting_agent, editing_agent],
    model=model,
    supervisor_name="writing_supervisor",
    prompt="Manage the writing team.",
).compile(name="writing_team")

# Level 2: Top-level supervisor manages teams
top_supervisor = create_supervisor(
    [research_team, writing_team],
    model=model,
    supervisor_name="project_manager",
    prompt="You are the project manager. Route to research_team or writing_team.",
).compile(name="project_manager")

result = top_supervisor.invoke({
    "messages": [{"role": "user", "content": "Research AI trends and write a report"}]
})
```

---

## Shared State Between Agents

### Through graph state (recommended)

All agents share the same state keys — the most natural approach:

```python
class SharedState(TypedDict):
    messages: Annotated[list, add_messages]
    research_notes: str       # written by researcher, read by writer
    draft: str                # written by writer, read by reviewer
    feedback: str             # written by reviewer, read by writer
    current_agent: str

def researcher(state: SharedState) -> dict:
    notes = do_research(state["messages"])
    return {"research_notes": notes, "current_agent": "writer"}

def writer(state: SharedState) -> dict:
    draft = write_draft(state["research_notes"], state.get("feedback", ""))
    return {"draft": draft, "current_agent": "reviewer"}

def reviewer(state: SharedState) -> dict:
    feedback = review_draft(state["draft"])
    return {"feedback": feedback, "current_agent": "writer"}
```

### Through Store (cross-thread)

For agents running in separate threads that need shared memory:

```python
from langgraph.store.memory import InMemoryStore
from langgraph.store.base import BaseStore

store = InMemoryStore()

def agent_a(state: State, *, store: BaseStore) -> dict:
    # Write shared data
    store.put(("shared", "project-1"), "findings", {"data": "important result"})
    return {"messages": [...]}

def agent_b(state: State, *, store: BaseStore) -> dict:
    # Read data written by agent_a (even from a different thread)
    findings = store.get(("shared", "project-1"), "findings")
    return {"messages": [...]}

graph = builder.compile(
    checkpointer=InMemorySaver(),
    store=store,  # shared across all threads
)
```
