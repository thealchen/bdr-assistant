import os
import json
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from data import LeadVectorStore
from tools.retriever import LeadRetriever
from tools.web_research import WebResearchTool
from tools.gmail_api import GmailAPI, GmailDraftTool
from tools.linkedin_api import LinkedInAPI
from tools.protect import validate_draft_output


# Initialize components
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
vector_store = LeadVectorStore()
retriever = LeadRetriever(vector_store)
web_research = WebResearchTool()
gmail_api = GmailAPI()
gmail_tool = GmailDraftTool()
linkedin_api = LinkedInAPI()


def retrieve_enrichment(state: Dict) -> Dict:
    """Retrieve lead enrichment data from vector store."""
    input_type = state["input_type"]
    
    # For name+company inputs, skip vector store and go directly to web research
    if input_type == "name_company":
        return {
            "enrichment_data": None,
            "enrichment_sufficient": False,
            "status": ["enrichment_skipped_name_company"]
        }
    
    # For email inputs, use existing vector store lookup
    lead_email = state["lead_email"]
    if not lead_email:
        return {
            "enrichment_data": None,
            "enrichment_sufficient": False,
            "status": ["enrichment_error"],
            "error": "No email provided for email-based lookup"
        }

    try:
        # Use LangChain tool's invoke method
        result_json = retriever.invoke({"lead_identifier": lead_email, "k": 1})
        results = json.loads(result_json)

        if results:
            enrichment_data = results[0]
            # Check if enrichment has sufficient detail
            enrichment_sufficient = _check_enrichment_quality(enrichment_data)

            return {
                "enrichment_data": enrichment_data,
                "enrichment_sufficient": enrichment_sufficient,
                "status": ["enrichment_retrieved"]
            }
        else:
            return {
                "enrichment_data": None,
                "enrichment_sufficient": False,
                "status": ["enrichment_not_found"]
            }
    except Exception as e:
        return {
            "enrichment_data": None,
            "enrichment_sufficient": False,
            "status": ["enrichment_error"],
            "error": str(e)
        }


def web_research_node(state: Dict) -> Dict:
    """Perform web research on the lead."""
    input_type = state["input_type"]
    enrichment_data = state.get("enrichment_data") or {}
    
    # Determine research parameters based on input type
    if input_type == "email":
        # Email-based research - use email + enrichment metadata
        lead_email = state["lead_email"]
        company = enrichment_data.get("metadata", {}).get("company", "")
        title = enrichment_data.get("metadata", {}).get("title", "")
        
        # Append "company" to avoid ambiguous searches (e.g., "Visa" vs "visa immigration")
        company_search = f"{company} company" if company else ""
        
        research_params = {
            "email": lead_email,
            "company": company_search,
            "title": title
        }
    else:
        # Name+company research - use name and company directly
        lead_name = state["lead_name"]
        lead_company = state["lead_company"]
        
        # Create a placeholder email for the tool (required parameter)
        placeholder_email = f"{lead_name.lower().replace(' ', '.')}@{lead_company.lower().replace(' ', '')}.com"
        
        # Append "company" to avoid ambiguous searches
        company_search = f"{lead_company} company" if lead_company else ""
        
        research_params = {
            "email": placeholder_email,
            "company": company_search,
            "title": ""  # We don't have title for name+company inputs
        }

    try:
        print(f"🔍 Web research for: {research_params.get('company', 'Unknown')} ({research_params.get('title', 'Unknown')})")
        
        # Use LangChain tool's invoke method
        result_json = web_research.invoke(research_params)
        research_results = json.loads(result_json)
        
        # Extract personalization hooks from research
        hooks = _extract_personalization_hooks(research_results)
        
        print(f"🎯 Hooks extracted: {len([h for h in hooks.values() if h])} of 3 types")

        return {
            "research_results": research_results,
            "personalization_hooks": hooks,
            "status": ["research_completed"]
        }
    except Exception as e:
        return {
            "research_results": None,
            "personalization_hooks": {},
            "status": ["research_error"],
            "error": str(e)
        }


