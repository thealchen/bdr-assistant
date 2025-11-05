from typing import TypedDict, Optional, Dict, List, Annotated, Literal
from operator import add


class LeadState(TypedDict):
    """State for the SDR outreach workflow.

    Uses Annotated reducer for status to support parallel node execution.
    Multiple nodes can update status simultaneously - values are collected into a list.
    
    Supports two input formats:
    1. Email-based: lead_email populated, input_type="email"
    2. Name+Company: lead_name + lead_company populated, input_type="name_company"
    """

    # Input - supports both email and name+company formats
    lead_id: str
    input_type: Literal["email", "name_company"]
    original_input: str
    
    # Email-based input
    lead_email: Optional[str]
    
    # Name+Company input  
    lead_name: Optional[str]
    lead_company: Optional[str]

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
