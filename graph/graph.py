from typing import Literal
from langgraph.graph import StateGraph, END
from graph.state import LeadState
from graph.nodes import (
    retrieve_enrichment,
    web_research_node,
    draft_email_node,
    draft_linkedin_node,
    draft_call_script_node
)


def should_do_research(state: LeadState) -> Literal["research", "draft"]:
    """Determine if additional web research is needed."""
    if state.get("enrichment_sufficient", False):
        return "draft"
    return "research"


def build_graph() -> StateGraph:
    """Build the SDR outreach workflow graph."""

    workflow = StateGraph(LeadState)

    # Add nodes
    workflow.add_node("retrieve_enrichment", retrieve_enrichment)
    workflow.add_node("web_research", web_research_node)
    workflow.add_node("draft_email", draft_email_node)
    workflow.add_node("draft_linkedin", draft_linkedin_node)
    workflow.add_node("draft_call_script", draft_call_script_node)

    # Set entry point
    workflow.set_entry_point("retrieve_enrichment")

    # Add conditional edge after enrichment
    workflow.add_conditional_edges(
        "retrieve_enrichment",
        should_do_research,
        {
            "research": "web_research",
            "draft": "draft_email"
        }
    )

    # After research, go to drafting
    workflow.add_edge("web_research", "draft_email")

    # Parallel drafting: all three draft nodes run concurrently
    # Email triggers LinkedIn and Call Script
    workflow.add_edge("draft_email", "draft_linkedin")
    workflow.add_edge("draft_email", "draft_call_script")

    # Both LinkedIn and Call Script end after completion
    workflow.add_edge("draft_linkedin", END)
    workflow.add_edge("draft_call_script", END)

    return workflow.compile()


# Create compiled graph instance
app = build_graph()


def invoke_with_config(state: LeadState, config: dict = None):
    """Invoke workflow with optional config (for Galileo callbacks).

    Args:
        state: Initial workflow state
        config: Optional config dict with callbacks for Galileo tracing

    Returns:
        Final workflow state
    """
    if config:
        return app.invoke(state, config=config)
    return app.invoke(state)
