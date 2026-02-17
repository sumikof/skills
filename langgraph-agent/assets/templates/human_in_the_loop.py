"""
Human-in-the-Loop Workflow — LangGraph v1.0.8
Demonstrates interrupt()/Command pattern with multi-round approval and revision.
Usage: python human_in_the_loop.py
Requires: pip install langgraph==1.0.8 langchain-openai
"""

from typing import Literal, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

# ── State ──────────────────────────────────────────────────────────────────────

class State(TypedDict):
    topic: str
    draft: str
    feedback: str
    revision_count: int
    approved: bool
    final: str


# ── Model ──────────────────────────────────────────────────────────────────────

model = ChatOpenAI(model="gpt-4o", temperature=0.7)

MAX_REVISIONS = 3  # prevent infinite revision loop

# ── Nodes ──────────────────────────────────────────────────────────────────────

def generate_draft(state: State) -> dict:
    """Generate initial draft content."""
    prompt = f"Write a concise 2-sentence summary about: {state['topic']}"
    if state.get("feedback"):
        prompt = (
            f"Revise this draft based on feedback.\n\n"
            f"Draft: {state['draft']}\n"
            f"Feedback: {state['feedback']}\n\n"
            f"Write a revised 2-sentence summary."
        )
    response = model.invoke(prompt)
    return {"draft": response.content, "feedback": ""}


def human_review(state: State) -> dict:
    """
    Pause for human review. Returns approved=True or approved=False with feedback.
    The graph pauses here until Command(resume=...) is called.
    """
    decision = interrupt({
        "draft": state["draft"],
        "revision": state.get("revision_count", 0),
        "instructions": (
            "To approve: {'approved': True}\n"
            "To revise: {'approved': False, 'feedback': 'your notes here'}"
        ),
    })

    approved = decision.get("approved", False)
    feedback = decision.get("feedback", "")
    return {
        "approved": approved,
        "feedback": feedback,
        "revision_count": state.get("revision_count", 0) + (0 if approved else 1),
    }


def publish(state: State) -> dict:
    """Finalize approved content."""
    return {"final": f"[PUBLISHED] {state['draft']}"}


# ── Routing ────────────────────────────────────────────────────────────────────

def route_review(state: State) -> Literal["publish", "generate_draft", END]:
    if state["approved"]:
        return "publish"
    if state.get("revision_count", 0) >= MAX_REVISIONS:
        return END  # max revisions reached
    return "generate_draft"


# ── Graph ──────────────────────────────────────────────────────────────────────

builder = StateGraph(State)
builder.add_node("generate_draft", generate_draft)
builder.add_node("human_review", human_review)
builder.add_node("publish", publish)

builder.add_edge(START, "generate_draft")
builder.add_edge("generate_draft", "human_review")
builder.add_conditional_edges("human_review", route_review, {
    "publish": "publish",
    "generate_draft": "generate_draft",
    END: END,
})
builder.add_edge("publish", END)

# Checkpointer is REQUIRED for interrupt() to work
graph = builder.compile(checkpointer=InMemorySaver())

# ── Run ────────────────────────────────────────────────────────────────────────

def run_interactive():
    """Interactive HITL loop for terminal use."""
    config = {"configurable": {"thread_id": "content-001"}}
    initial_state = {
        "topic": "the benefits of daily exercise",
        "draft": "",
        "feedback": "",
        "revision_count": 0,
        "approved": False,
        "final": "",
    }

    print("=== Content Generation Workflow ===\n")

    # First run — pauses at interrupt()
    for event in graph.stream(initial_state, config, stream_mode="values"):
        if "draft" in event and event["draft"] and not event.get("final"):
            print(f"Draft (revision {event.get('revision_count', 0)}):\n{event['draft']}\n")

    while True:
        state = graph.get_state(config)
        if not state.next:  # graph finished
            break

        print("--- Human Review ---")
        approve_input = input("Approve? (y/n): ").strip().lower()
        if approve_input == "y":
            human_response = {"approved": True}
        else:
            feedback = input("Feedback for revision: ").strip()
            human_response = {"approved": False, "feedback": feedback}

        print()

        # Resume graph
        for event in graph.stream(Command(resume=human_response), config, stream_mode="values"):
            if "draft" in event and event["draft"] and not event.get("final"):
                rev = event.get("revision_count", 0)
                print(f"Revised draft (revision {rev}):\n{event['draft']}\n")
            if "final" in event and event["final"]:
                print(f"✓ {event['final']}")
                return


def run_automated():
    """Non-interactive demo that simulates human decisions."""
    config = {"configurable": {"thread_id": "auto-demo-001"}}
    initial_state = {
        "topic": "machine learning in healthcare",
        "draft": "", "feedback": "", "revision_count": 0,
        "approved": False, "final": "",
    }

    print("=== Automated Demo (Simulated Human) ===\n")

    # First run
    for event in graph.stream(initial_state, config, stream_mode="values"):
        if "draft" in event and event["draft"]:
            print(f"Initial draft:\n{event['draft']}\n")

    # Simulate: reject first, then approve
    decisions = [
        {"approved": False, "feedback": "Too vague — add specific examples"},
        {"approved": True},
    ]

    for i, decision in enumerate(decisions):
        state = graph.get_state(config)
        if not state.next:
            break
        print(f"Human decision {i + 1}: {decision}")
        for event in graph.stream(Command(resume=decision), config, stream_mode="values"):
            if "draft" in event and event["draft"] and not event.get("final"):
                print(f"Revised draft:\n{event['draft']}\n")
            if "final" in event and event["final"]:
                print(f"Result: {event['final']}")


if __name__ == "__main__":
    import sys
    if "--interactive" in sys.argv:
        run_interactive()
    else:
        run_automated()
        print("\nRun with --interactive for human input mode")
