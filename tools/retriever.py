from typing import List, Dict, Optional
from data import LeadVectorStore


class LeadRetriever:
    """Retrieves lead enrichment data from vector store."""

    def __init__(self, vector_store: LeadVectorStore):
        self.vector_store = vector_store

    def retrieve(self, lead_identifier: str, k: int = 1) -> List[Dict]:
        """Retrieve enrichment data for a lead.

        Args:
            lead_identifier: Email or lead_id
            k: Number of results to return

        Returns:
            List of dicts with enrichment content and metadata
        """
        return self.vector_store.search_lead(lead_identifier, k=k)
