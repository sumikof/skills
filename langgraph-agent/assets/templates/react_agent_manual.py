"""
ReAct Agent (Manual) — LangGraph v1.0.8
Full control over the agent loop via StateGraph.
Use this when you need custom routing, error handling, or state beyond messages.
Usage: python react_agent_manual.py
Requires: pip install langgraph==1.0.8 langchain-openai
"""

import json
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# ── State ──────────────────────────────────────────────────────────────────────
# Add custom fields beyond messages here

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    step_count: int  # example custom field


# ── Tools ──────────────────────────────────────────────────────────────────────

@tool
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    return f"72°F and sunny in {location}"


@tool
def calculate(a: float, b: float, operation: str) -> str:
    """Perform arithmetic. operation: add | subtract | multiply | divide"""
    ops = {"add": a + b, "subtract": a - b, "multiply": a * b}
    if operation == "divide":
        if b == 0:
            return "Error: Division by zero"
        ops["divide"] = a / b
    if operation not in ops:
        return f"Unknown operation: {operation}. Use: add | subtract | multiply | divide"
    return str(ops[operation])


tools = [get_weather, calculate]

# ── Model ──────────────────────────────────────────────────────────────────────

model = ChatOpenAI(model="gpt-4o", temperature=0)
model_with_tools = model.bind_tools(tools)

SYSTEM_PROMPT = "You are a helpful AI assistant. Use tools when needed."

# ── Nodes ──────────────────────────────────────────────────────────────────────

def call_model(state: AgentState, config: RunnableConfig) -> dict:
    messages = [SystemMessage(SYSTEM_PROMPT)] + list(state["messages"])
    response = model_with_tools.invoke(messages, config)
    return {
        "messages": [response],
        "step_count": state.get("step_count", 0) + 1,
    }


# Option A: Use prebuilt ToolNode (handles errors automatically)
tool_node = ToolNode(tools)

# Option B: Manual tool execution (uncomment to use instead)
# def tool_node(state: AgentState) -> dict:
#     outputs = []
#     for tc in state["messages"][-1].tool_calls:
#         try:
#             result = {t.name: t for t in tools}[tc["name"]].invoke(tc["args"])
#             content = json.dumps(result)
#         except Exception as e:
#             content = f"Error: {e}"
#         outputs.append(ToolMessage(content=content, name=tc["name"], tool_call_id=tc["id"]))
#     return {"messages": outputs}


# ── Routing ────────────────────────────────────────────────────────────────────

MAX_STEPS = 20  # safety cap against infinite loops

def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if state.get("step_count", 0) >= MAX_STEPS:
        return END  # safety exit
    return "tools" if last.tool_calls else END


# ── Graph ──────────────────────────────────────────────────────────────────────

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")

graph = workflow.compile()

# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    user_input = "What's the weather in Tokyo, and what is 123 multiplied by 456?"
    print(f"User: {user_input}\n")

    result = graph.invoke({
        "messages": [{"role": "user", "content": user_input}],
        "step_count": 0,
    })

    print("Conversation:")
    for msg in result["messages"]:
        role = getattr(msg, "type", "unknown")
        content = getattr(msg, "content", "")
        if content:
            print(f"  [{role}] {content}")
    print(f"\nTotal steps: {result['step_count']}")
