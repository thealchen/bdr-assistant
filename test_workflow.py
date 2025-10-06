"""Test script to run workflow with sample data."""

import os
from dotenv import load_dotenv
from graph import app
from graph.state import LeadState

load_dotenv()


def test_workflow():
    """Test the workflow with a sample lead."""

    print("=" * 60)
    print("Testing SDR Outreach Assistant Workflow")
    print("=" * 60)

    # Initialize state with test lead
    initial_state: LeadState = {
        "lead_id": "lead_001",
        "lead_email": "sarah.johnson@techcorp.com",
        "enrichment_data": None,
        "enrichment_sufficient": False,
        "research_results": None,
        "email_draft": None,
        "linkedin_draft": None,
        "call_script": None,
        "status": "started",
        "error": None
    }

    print(f"\n📧 Processing lead: {initial_state['lead_email']}")
    print("-" * 60)

    try:
        # Run workflow
        print("\n⚙️  Running workflow...\n")
        result = app.invoke(initial_state)

        # Display results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)

        print(f"\n✓ Status: {result.get('status')}")
        print(f"✓ Enrichment sufficient: {result.get('enrichment_sufficient')}")
        print(f"✓ Research performed: {bool(result.get('research_results'))}")

        if result.get("error"):
            print(f"⚠️  Error: {result.get('error')}")

        # Email draft
        print("\n" + "-" * 60)
        print("📧 EMAIL DRAFT")
        print("-" * 60)
        email = result.get("email_draft")
        if email:
            print(email)
        else:
            print("(not generated)")

        # LinkedIn draft
        print("\n" + "-" * 60)
        print("💼 LINKEDIN MESSAGE")
        print("-" * 60)
        linkedin = result.get("linkedin_draft")
        if linkedin:
            print(linkedin)
        else:
            print("(not generated)")

        # Call script
        print("\n" + "-" * 60)
        print("📞 CALL SCRIPT")
        print("-" * 60)
        call_script = result.get("call_script")
        if call_script:
            print(call_script[:500] + "..." if len(call_script) > 500 else call_script)
            print(f"\n✓ Full script saved to: outputs/call_script_{result.get('lead_id')}.md")
        else:
            print("(not generated)")

        print("\n" + "=" * 60)
        print("✓ Test completed successfully!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error running workflow: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check for required API keys
    required_keys = ["OPENAI_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]

    if missing_keys:
        print("⚠️  Missing required environment variables:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\nPlease set these in your .env file")
    else:
        test_workflow()
