import os
import json
from typing import Dict, Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()


class WebResearchInput(BaseModel):
    """Input schema for web research tool."""
    email: str = Field(description="Lead email address")
    company: str = Field(default="", description="Company name")
    title: str = Field(default="", description="Lead's job title")


class WebResearchTool(BaseTool):
    """Performs web research on leads using Tavily and other sources."""

    name: str = "web_research"
    description: str = "Research a lead using web search to find company and role context. Returns research summary and sources."
    args_schema: Type[BaseModel] = WebResearchInput

    tavily: Optional[TavilyClient] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        tavily_key = os.getenv("TAVILY_API_KEY")
        self.tavily = TavilyClient(api_key=tavily_key) if tavily_key else None

    def _run(
        self,
        email: str,
        company: str = "",
        title: str = ""
    ) -> str:
        """Research lead using web search.

        Args:
            email: Lead email
            company: Company name
            title: Lead's job title

        Returns:
            JSON string with research results
        """
        if not self.tavily:
            result = {
                "summary": "Web research not available - Tavily API key not configured",
                "sources": []
            }
            return json.dumps(result)

        # Build search query
        query_parts = []
        if company:
            query_parts.append(company)
        if title:
            query_parts.append(title)

        query = " ".join(query_parts) if query_parts else email

        try:
            # Search for company and role context
            search_results = self.tavily.search(
                query=query,
                search_depth="basic",
                max_results=3
            )

            # Extract key information
            summary_parts = []
            sources = []

            for result in search_results.get("results", []):
                summary_parts.append(result.get("content", ""))
                sources.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", "")
                })

            summary = " ".join(summary_parts[:500])  # Limit length

            result = {
                "summary": summary,
                "sources": sources,
                "query": query
            }
            return json.dumps(result)

        except Exception as e:
            result = {
                "summary": f"Research failed: {str(e)}",
                "sources": [],
                "error": str(e)
            }
            return json.dumps(result)

    def search_linkedin_profile(self, name: str, company: str) -> Optional[str]:
        """Search for LinkedIn profile (placeholder for LinkedIn API integration).

        Args:
            name: Person's name
            company: Company name

        Returns:
            LinkedIn profile URL if found
        """
        # This would integrate with LinkedIn API or web scraping
        # For now, return placeholder
        return None

    def search_company_news(self, company: str) -> Dict:
        """Search for recent company news.

        Args:
            company: Company name

        Returns:
            Dict with news articles
        """
        if not self.tavily:
            return {"articles": []}

        try:
            search_results = self.tavily.search(
                query=f"{company} news",
                search_depth="basic",
                max_results=3,
                days=30  # Recent news only
            )

            articles = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")
                }
                for r in search_results.get("results", [])
            ]

            return {"articles": articles}

        except Exception as e:
            return {"articles": [], "error": str(e)}
