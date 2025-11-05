# SDR Outreach Assistant

Automates lead research and outreach drafting for sales development representatives.

## Features

- Retrieves lead enrichment data from vector store
- Performs web research when enrichment is insufficient
- Generates personalized email drafts in Gmail
- Creates LinkedIn message drafts
- Produces call scripts as markdown files
- Evaluates output quality using Galileo SDK

## Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Required variables:
- `OPENAI_API_KEY` - OpenAI API key
- `TAVILY_API_KEY` - Tavily search API key
- `GALILEO_API_KEY` - Galileo v2.0 evaluation API key
- `GALILEO_PROJECT` - Galileo project name (e.g., "sdr-outreach-assistant")

Optional (for full functionality):
- `GMAIL_CREDENTIALS_PATH` - Path to Gmail API credentials
- `LINKEDIN_EMAIL` / `LINKEDIN_PASSWORD` - LinkedIn credentials
- `GOOGLE_SEARCH_API_KEY` - Google Custom Search API
- `GALILEO_CONSOLE_URL` - Galileo console URL (only for custom deployments)

### Initialize Vector Store

Load lead enrichment data:

```python
from data import LeadVectorStore, EnrichmentLoader

# Load from Apollo export
leads = EnrichmentLoader.load_from_apollo_export("apollo_export.csv")

# Add to vector store
vector_store = LeadVectorStore()
vector_store.add_leads(leads)
```

### Gmail API Setup (Optional)

1. Create project in Google Cloud Console
2. Enable Gmail API
3. Download OAuth credentials as `credentials.json`
4. Place in project root
5. First run will prompt for authentication

## Usage

### Run Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

Enter lead email or [NAME - COMPANY] and generate outreach materials.

## Project Structure

```
sdr-outreach-assistant/
├── graph/           # LangGraph workflow
├── tools/           # API integrations
├── data/            # Vector store and enrichment
├── evaluation/      # Galileo evaluation
├── ui/              # Streamlit interface
└── outputs/         # Generated call scripts
```

## Workflow

1. **retrieve_enrichment** - Query vector store for lead data
2. **web_research** (conditional) - Search web if enrichment insufficient
3. **draft_email** - Generate Gmail draft
4. **draft_linkedin** - Generate LinkedIn message
5. **draft_call_script** - Generate markdown call script

All three drafting steps run in parallel.
