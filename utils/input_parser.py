import re
from typing import Dict, Literal, Tuple


def parse_lead_input(input_str: str) -> Dict:
    """Parse lead input and detect format type.
    
    Supports two formats:
    1. Email: john.doe@acme.com
    2. Name + Company: john smith - Nike
    
    Args:
        input_str: Raw input string from user
        
    Returns:
        Dict with parsed components and input type
        
    Raises:
        ValueError: If input format is invalid
    """
    if not input_str or not input_str.strip():
        raise ValueError("Input cannot be empty")
    
    input_str = input_str.strip()
    
    # Check for email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, input_str):
        return {
            "input_type": "email",
            "lead_email": input_str,
            "lead_name": None,
            "lead_company": None,
            "original_input": input_str
        }
    
    # Check for name + company format (name - company)
    name_company_pattern = r'^(.+?)\s*-\s*(.+)$'
    match = re.match(name_company_pattern, input_str)
    
    if match:
        name_part = match.group(1).strip()
        company_part = match.group(2).strip()
        
        # Validate name (should have at least first and last name)
        name_words = name_part.split()
        if len(name_words) < 2:
            raise ValueError("Name should include at least first and last name (e.g., 'john smith - Nike')")
        
        # Validate company (should not be empty)
        if not company_part:
            raise ValueError("Company name cannot be empty")
        
        return {
            "input_type": "name_company",
            "lead_email": None,
            "lead_name": name_part,
            "lead_company": company_part,
            "original_input": input_str
        }
    
    # Invalid format
    raise ValueError(
        "Invalid input format. Use either:\n"
        "• Email: john.doe@acme.com\n"
        "• Name + Company: john smith - Nike"
    )


def validate_parsed_input(parsed_data: Dict) -> bool:
    """Validate parsed input data structure.
    
    Args:
        parsed_data: Result from parse_lead_input()
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["input_type", "original_input"]
    
    # Check required fields exist
    if not all(field in parsed_data for field in required_fields):
        return False
    
    input_type = parsed_data.get("input_type")
    
    # Validate email format
    if input_type == "email":
        return (
            parsed_data.get("lead_email") is not None and
            parsed_data.get("lead_name") is None and
            parsed_data.get("lead_company") is None
        )
    
    # Validate name+company format
    if input_type == "name_company":
        return (
            parsed_data.get("lead_email") is None and
            parsed_data.get("lead_name") is not None and
            parsed_data.get("lead_company") is not None
        )
    
    return False


def get_display_identifier(parsed_data: Dict) -> str:
    """Get human-readable identifier for the lead.
    
    Args:
        parsed_data: Result from parse_lead_input()
        
    Returns:
        Display string for the lead
    """
    input_type = parsed_data.get("input_type")
    
    if input_type == "email":
        return parsed_data.get("lead_email", "Unknown")
    
    if input_type == "name_company":
        name = parsed_data.get("lead_name", "Unknown")
        company = parsed_data.get("lead_company", "Unknown")
        return f"{name} at {company}"
    
    return parsed_data.get("original_input", "Unknown")