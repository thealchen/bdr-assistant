"""Galileo Protect guardrails for SDR outreach content validation."""

import os
from typing import Dict, List, Optional, Any
import galileo_protect as gp


# Module-level variables for Protect project/stage
_PROTECT_PROJECT_ID: Optional[str] = None
_PROTECT_STAGE_ID: Optional[str] = None


def init_protect() -> str:
    """Initialize Protect project and stage (call once at startup).

    Returns:
        stage_id: The Galileo Protect stage ID for this project
    """
    global _PROTECT_PROJECT_ID, _PROTECT_STAGE_ID

    if not _PROTECT_STAGE_ID:
        try:
            # Set default console URL if not provided
            if not os.getenv('GALILEO_CONSOLE_URL'):
                os.environ['GALILEO_CONSOLE_URL'] = 'https://console.galileo.ai'
                print("ℹ️  Using default Galileo console URL: https://console.galileo.ai")

            # Try to create project, or use existing one
            try:
                project = gp.create_project('sdr-outreach-assistant-protect')
                _PROTECT_PROJECT_ID = project.id
                print(f"✅ Created new Protect project: {_PROTECT_PROJECT_ID}")
            except Exception as e:
                # Project likely already exists - extract ID from error or use default
                if "already exists" in str(e):
                    # Try to get existing project (this is a workaround - ideally use list_projects)
                    # For now, use a known ID from previous run
                    _PROTECT_PROJECT_ID = "a26c7755-6b64-4ce2-8eaf-18218578e18e"
                    print(f"ℹ️  Using existing Protect project: {_PROTECT_PROJECT_ID}")
                else:
                    raise

            # Try to create stage, or use existing one
            try:
                stage = gp.create_stage(
                    name="production",
                    project_id=_PROTECT_PROJECT_ID
                )
                _PROTECT_STAGE_ID = stage.id
                print(f"✅ Created new Protect stage: {_PROTECT_STAGE_ID}")
            except Exception as e:
                # Stage likely already exists
                if "already exists" in str(e):
                    # Use known stage ID from previous run
                    _PROTECT_STAGE_ID = "6f9b2c17-3cb4-4925-898c-bbff5edd2a87"
                    print(f"ℹ️  Using existing Protect stage: {_PROTECT_STAGE_ID}")
                else:
                    raise

            print(f"✅ Galileo Protect ready: project={_PROTECT_PROJECT_ID}, stage={_PROTECT_STAGE_ID}")

        except Exception as e:
            print(f"⚠️  Protect initialization warning: {e}")
            # Set to fallback to avoid repeated failures
            _PROTECT_STAGE_ID = "fallback"

    return _PROTECT_STAGE_ID


def validate_draft_output(
    draft_text: str,
    draft_type: str,
    user_input: str = "",
    strict_mode: bool = True
) -> Dict[str, Any]:
    """Validate generated draft for PII, toxicity, and professional tone.

    Args:
        draft_text: The generated content to validate (email/LinkedIn/call script)
        draft_type: Type of content ('email', 'linkedin', 'call_script')
        user_input: Original context/input used to generate the draft
        strict_mode: If True, block on any violation. If False, allow with warning.

    Returns:
        Dict containing:
            - safe: bool - Whether content passed all guardrails
            - filtered_text: str - Original or blocked message
            - violations: list - List of triggered rules
            - original_text: str - Original unfiltered text
            - error: str (optional) - Error message if validation failed
    """
    # Get stage ID (initialize if needed)
    stage_id = init_protect()

    # Skip validation if Protect initialization failed
    if stage_id == "fallback":
        print("⚠️  Protect validation skipped (initialization failed)")
        return {
            'safe': True,
            'filtered_text': draft_text,
            'violations': [],
            'original_text': draft_text,
            'error': 'Protect not initialized'
        }

    # Define rulesets based on draft type
    rulesets = _build_rulesets(draft_type, strict_mode)

    try:
        # Invoke Protect with guardrails
        response = gp.invoke(
            payload={
                "input": user_input or f"Generate {draft_type} for SDR outreach",
                "output": draft_text
            },
            prioritized_rulesets=rulesets,
            stage_id=stage_id,
            timeout=10
        )

        # Handle response - it might be a dict or an object
        if hasattr(response, '__dict__'):
            # Convert object to dict
            response_dict = vars(response) if hasattr(response, '__dict__') else {}
        else:
            response_dict = response if isinstance(response, dict) else {}

        # Check if output was overridden (blocked)
        is_overridden = response_dict.get('overridden', False) if response_dict else False
        filtered = response_dict.get('output', draft_text) if response_dict else draft_text
        triggered_rules = response_dict.get('triggered_rules', []) if response_dict else []

        # Extract violation details
        violations = []
        for rule in triggered_rules:
            if isinstance(rule, dict):
                violations.append({
                    'metric': rule.get('metric', 'unknown'),
                    'value': rule.get('value'),
                    'threshold': rule.get('threshold')
                })
            else:
                # Handle rule as object
                violations.append({
                    'metric': getattr(rule, 'metric', 'unknown'),
                    'value': getattr(rule, 'value', None),
                    'threshold': getattr(rule, 'threshold', None)
                })

        is_safe = not is_overridden

        if not is_safe:
            print(f"🚨 Protect blocked {draft_type}: {[v['metric'] for v in violations]}")
        else:
            print(f"✅ Protect validated {draft_type}: passed all guardrails")

        return {
            'safe': is_safe,
            'filtered_text': filtered,
            'violations': violations,
            'original_text': draft_text
        }

    except Exception as e:
        # Fail-safe: if Protect fails, log error but allow draft through
        print(f"⚠️  Protect validation error for {draft_type}: {e}")

        # In production, decide whether to fail-open or fail-closed
        # For now: fail-open (allow content through with warning)
        return {
            'safe': True,  # Fail open
            'filtered_text': draft_text,
            'violations': [],
            'original_text': draft_text,
            'error': str(e)
        }


