import json
from typing import List, Dict, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from data import LeadVectorStore


class LeadEnrichmentInput(BaseModel):
    """Input schema for lead enrichment retrieval tool."""
    lead_identifier: str = Field(description="Lead email address or lead_id")
    k: int = Field(default=1, description="Number of results to return")


class LeadRetriever(BaseTool):
    """Retrieves lead enrichment data from vector store."""

    name: str = "lead_enrichment"
    description: str = "Retrieve enrichment data for a lead from the vector database. Returns lead profile information, company details, and other context."
    args_schema: Type[BaseModel] = LeadEnrichmentInput

    vector_store: Optional[LeadVectorStore] = None

    def __init__(self, vector_store: LeadVectorStore, **kwargs):
        super().__init__(**kwargs)
        self.vector_store = vector_store

    def _run(self, lead_identifier: str, k: int = 1) -> str:
        """Retrieve enrichment data for a lead.

        Args:
            lead_identifier: Email or lead_id
            k: Number of results to return

        Returns:
            JSON string with enrichment results
        """
        results = self.vector_store.search_lead(lead_identifier, k=k)
        return json.dumps(results)
