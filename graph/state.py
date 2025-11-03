from typing import TypedDict, Optional, Dict, List, Annotated
from operator import add


class LeadState(TypedDict):
    """State for the SDR outreach workflow.

    Uses Annotated reducer for status to support parallel node execution.
    Multiple nodes can update status simultaneously - values are collected into a list.
    """

    # Input
    lead_id: str
    lead_email: str

    # Enrichment data
    enrichment_data: Optional[Dict]
    enrichment_sufficient: bool

    # Research results
    research_results: Optional[Dict]

    # Personalization hooks extracted from research
    personalization_hooks: Optional[Dict]

    # Generated outputs
    email_draft: Optional[str]
    linkedin_draft: Optional[str]
    call_script: Optional[str]

    # Workflow status - uses reducer to handle parallel updates
    # Each node can append status messages, they'll be collected in a list
    status: Annotated[List[str], add]
    error: Optional[str]
