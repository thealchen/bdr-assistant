import os
from typing import Literal
from datetime import datetime
from langgraph.graph import StateGraph, END
from galileo import galileo_context
from galileo.handlers.langchain import GalileoAsyncCallback
from dotenv import load_dotenv
from graph.state import LeadState
from graph.nodes import (
    retrieve_enrichment,
    web_research_node,
    draft_email_node,
    draft_linkedin_node,
    draft_call_script_node
)

load_dotenv()
galileo_context.init(project=os.getenv("GALILEO_PROJECT", "sdr-outreach-assistant"))


def should_do_research(state: LeadState) -> Literal["research", "draft"]:
    """Determine if web research is needed.
    
    Always do web research to get fresh personalization hooks,
    even when vector store enrichment is available.
    """
    # Always do research to get fresh personalization hooks
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

# Invoke with regular Langgraph
# result = app.invoke(state)

# Invoke with Galileo
def invoke_with_galileo(state: LeadState):
    """Invoke workflow with Galileo observability."""
    galileo_context.start_session(name=f"lead_{datetime.now().strftime('%Y%m%d_%H%M%S')}", external_id=state["lead_email"])
    result = app.invoke(state, config={"callbacks": [GalileoAsyncCallback()]})
    galileo_context.clear_session()
    return result