def _build_rulesets(draft_type: str, strict_mode: bool) -> List[Dict]:
    """Build appropriate rulesets based on draft type.

    Args:
        draft_type: 'email', 'linkedin', or 'call_script'
        strict_mode: If True, use stricter thresholds

    Returns:
        List of ruleset dictionaries for gp.invoke()
    """
    # Shared rulesets for all content types
    rulesets = [
        # Rule 1: Block PII in output
        {
            "rules": [{
                "metric": "pii",
                "operator": "contains",
                "target_value": "any"  # Block any PII type
            }],
            "action": {
                "type": "OVERRIDE",
                "choices": [
                    f"[BLOCKED BY PROTECT: PII detected in {draft_type.upper()}. "
                    f"Please regenerate without personal information.]"
                ]
            }
        },

        # Rule 2: Block toxic content
        {
            "rules": [{
                "metric": "toxicity",
                "operator": "gt",  # Use 'gt' not 'greater_than'
                "target_value": 0.7 if strict_mode else 0.85
            }],
            "action": {
                "type": "OVERRIDE",
                "choices": [
                    f"[BLOCKED BY PROTECT: Toxic content detected in {draft_type.upper()}. "
                    f"Please regenerate with professional language.]"
                ]
            }
        },

        # Rule 3: Ensure professional tone (block unprofessional emotions)
        {
            "rules": [{
                "metric": "tone",
                "operator": "contains",
                "target_value": ["anger", "annoyance"]
            }],
            "action": {
                "type": "OVERRIDE",
                "choices": [
                    f"[BLOCKED BY PROTECT: Unprofessional tone in {draft_type.upper()}. "
                    f"Please regenerate with neutral/positive tone.]"
                ]
            }
        }
    ]

    # LinkedIn-specific: stricter tone (300 char limit makes every word count)
    if draft_type == "linkedin":
        rulesets.append({
            "rules": [{
                "metric": "tone",
                "operator": "contains",
                "target_value": ["fear", "sadness"]  # Also block negative emotions
            }],
            "action": {
                "type": "OVERRIDE",
                "choices": [
                    "[BLOCKED BY PROTECT: Negative tone in LinkedIn message. "
                    "Please regenerate with positive/professional tone.]"
                ]
            }
        })

    return rulesets


def check_input_safety(lead_data: Dict) -> Dict[str, Any]:
    """Validate incoming lead data for PII or sensitive information.

    Args:
        lead_data: Dictionary containing lead information

    Returns:
        Dict with safety assessment
    """
    # Build text representation of lead data
    lead_text = " ".join([
        str(v) for k, v in lead_data.items()
        if v and k not in ['status', 'error', 'personalization_hooks']
    ])

    try:
        stage_id = init_protect()

        if stage_id == "fallback":
            return {'safe': True, 'violations': []}

        # Simple PII check on input data
        response = gp.invoke(
            payload={
                "input": "",
                "output": lead_text
            },
            prioritized_rulesets=[{
                "rules": [{
                    "metric": "pii",
                    "operator": "contains",
                    "target_value": ["ssn", "credit_card", "bank_account"]
                }],
                "action": {
                    "type": "OVERRIDE",
                    "choices": ["[SENSITIVE DATA DETECTED]"]
                }
            }],
            stage_id=stage_id,
            timeout=5
        )

        is_safe = not response.get('overridden', False)
        violations = response.get('triggered_rules', [])

        return {
            'safe': is_safe,
            'violations': violations
        }

    except Exception as e:
        print(f"⚠️  Input safety check error: {e}")
        return {
            'safe': True,  # Fail open for input validation
            'violations': [],
            'error': str(e)
        }
