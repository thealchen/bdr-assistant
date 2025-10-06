import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph import app
from graph.state import LeadState
from evaluation import GalileoEvaluator, evaluate_workflow_output


st.set_page_config(
    page_title="SDR Outreach Assistant",
    page_icon="📧",
    layout="wide"
)

st.title("📧 SDR Outreach Assistant")
st.markdown("Generate personalized outreach drafts for leads")

# Sidebar configuration
with st.sidebar:
    st.header("Configuration")

    use_galileo = st.checkbox("Enable Galileo Evaluation", value=False)

    if use_galileo:
        st.info("Galileo logging enabled. Results will be tracked in your project.")

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
    lead_email = st.text_input(
        "Lead Email *",
        placeholder="john.doe@acme.com",
        help="Email address of the lead to research"
    )

with col2:
    lead_id = st.text_input(
        "Lead ID",
        placeholder="Optional - defaults to email",
        help="Unique identifier for the lead"
    )

# Generate button
if st.button("🚀 Generate Outreach", type="primary", disabled=not lead_email):

    if not lead_id:
        lead_id = lead_email

    with st.spinner("Generating outreach materials..."):

        # Initialize state
        initial_state: LeadState = {
            "lead_id": lead_id,
            "lead_email": lead_email,
            "enrichment_data": None,
            "enrichment_sufficient": False,
            "research_results": None,
            "email_draft": None,
            "linkedin_draft": None,
            "call_script": None,
            "status": "started",
            "error": None
        }

        try:
            # Run workflow
            if use_galileo:
                evaluator = GalileoEvaluator()
                result = evaluator.run_workflow(
                    lambda state: app.invoke(state),
                    initial_state,
                    experiment_name="streamlit_run"
                )
            else:
                result = app.invoke(initial_state)

            # Display results
            st.success("✅ Outreach materials generated successfully!")

            # Status info
            with st.expander("ℹ️ Workflow Details", expanded=False):
                st.json({
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

            # Evaluation metrics (if enabled)
            if use_galileo:
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

        except Exception as e:
            st.error(f"❌ Error generating outreach: {str(e)}")
            st.exception(e)

# Instructions
if not lead_email:
    st.info("👆 Enter a lead email to get started")

    with st.expander("📖 Setup Instructions"):
        st.markdown("""
        ### First Time Setup

        1. **Install dependencies**:
           ```bash
           pip install -r requirements.txt
           ```

        2. **Configure environment variables**:
           - Copy `.env.example` to `.env`
           - Add your API keys (OpenAI, Tavily, Gmail, Galileo)

        3. **Initialize vector store**:
           - Load lead enrichment data from Apollo/reo.dev
           - Run data loading script to populate Chroma

        4. **Gmail API setup** (optional):
           - Download credentials from Google Cloud Console
           - Save as `credentials.json` in project root
           - First run will prompt for authentication

        5. **Run Streamlit**:
           ```bash
           streamlit run ui/streamlit_app.py
           ```
        """)