def draft_email_node(state: Dict) -> Dict:
    """Draft email outreach message."""
    enrichment = state.get("enrichment_data", {})
    research = state.get("research_results", {})
    hooks = state.get("personalization_hooks", {})
    input_type = state["input_type"]
    
    # Get email or generate placeholder for name+company inputs
    if input_type == "email":
        recipient_email = state["lead_email"]
    else:
        # For name+company, we need an email for Gmail - use placeholder
        lead_name = state["lead_name"]
        lead_company = state["lead_company"]
        recipient_email = f"{lead_name.lower().replace(' ', '.')}@{lead_company.lower().replace(' ', '')}.com"

    context = _build_context(enrichment, research)

    system_prompt = """You are an expert SDR at Galileo.ai drafting personalized outreach emails.

CRITICAL REQUIREMENTS:
- You MUST reference at least ONE specific personalization hook in the first 2 sentences
- DO NOT use generic statements like "I noticed your company works in AI..."
- Connect the hook directly to how Galileo can help

Examples of GOOD openers:
- "Congrats on the $50M Series B announced last month! With your ML team scaling to 200+ models..."
- "I saw you're hiring 15 ML engineers - a clear sign of AI infrastructure expansion..."
- "Given the challenges around model drift mentioned in your recent blog post..."

Examples of BAD openers:
- "I noticed your company works in the AI space..."
- "Your role as VP of Engineering caught my attention..."

Key guidelines:
- 100-150 words
- Specific hook → Galileo value → Clear CTA
- Professional but conversational"""

    # Build hook section for prompt
    hook_section = ""
    if hooks.get("recent_event"):
        hook_section += f"\n- Recent Event: {hooks['recent_event']}"
    if hooks.get("pain_point"):
        hook_section += f"\n- Pain Point: {hooks['pain_point']}"
    if hooks.get("growth_signal"):
        hook_section += f"\n- Growth Signal: {hooks['growth_signal']}"

    if not hook_section:
        hook_section = "\n- No specific hooks found - use company/role info from context"

    user_prompt = f"""Draft an email to this lead.

PERSONALIZATION HOOKS (USE AT LEAST ONE):{hook_section}

Lead Context:
{context}

    Galileo Value: ML observability and evaluation platform for LLM applications.

    Draft the email body only (no subject line)."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        email_draft = response.content

        # Validate with Galileo Protect guardrails
        print(f"🛡️  Validating email draft with Protect guardrails...")
        validation = validate_draft_output(
            draft_text=email_draft,
            draft_type='email',
            user_input=context,
            strict_mode=True
        )

        if not validation['safe']:
            # Email blocked by guardrails
            violation_types = [v['metric'] for v in validation['violations']]
            print(f"🚨 Email blocked by Protect: {violation_types}")
            return {
                "email_draft": validation['filtered_text'],  # Blocked message
                "status": ["email_blocked_by_protect"],
                "error": f"Guardrails triggered: {', '.join(violation_types)}"
            }

        # Email passed guardrails, use validated content
        email_draft = validation['filtered_text']
        print(f"✅ Email passed Protect validation")

        # Create Gmail draft using LangChain tool
        # Get company name based on input type
        if input_type == "email":
            company_name = enrichment.get("metadata", {}).get("company", "your company")
        else:
            company_name = state["lead_company"]

        subject = f"Improving ML model quality at {company_name}"
        # Create Gmail draft - result not used but draft is created
        gmail_tool.invoke({
            "to": recipient_email,
            "subject": subject,
            "body": email_draft
        })

        return {
            "email_draft": email_draft,
            "status": ["email_drafted"]
        }
    except Exception as e:
        return {
            "email_draft": None,
            "status": ["email_error"],
            "error": str(e)
        }


def draft_linkedin_node(state: Dict) -> Dict:
    """Draft LinkedIn outreach message."""
    enrichment = state.get("enrichment_data", {})
    research = state.get("research_results", {})
    hooks = state.get("personalization_hooks", {})
    input_type = state["input_type"]
    
    # Get identifier based on input type
    if input_type == "email":
        recipient_email = state["lead_email"]
    else:
        # For name+company, use placeholder email
        lead_name = state["lead_name"]
        lead_company = state["lead_company"]
        recipient_email = f"{lead_name.lower().replace(' ', '.')}@{lead_company.lower().replace(' ', '')}.com"

    context = _build_context(enrichment, research)

    system_prompt = """You are an expert SDR drafting LinkedIn connection messages.

REQUIREMENTS:
- Under 300 characters
- MUST reference ONE personalization hook
- No sales pitch, just relevant connection reason

GOOD: "Congrats on the Series B! Would love to connect given your ML infrastructure challenges."
BAD: "I see you work in AI. Let's connect!"""

    # Build hook section
    hook_section = ""
    if hooks.get("recent_event"):
        hook_section += f"\n- Recent Event: {hooks['recent_event']}"
    if hooks.get("growth_signal"):
        hook_section += f"\n- Growth Signal: {hooks['growth_signal']}"

    if not hook_section:
        hook_section = "\n- Use company/role from context"

    user_prompt = f"""Draft LinkedIn connection request.

HOOKS (USE ONE):{hook_section}

Context: {context}

Draft connection message only (under 300 chars)."""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        linkedin_draft = response.content

        # Validate with Galileo Protect guardrails
        print(f"🛡️  Validating LinkedIn draft with Protect guardrails...")
        validation = validate_draft_output(
            draft_text=linkedin_draft,
            draft_type='linkedin',
            user_input=context,
            strict_mode=True
        )

        if not validation['safe']:
            # LinkedIn message blocked by guardrails
            violation_types = [v['metric'] for v in validation['violations']]
            print(f"🚨 LinkedIn message blocked by Protect: {violation_types}")
            return {
                "linkedin_draft": validation['filtered_text'],  # Blocked message
                "status": ["linkedin_blocked_by_protect"],
                "error": f"Guardrails triggered: {', '.join(violation_types)}"
            }

        # LinkedIn message passed guardrails, use validated content
        linkedin_draft = validation['filtered_text']
        print(f"✅ LinkedIn message passed Protect validation")

        # Note: LinkedIn API integration would post this as draft/scheduled message
        linkedin_api.create_message_draft(
            recipient_email=recipient_email,
            message=linkedin_draft
        )

        return {
            "linkedin_draft": linkedin_draft,
            "status": ["linkedin_drafted"]
        }
    except Exception as e:
        return {
            "linkedin_draft": None,
            "status": ["linkedin_error"],
            "error": str(e)
        }


