"""Script to load sample lead data into vector store for testing."""

from data import LeadVectorStore, EnrichmentLoader

# Sample lead data
sample_leads = [
    {
        "lead_id": "lead_001",
        "email": "sarah.johnson@techcorp.com",
        "company": "TechCorp",
        "industry": "Software",
        "revenue": "10M-50M",
        "title": "VP of Engineering",
        "location": "San Francisco, CA",
        "enrichment_text": """
        TechCorp is a rapidly growing SaaS company specializing in cloud infrastructure.
        They recently raised a Series B and are scaling their engineering team.
        The company uses modern ML/AI tools and has 200+ employees.
        Key technologies: Python, Kubernetes, AWS.
        """
    },
    {
        "lead_id": "lead_002",
        "email": "mike.chen@datainsights.io",
        "company": "DataInsights",
        "industry": "Data Analytics",
        "revenue": "5M-10M",
        "title": "Director of Data Science",
        "location": "New York, NY",
        "enrichment_text": """
        DataInsights provides analytics solutions for enterprise clients.
        They have a team of 15 data scientists working on ML models.
        Recent challenges include model monitoring and evaluation.
        Technologies: Python, Spark, TensorFlow.
        """
    },
    {
        "lead_id": "lead_003",
        "email": "emma.wilson@financeai.com",
        "company": "FinanceAI",
        "industry": "Financial Services",
        "revenue": "50M-100M",
        "title": "Head of AI/ML",
        "location": "Boston, MA",
        "enrichment_text": """
        FinanceAI uses machine learning for fraud detection and risk assessment.
        They're building LLM-powered tools for customer service.
        Team of 50+ engineers, heavily invested in AI infrastructure.
        Compliance and model explainability are critical concerns.
        """
    }
]


def load_sample_data():
    """Load sample leads into vector store."""
    print("Initializing vector store...")
    vector_store = LeadVectorStore()

    print(f"Adding {len(sample_leads)} sample leads...")
    vector_store.add_leads(sample_leads)

    print("✓ Sample data loaded successfully!")
    print("\nTest leads:")
    for lead in sample_leads:
        print(f"  - {lead['email']} ({lead['company']})")


if __name__ == "__main__":
    load_sample_data()
