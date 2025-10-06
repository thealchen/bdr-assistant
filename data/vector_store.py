import os
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()


class LeadVectorStore:
    """Vector store for lead enrichment data."""

    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIRECTORY", "./chroma_db"
        )
        self.embeddings = OpenAIEmbeddings()
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.vectorstore = Chroma(
            client=self.client,
            collection_name="lead_enrichment",
            embedding_function=self.embeddings
        )

    def add_leads(self, leads: List[Dict]) -> None:
        """Add lead enrichment data to vector store.

        Args:
            leads: List of dicts with keys: lead_id, email, company, industry,
                   revenue, title, location, enrichment_text
        """
        texts = []
        metadatas = []
        ids = []

        for lead in leads:
            # Combine all enrichment data into searchable text
            enrichment_text = f"""
            Company: {lead.get('company', 'N/A')}
            Industry: {lead.get('industry', 'N/A')}
            Revenue: {lead.get('revenue', 'N/A')}
            Title: {lead.get('title', 'N/A')}
            Location: {lead.get('location', 'N/A')}
            {lead.get('enrichment_text', '')}
            """

            texts.append(enrichment_text.strip())
            metadatas.append({
                "lead_id": lead.get("lead_id", ""),
                "email": lead.get("email", ""),
                "company": lead.get("company", ""),
                "industry": lead.get("industry", ""),
                "revenue": str(lead.get("revenue", "")),
                "title": lead.get("title", ""),
                "location": lead.get("location", "")
            })
            ids.append(lead.get("lead_id", lead.get("email", "")))

        self.vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)

    def search_lead(self, lead_identifier: str, k: int = 1) -> List[Dict]:
        """Search for lead enrichment data.

        Args:
            lead_identifier: Email or lead_id to search for
            k: Number of results to return

        Returns:
            List of dicts with enrichment data and metadata
        """
        results = self.vectorstore.similarity_search(
            query=lead_identifier,
            k=k,
            filter={"email": lead_identifier}
        )

        if not results:
            # Fallback to semantic search if no exact match
            results = self.vectorstore.similarity_search(
                query=lead_identifier,
                k=k
            )

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in results
        ]
