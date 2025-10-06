from typing import Dict, List


def calculate_personalization_score(draft: str, enrichment: Dict) -> float:
    """Calculate how personalized a draft is based on enrichment data usage.

    Args:
        draft: Draft text (email, LinkedIn, or call script)
        enrichment: Enrichment data that should be referenced

    Returns:
        Score between 0 and 1
    """
    if not draft or not enrichment:
        return 0.0

    score = 0.0
    draft_lower = draft.lower()

    # Check if key enrichment fields are referenced
    metadata = enrichment.get("metadata", {})

    # Company mention (0.3)
    company = metadata.get("company", "")
    if company and company.lower() in draft_lower:
        score += 0.3

    # Industry/role mention (0.2)
    industry = metadata.get("industry", "")
    title = metadata.get("title", "")
    if (industry and industry.lower() in draft_lower) or (title and title.lower() in draft_lower):
        score += 0.2

    # Specific details from enrichment content (0.3)
    enrichment_content = enrichment.get("content", "")
    if enrichment_content:
        # Check for overlap of meaningful words
        content_words = set(enrichment_content.lower().split())
        draft_words = set(draft_lower.split())
        overlap = len(content_words & draft_words)
        score += min(overlap / 20, 0.3)

    # Length and structure (0.2)
    if len(draft) > 100:
        score += 0.2

    return round(min(score, 1.0), 2)


def calculate_research_depth_score(research_results: Dict) -> float:
    """Calculate how comprehensive the research was.

    Args:
        research_results: Research data from web research node

    Returns:
        Score between 0 and 1
    """
    if not research_results:
        return 0.0

    score = 0.0

    # Has research summary (0.5)
    if research_results.get("summary"):
        score += 0.5

    # Number of sources (0.5)
    sources = research_results.get("sources", [])
    source_score = min(len(sources) / 3, 0.5)
    score += source_score

    return round(score, 2)


def calculate_draft_quality_score(draft: str, draft_type: str) -> float:
    """Calculate quality score for a draft.

    Args:
        draft: Draft text
        draft_type: Type of draft ('email', 'linkedin', 'call_script')

    Returns:
        Score between 0 and 1
    """
    if not draft:
        return 0.0

    score = 0.0

    # Length appropriateness
    expected_length = {
        "email": (100, 200),
        "linkedin": (50, 300),
        "call_script": (300, 1000)
    }

    min_len, max_len = expected_length.get(draft_type, (100, 500))
    draft_len = len(draft)

    if min_len <= draft_len <= max_len:
        score += 0.4
    else:
        # Partial credit for being close
        if draft_len < min_len:
            score += 0.2 * (draft_len / min_len)
        else:
            score += 0.2 * (max_len / draft_len)

    # Has call-to-action (0.3)
    cta_keywords = ["call", "meeting", "chat", "connect", "discuss", "schedule", "book"]
    if any(kw in draft.lower() for kw in cta_keywords):
        score += 0.3

    # Professional tone indicators (0.3)
    professional_indicators = ["thank", "appreciate", "would love", "happy to", "let me know"]
    matches = sum(1 for ind in professional_indicators if ind in draft.lower())
    score += min(matches / len(professional_indicators), 0.3)

    return round(min(score, 1.0), 2)


def evaluate_workflow_output(
    input_state: Dict,
    output_state: Dict
) -> Dict[str, float]:
    """Evaluate complete workflow output.

    Args:
        input_state: Input state with lead data
        output_state: Output state with drafts

    Returns:
        Dict of metric scores
    """
    metrics = {}

    enrichment = output_state.get("enrichment_data", {})
    research = output_state.get("research_results", {})

    # Email quality
    email_draft = output_state.get("email_draft", "")
    if email_draft:
        metrics["email_quality"] = calculate_draft_quality_score(email_draft, "email")
        metrics["email_personalization"] = calculate_personalization_score(email_draft, enrichment)

    # LinkedIn quality
    linkedin_draft = output_state.get("linkedin_draft", "")
    if linkedin_draft:
        metrics["linkedin_quality"] = calculate_draft_quality_score(linkedin_draft, "linkedin")
        metrics["linkedin_personalization"] = calculate_personalization_score(linkedin_draft, enrichment)

    # Call script quality
    call_script = output_state.get("call_script", "")
    if call_script:
        metrics["call_script_quality"] = calculate_draft_quality_score(call_script, "call_script")
        metrics["call_script_personalization"] = calculate_personalization_score(call_script, enrichment)

    # Research depth
    metrics["research_depth"] = calculate_research_depth_score(research)

    # Overall completion
    metrics["completion_rate"] = sum([
        bool(email_draft),
        bool(linkedin_draft),
        bool(call_script)
    ]) / 3.0

    return metrics
