"""
Multi-Agent Supervisor — LangGraph v1.0.8
A central supervisor routes tasks to specialist agents.
Usage: python multi_agent_supervisor.py
Requires: pip install langgraph==1.0.8 langgraph-supervisor langchain-openai
"""

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import InMemorySaver

# ── Model ──────────────────────────────────────────────────────────────────────

model = ChatOpenAI(model="gpt-4o", temperature=0)

# ── Specialist Agent Tools ─────────────────────────────────────────────────────

@tool
def web_search(query: str) -> str:
    """Search the web for current information."""
    # Replace with Tavily, SerpAPI, etc.
    return f"Web search results for '{query}': [result 1, result 2, result 3]"


@tool
def scrape_url(url: str) -> str:
    """Fetch and extract text content from a webpage."""
    # Replace with actual scraper (requests + BeautifulSoup, etc.)
    return f"Content from {url}: [page content here]"


@tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@tool
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@tool
def divide(a: float, b: float) -> float:
    """Divide a by b. Returns error if b is 0."""
    if b == 0:
        return float("nan")
    return a / b


@tool
def write_report(title: str, content: str, format: str = "markdown") -> str:
    """Format a research report with title and content."""
    if format == "markdown":
        return f"# {title}\n\n{content}"
    return f"{title}\n{'=' * len(title)}\n\n{content}"


# ── Specialist Agents ──────────────────────────────────────────────────────────

research_agent = create_react_agent(
    model=model,
    tools=[web_search, scrape_url],
    name="research_expert",
    prompt=(
        "You are a research expert with web search and scraping capabilities. "
        "Gather thorough, accurate information. "
        "Summarize findings clearly for the supervisor."
    ),
)

math_agent = create_react_agent(
    model=model,
    tools=[add, subtract, multiply, divide],
    name="math_expert",
    prompt=(
        "You are a mathematics expert. "
        "Solve calculations step by step, showing your work. "
        "Always use tools for arithmetic — never compute mentally."
    ),
)

writing_agent = create_react_agent(
    model=model,
    tools=[write_report],
    name="writing_expert",
    prompt=(
        "You are a professional writer and editor. "
        "Transform research findings into clear, well-structured content. "
        "Use the write_report tool to produce formatted output."
    ),
)

# ── Supervisor ─────────────────────────────────────────────────────────────────

workflow = create_supervisor(
    agents=[research_agent, math_agent, writing_agent],
    model=model,
    prompt=(
        "You are a team manager coordinating three experts:\n"
        "- research_expert: For web searches, fact-finding, and data gathering\n"
        "- math_expert: For calculations, statistics, and numerical analysis\n"
        "- writing_expert: For drafting reports, summaries, and formatted output\n\n"
        "Break complex tasks into subtasks and delegate appropriately. "
        "Combine their results to produce a final comprehensive answer."
    ),
    output_mode="last_message",  # "last_message" | "full_history"
)

app = workflow.compile(checkpointer=InMemorySaver())

# ── Run ────────────────────────────────────────────────────────────────────────

EXAMPLE_QUERIES = [
    "What is 1234 * 5678? Then search for the population of Tokyo and multiply it by 0.05.",
    "Research the latest developments in quantum computing and write a 3-paragraph summary report.",
    "Search for the GDP of Japan and Germany, then calculate which is larger and by how much.",
]


def run_query(query: str, thread_id: str = "supervisor-001") -> str:
    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke(
        {"messages": [{"role": "user", "content": query}]},
        config=config,
    )
    return result["messages"][-1].content


def run_streaming(query: str, thread_id: str = "supervisor-stream-001"):
    config = {"configurable": {"thread_id": thread_id}}
    print(f"Query: {query}\n")
    print("Workflow execution:")

    for chunk in app.stream(
        {"messages": [{"role": "user", "content": query}]},
        config=config,
        stream_mode="updates",
    ):
        for node_name, output in chunk.items():
            msgs = output.get("messages", [])
            if msgs:
                last = msgs[-1]
                content = getattr(last, "content", "")
                if content:
                    print(f"\n[{node_name}]:\n{content[:300]}{'...' if len(content) > 300 else ''}")


if __name__ == "__main__":
    import sys

    query = EXAMPLE_QUERIES[0]
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])

    print("=== Multi-Agent Supervisor Demo ===\n")
    run_streaming(query)
