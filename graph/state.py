from typing import TypedDict, Optional, Dict, List


class LeadState(TypedDict):
    """State for the SDR outreach workflow."""

    # Input
    lead_id: str
    lead_email: str

    # Enrichment data
    enrichment_data: Optional[Dict]
    enrichment_sufficient: bool

    # Research results
    research_results: Optional[Dict]

    # Generated outputs
    email_draft: Optional[str]
    linkedin_draft: Optional[str]
    call_script: Optional[str]

    # Workflow status
    status: str
    error: Optional[str]
