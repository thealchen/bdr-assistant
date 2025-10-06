import os
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from data import LeadVectorStore
from tools.retriever import LeadRetriever
from tools.web_research import WebResearchTool
from tools.gmail_api import GmailAPI
from tools.linkedin_api import LinkedInAPI


# Initialize components
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
vector_store = LeadVectorStore()
retriever = LeadRetriever(vector_store)
web_research = WebResearchTool()
gmail_api = GmailAPI()
linkedin_api = LinkedInAPI()


def retrieve_enrichment(state: Dict) -> Dict:
    """Retrieve lead enrichment data from vector store."""
    lead_email = state["lead_email"]

    try:
        results = retriever.retrieve(lead_email)

        if results:
            enrichment_data = results[0]
            # Check if enrichment has sufficient detail
            enrichment_sufficient = _check_enrichment_quality(enrichment_data)

            return {
                "enrichment_data": enrichment_data,
                "enrichment_sufficient": enrichment_sufficient,
                "status": "enrichment_retrieved"
            }
        else:
            return {
                "enrichment_data": None,
                "enrichment_sufficient": False,
                "status": "enrichment_not_found"
            }
    except Exception as e:
        return {
            "enrichment_data": None,
            "enrichment_sufficient": False,
            "status": "enrichment_error",
            "error": str(e)
        }


def web_research_node(state: Dict) -> Dict:
    """Perform web research on the lead."""
    lead_email = state["lead_email"]
    enrichment_data = state.get("enrichment_data", {})

    company = enrichment_data.get("metadata", {}).get("company", "")
    title = enrichment_data.get("metadata", {}).get("title", "")

    try:
        research_results = web_research.research_lead(
            email=lead_email,
            company=company,
            title=title
        )

        return {
            "research_results": research_results,
            "status": "research_completed"
        }
    except Exception as e:
        return {
            "research_results": None,
            "status": "research_error",
            "error": str(e)
        }


def draft_email_node(state: Dict) -> Dict:
    """Draft email outreach message."""
    enrichment = state.get("enrichment_data", {})
    research = state.get("research_results", {})
    lead_email = state["lead_email"]

    context = _build_context(enrichment, research)

    system_prompt = """You are an expert SDR at Galileo.ai drafting personalized outreach emails.

Key guidelines:
- Keep emails concise (100-150 words)
- Lead with value, not product pitch
- Reference specific, relevant context about the lead
- End with clear, low-friction CTA
- Professional but conversational tone"""

    user_prompt = f"""Draft an email to reach out to this lead:

Lead Context:
{context}

Company: Galileo.ai provides ML observability and evaluation platform for LLM applications.

Draft the email body only (no subject line)."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        email_draft = response.content

        # Create Gmail draft
        gmail_api.create_draft(
            to=lead_email,
            subject="Improving ML model quality at {company}".format(
                company=enrichment.get("metadata", {}).get("company", "your company")
            ),
            body=email_draft
        )

        return {
            "email_draft": email_draft,
            "status": "email_drafted"
        }
    except Exception as e:
        return {
            "email_draft": None,
            "status": "email_error",
            "error": str(e)
        }


def draft_linkedin_node(state: Dict) -> Dict:
    """Draft LinkedIn outreach message."""
    enrichment = state.get("enrichment_data", {})
    research = state.get("research_results", {})
    lead_email = state["lead_email"]

    context = _build_context(enrichment, research)

    system_prompt = """You are an expert SDR drafting LinkedIn connection messages.

Key guidelines:
- Keep under 300 characters for initial connection request
- Mention mutual connection or shared interest
- Professional and friendly
- No sales pitch in connection request"""

    user_prompt = f"""Draft a LinkedIn connection request message:

Lead Context:
{context}

Draft the connection message only."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        linkedin_draft = response.content

        # Note: LinkedIn API integration would post this as draft/scheduled message
        linkedin_api.create_message_draft(
            recipient_email=lead_email,
            message=linkedin_draft
        )

        return {
            "linkedin_draft": linkedin_draft,
            "status": "linkedin_drafted"
        }
    except Exception as e:
        return {
            "linkedin_draft": None,
            "status": "linkedin_error",
            "error": str(e)
        }


def draft_call_script_node(state: Dict) -> Dict:
    """Draft call script as markdown file."""
    enrichment = state.get("enrichment_data", {})
    research = state.get("research_results", {})
    lead_email = state["lead_email"]
    lead_id = state["lead_id"]

    context = _build_context(enrichment, research)

    system_prompt = """You are an expert SDR drafting call scripts.

Key guidelines:
- Opening: Brief intro + permission to proceed
- Discovery: 3-4 key questions about their challenges
- Positioning: Connect their needs to Galileo's value
- Close: Calendar booking or next step
- Include objection handling tips
- Format as structured markdown"""

    user_prompt = f"""Draft a call script for this lead:

Lead Context:
{context}

Company: Galileo.ai provides ML observability and evaluation platform for LLM applications.

Format with sections: Opening, Discovery Questions, Positioning, Close, Objection Handling."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        call_script = response.content

        # Save to markdown file
        output_path = f"./outputs/call_script_{lead_id}.md"
        os.makedirs("./outputs", exist_ok=True)
        with open(output_path, "w") as f:
            f.write(call_script)

        return {
            "call_script": call_script,
            "status": "call_script_drafted"
        }
    except Exception as e:
        return {
            "call_script": None,
            "status": "call_script_error",
            "error": str(e)
        }


# Helper functions

def _check_enrichment_quality(enrichment_data: Dict) -> bool:
    """Check if enrichment data has sufficient detail."""
    metadata = enrichment_data.get("metadata", {})

    required_fields = ["company", "industry", "title"]
    has_required = all(metadata.get(field) for field in required_fields)

    content_length = len(enrichment_data.get("content", ""))

    return has_required and content_length > 100


def _build_context(enrichment: Dict, research: Dict) -> str:
    """Build context string from enrichment and research data."""
    context_parts = []

    if enrichment:
        metadata = enrichment.get("metadata", {})
        context_parts.append(f"Company: {metadata.get('company', 'N/A')}")
        context_parts.append(f"Title: {metadata.get('title', 'N/A')}")
        context_parts.append(f"Industry: {metadata.get('industry', 'N/A')}")
        context_parts.append(f"Location: {metadata.get('location', 'N/A')}")
        context_parts.append(f"\nEnrichment: {enrichment.get('content', '')}")

    if research:
        context_parts.append(f"\nWeb Research: {research.get('summary', '')}")

    return "\n".join(context_parts)
