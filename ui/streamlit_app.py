import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph import invoke_with_galileo
from graph.state import LeadState
from evaluation import evaluate_workflow_output
from utils.input_parser import parse_lead_input, get_display_identifier


st.set_page_config(
    page_title="SDR Outreach Assistant",
    page_icon="📧",
    layout="wide"
)

st.title("📧 SDR Outreach Assistant")

# Sidebar configuration
with st.sidebar:
    st.header("Configuration")

    st.info("🔍 Galileo tracking enabled - all runs are logged")

    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This tool automates:
    - Lead enrichment retrieval
    - Web research (if needed)
    - Email draft (Gmail)
    - LinkedIn message draft
    - Call script generation
    """)

# Main input form
col1, col2 = st.columns(2)

with col1:
    lead_input = st.text_input(
        "Lead Input *",
        placeholder="john.doe@acme.com OR john smith - Nike",
        help="Enter either an email address or name + company (separated by ' - ')"
    )

with col2:
    lead_id = st.text_input(
        "Lead ID",
        placeholder="Optional - auto-generated if empty",
        help="Unique identifier for the lead"
    )

# Input format help
if lead_input:
    try:
        parsed_input = parse_lead_input(lead_input)
        input_type = parsed_input["input_type"]
        display_id = get_display_identifier(parsed_input)
        
        if input_type == "email":
            st.success(f"✅ Email format detected: {display_id}")
        else:
            st.success(f"✅ Name + Company format detected: {display_id}")
    except ValueError as e:
        st.error(f"❌ {str(e)}")
else:
    st.info("👆 Enter lead information to get started")
    st.markdown("""
    **Supported formats:**
    - Email: `john.doe@acme.com`
    - Name + Company: `john smith - Nike`
    """)

# Generate button
if st.button("🚀 Generate Outreach", type="primary", disabled=not lead_input):

    try:
        # Parse and validate input
        parsed_input = parse_lead_input(lead_input)
        
        if not lead_id:
            # Generate lead_id based on input type
            if parsed_input["input_type"] == "email":
                lead_id = parsed_input["lead_email"]
            else:
                # Use name_company format for ID
                name_part = parsed_input["lead_name"].lower().replace(" ", "_")
                company_part = parsed_input["lead_company"].lower().replace(" ", "_")
                lead_id = f"{name_part}_{company_part}"

        with st.spinner("Generating outreach materials..."):

            # Initialize state
            initial_state: LeadState = {
                "lead_id": lead_id,
                "input_type": parsed_input["input_type"],
                "original_input": parsed_input["original_input"],
                "lead_email": parsed_input["lead_email"],
                "lead_name": parsed_input["lead_name"],
                "lead_company": parsed_input["lead_company"],
                "enrichment_data": None,
                "enrichment_sufficient": False,
                "research_results": None,
                "personalization_hooks": {},  # Initialize as empty dict, not None
                "email_draft": None,
                "linkedin_draft": None,
                "call_script": None,
                "status": [],
                "error": None
            }
            
            print(f"🔄 Starting workflow for: {parsed_input['original_input']}")  # Debug log
            print(f"📋 State initialized for lead_id: {lead_id}")  # Debug log
            
            # Run workflow with Galileo tracking
            result = invoke_with_galileo(initial_state)
            
            print(f"✅ Workflow completed with status: {result.get('status')}")  # Debug log
            
            # Display results
            display_name = get_display_identifier(parsed_input)
            st.success(f"✅ Outreach materials generated for {display_name}!")

            # Status info
            with st.expander("ℹ️ Workflow Details", expanded=False):
                st.json({
                    "input_type": result.get("input_type"),
                    "status": result.get("status"),
                    "enrichment_sufficient": result.get("enrichment_sufficient"),
                    "research_performed": bool(result.get("research_results"))
                })

            # Email draft
            st.markdown("---")
            st.subheader("📧 Email Draft")
            email_draft = result.get("email_draft")
            if email_draft:
                st.text_area(
                    "Email Body",
                    value=email_draft,
                    height=200,
                    help="Draft created in Gmail"
                )
                st.info("✓ Draft created in Gmail")
            else:
                st.warning("Email draft not generated")

            # LinkedIn draft
            st.markdown("---")
            st.subheader("💼 LinkedIn Message")
            linkedin_draft = result.get("linkedin_draft")
            if linkedin_draft:
                st.text_area(
                    "Connection Message",
                    value=linkedin_draft,
                    height=150,
                    help="Message for LinkedIn connection request"
                )
                st.info("✓ Message ready for LinkedIn")
            else:
                st.warning("LinkedIn message not generated")

            # Call script
            st.markdown("---")
            st.subheader("📞 Call Script")
            call_script = result.get("call_script")
            if call_script:
                st.markdown(call_script)

                # Download button
                st.download_button(
                    label="⬇️ Download Call Script",
                    data=call_script,
                    file_name=f"call_script_{lead_id}.md",
                    mime="text/markdown"
                )
            else:
                st.warning("Call script not generated")

            # Evaluation metrics
            st.markdown("---")
            st.subheader("📊 Quality Metrics")

            metrics = evaluate_workflow_output(initial_state, result)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Email Quality",
                    f"{metrics.get('email_quality', 0):.2f}",
                    help="Overall email draft quality"
                )
                st.metric(
                    "Email Personalization",
                    f"{metrics.get('email_personalization', 0):.2f}",
                    help="How personalized the email is"
                )

            with col2:
                st.metric(
                    "LinkedIn Quality",
                    f"{metrics.get('linkedin_quality', 0):.2f}",
                    help="Overall LinkedIn message quality"
                )
                st.metric(
                    "Research Depth",
                    f"{metrics.get('research_depth', 0):.2f}",
                    help="Comprehensiveness of research"
                )

            with col3:
                st.metric(
                    "Call Script Quality",
                    f"{metrics.get('call_script_quality', 0):.2f}",
                    help="Overall call script quality"
                )
                st.metric(
                    "Completion Rate",
                    f"{metrics.get('completion_rate', 0):.0%}",
                    help="Percentage of drafts completed"
                )

    except ValueError as e:
        st.error(f"❌ Invalid input format: {str(e)}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error generating outreach: {str(e)}")
        st.exception(e)
        print(f"🚨 Error in workflow: {str(e)}")  # Debug log
        st.stop()

# Instructions
