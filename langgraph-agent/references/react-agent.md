# ReAct Agent Guide (LangGraph v1.0.8)

## Table of Contents
1. [Prebuilt: create_react_agent](#prebuilt-create_react_agent)
2. [Full Signature](#full-signature)
3. [Manual ReAct Graph](#manual-react-graph)
4. [Prebuilt ToolNode](#prebuilt-toolnode)
5. [Defining Tools](#defining-tools)
6. [Different LLM Providers](#different-llm-providers)
7. [Hooks: pre/post model](#hooks)
8. [Streaming Output](#streaming-output)

---

## Prebuilt: create_react_agent

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

@tool
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    return f"72°F and sunny in {location}"

@tool
def search(query: str) -> str:
    """Search the web for information."""
    return f"Search results for '{query}'"

model = ChatOpenAI(model="gpt-4o", temperature=0)

agent = create_react_agent(
    model=model,
    tools=[get_weather, search],
    prompt="You are a helpful assistant. Use tools when needed.",
    checkpointer=InMemorySaver(),  # enables memory across turns
)

config = {"configurable": {"thread_id": "user-123"}}
result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in Tokyo?"}]},
    config=config,
)
print(result["messages"][-1].content)
```

---

## Full Signature

```python
create_react_agent(
    model,              # str | BaseChatModel | Callable
    tools,              # list[BaseTool | Callable | dict] | ToolNode
    *,
    prompt=None,        # str | SystemMessage | Callable | Runnable
    response_format=None,   # Pydantic model for structured output
    pre_model_hook=None,    # Callable run before LLM call (trim messages, log, etc.)
    post_model_hook=None,   # Callable run after LLM call (filter, validate, etc.)
    state_schema=None,      # Custom state TypedDict (add extra keys beyond messages)
    context_schema=None,    # Immutable per-run context (e.g. user_id, session data)
    checkpointer=None,
    store=None,
    interrupt_before=None,
    interrupt_after=None,
    debug=False,
    version="v2",       # "v1"=parallel tool exec, "v2"=Send API routing (recommended)
    name=None,
) -> CompiledStateGraph
```

**Structured output:**
```python
from pydantic import BaseModel

class ResearchAnswer(BaseModel):
    topic: str
    summary: str
    confidence: float

agent = create_react_agent(model=model, tools=tools, response_format=ResearchAnswer)
result = agent.invoke({"messages": [...]})
structured = result["structured_response"]  # ResearchAnswer instance
```

**Custom state:**
```python
from typing import TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_name: str        # extra field beyond default
    step_count: int

agent = create_react_agent(
    model=model,
    tools=tools,
    state_schema=AgentState,
)
agent.invoke({"messages": [...], "user_name": "Alice", "step_count": 0})
```

---

## Manual ReAct Graph

Use when you need full control over the agent loop:

```python
import json
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

@tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f"72°F and sunny in {location}"

tools = [get_weather]
tools_by_name = {t.name: t for t in tools}

model = ChatOpenAI(model="gpt-4o", temperature=0)
model_with_tools = model.bind_tools(tools)

SYSTEM = "You are a helpful AI assistant."

def call_model(state: AgentState, config: RunnableConfig) -> dict:
    messages = [SystemMessage(SYSTEM)] + list(state["messages"])
    response = model_with_tools.invoke(messages, config)
    return {"messages": [response]}

def call_tools(state: AgentState) -> dict:
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        try:
            result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
            content = json.dumps(result)
        except Exception as e:
            content = f"Error: {e}"
        outputs.append(ToolMessage(
            content=content,
            name=tool_call["name"],
            tool_call_id=tool_call["id"],
        ))
    return {"messages": outputs}

def should_continue(state: AgentState) -> str:
    return "tools" if state["messages"][-1].tool_calls else END

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", call_tools)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

graph = workflow.compile()
result = graph.invoke({"messages": [{"role": "user", "content": "Weather in NYC?"}]})
```

---

## Prebuilt ToolNode

Drop-in replacement for writing your own tool execution node:

```python
from langgraph.prebuilt import ToolNode

# ToolNode automatically:
# - Executes all tool_calls from the last message
# - Returns ToolMessage results
# - Handles exceptions gracefully (returns error message in ToolMessage)
tool_node = ToolNode(tools)

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)  # use ToolNode instead of custom function
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")
```

---

## Defining Tools

```python
from langchain_core.tools import tool

# Simple
@tool
def search_web(query: str) -> str:
    """Search the web for information about a topic."""
    return f"Results: ..."

# With optional params
@tool
def create_event(title: str, date: str, duration_hours: float = 1.0) -> str:
    """Create a calendar event."""
    return f"Created: {title} on {date} ({duration_hours}h)"

# Return structured data
@tool
def get_stock(ticker: str) -> dict:
    """Get stock info. Returns dict with price, change, volume."""
    return {"ticker": ticker, "price": 150.0, "change": 2.5}

# Async tool
@tool
async def fetch_url(url: str) -> str:
    """Fetch content from a URL."""
    import httpx
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        return r.text[:500]
```

---

## Different LLM Providers

```python
# Anthropic (Claude) — recommended for agents
from langchain_anthropic import ChatAnthropic
model = ChatAnthropic(model="claude-sonnet-4-5-20250929", temperature=0)

# Google Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Azure OpenAI
from langchain_openai import AzureChatOpenAI
model = AzureChatOpenAI(azure_deployment="gpt-4o", api_version="2024-08-01-preview")

# All work the same way with create_react_agent
agent = create_react_agent(model=model, tools=tools)
```

---

## Hooks

```python
# pre_model_hook: runs before each LLM call
def trim_old_messages(state):
    """Keep only last 10 messages to manage context."""
    msgs = state["messages"]
    if len(msgs) > 10:
        state = {**state, "messages": msgs[-10:]}
    return state

# post_model_hook: runs after each LLM call
def content_filter(state):
    """Validate or modify LLM output."""
    last = state["messages"][-1]
    if hasattr(last, "content") and "UNSAFE" in last.content:
        # Replace with safe response
        from langchain_core.messages import AIMessage
        return {"messages": [AIMessage(content="I cannot help with that.")]}
    return state

agent = create_react_agent(
    model=model,
    tools=tools,
    pre_model_hook=trim_old_messages,
    post_model_hook=content_filter,
)
```

---

## Streaming Output

```python
# Stream node-level updates
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Search for latest AI news"}]},
    config,
    stream_mode="updates",  # "values" | "updates" | "messages"
):
    node_name, node_output = list(chunk.items())[0]
    print(f"[{node_name}]:", node_output)

# Stream LLM tokens in real-time (for user-facing output)
async def stream_to_user(user_input: str):
    async for chunk in agent.astream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="messages",
    ):
        if hasattr(chunk[0], "content") and chunk[0].content:
            print(chunk[0].content, end="", flush=True)
    print()  # newline at end
```