def draft_call_script_node(state: Dict) -> Dict:
    """Draft call script as markdown file."""
    enrichment = state.get("enrichment_data", {})
    research = state.get("research_results", {})
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
            "status": ["call_script_drafted"]
        }
    except Exception as e:
        return {
            "call_script": None,
            "status": ["call_script_error"],
            "error": str(e)
        }


# Helper functions

def _extract_personalization_hooks(research_results: Dict) -> Dict:
    """Extract specific personalization hooks from research.

    Returns dict with:
    - recent_event: Funding, launch, acquisition (if found)
    - pain_point: Challenge or problem mentioned (if found)
    - growth_signal: Hiring, expansion indicators (if found)
    """
    hooks = {
        "recent_event": None,
        "pain_point": None,
        "growth_signal": None
    }

    if not research_results:
        return hooks

    summary = research_results.get("summary", "").lower()
    recent_events = research_results.get("recent_events", [])
    pain_signals = research_results.get("pain_signals", [])

    # Enhanced event keywords for fintech/tech companies
    event_keywords = [
        "raised", "funding", "series", "launched", "acquired", "announced", 
        "partnership", "merger", "ipo", "investment", "venture", "round",
        "expansion", "opens", "debuts", "unveils", "introduces", "releases"
    ]
    
    # Find recent event (funding, launch, etc)
    for event_text in recent_events:
        for keyword in event_keywords:
            if keyword in event_text.lower():
                # Extract sentence containing keyword
                sentences = event_text.split(".")
                for sent in sentences:
                    if keyword in sent.lower():
                        hooks["recent_event"] = sent.strip()[:150]
                        break
                if hooks["recent_event"]:
                    break
        if hooks["recent_event"]:
            break

    # Enhanced pain keywords for financial/tech sectors
    pain_keywords = [
        "challenge", "problem", "struggle", "difficult", "issue", "concern",
        "risk", "threat", "vulnerability", "compliance", "regulation", 
        "security", "fraud", "cybersecurity", "data breach", "outage"
    ]
    
    # Find pain point
    for pain_text in pain_signals:
        for keyword in pain_keywords:
            if keyword in pain_text.lower():
                sentences = pain_text.split(".")
                for sent in sentences:
                    if keyword in sent.lower():
                        hooks["pain_point"] = sent.strip()[:150]
                        break
                if hooks["pain_point"]:
                    break
        if hooks["pain_point"]:
            break

    # Enhanced growth keywords
    growth_keywords = [
        "hiring", "expanding", "growing", "adding", "recruiting", "scaling",
        "building", "team", "talent", "headcount", "positions", "jobs",
        "opening", "opportunities", "careers"
    ]
    
    # Find growth signal
    for keyword in growth_keywords:
        if keyword in summary:
            hooks["growth_signal"] = f"Currently {keyword}"
            break

    # Fallback: extract from summary if no specific hooks found
    if not any(hooks.values()) and summary:
        # Look for any interesting content in first 200 chars of summary
        if len(summary) > 50:
            # Try to find company-specific information
            sentences = summary.split(".")
            for sent in sentences[:3]:  # First 3 sentences
                sent = sent.strip()
                if len(sent) > 30 and any(word in sent.lower() for word in ["ai", "artificial intelligence", "machine learning", "technology", "digital", "innovation"]):
                    hooks["pain_point"] = f"Focus on {sent[:120]}..."
                    break
    return hooks


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
        # Show categorized research instead of just summary
        recent = research.get("recent_events", [])
        pain = research.get("pain_signals", [])

        if recent:
            recent_text = " ".join(recent)[:200]
            context_parts.append(f"\nRecent Company News: {recent_text}")
        if pain:
            pain_text = " ".join(pain)[:200]
            context_parts.append(f"\nIndustry Challenges: {pain_text}")

    return "\n".join(context_parts)
