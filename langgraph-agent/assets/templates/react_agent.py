"""
ReAct Agent (Prebuilt) — LangGraph v1.0.8
Uses create_react_agent for fast setup with tool-calling and memory.
Usage: python react_agent.py
Requires: pip install langgraph==1.0.8 langchain-openai
"""

import os
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver

# ── Tools ──────────────────────────────────────────────────────────────────────
# Replace with your actual tool implementations

@tool
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    # Replace with actual weather API call
    return f"72°F and sunny in {location}"


@tool
def search(query: str) -> str:
    """Search for information about a topic."""
    # Replace with actual search implementation (Tavily, SerpAPI, etc.)
    return f"Search results for '{query}': [result 1, result 2, result 3]"


@tool
def calculate(expression: str) -> str:
    """Safely evaluate a math expression (e.g. '2 + 2 * 10')."""
    import ast, operator
    ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg,
    }
    def _eval(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp):
            return ops[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp):
            return ops[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported: {node}")
    try:
        return str(_eval(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"


# ── Model ──────────────────────────────────────────────────────────────────────
# Swap model for Anthropic: from langchain_anthropic import ChatAnthropic

model = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# ── Agent ──────────────────────────────────────────────────────────────────────

agent = create_react_agent(
    model=model,
    tools=[get_weather, search, calculate],
    prompt="You are a helpful assistant. Use the available tools to answer questions accurately.",
    checkpointer=InMemorySaver(),  # enables memory across turns in same session
)

# ── Run ────────────────────────────────────────────────────────────────────────

config = {"configurable": {"thread_id": "user-session-1"}}


def chat(user_message: str) -> str:
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_message}]},
        config=config,
    )
    return result["messages"][-1].content


if __name__ == "__main__":
    print("ReAct Agent ready. Type 'quit' to exit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue
        response = chat(user_input)
        print(f"Agent: {response}\n")
