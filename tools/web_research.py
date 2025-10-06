import os
from typing import Dict, Optional
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()


class WebResearchTool:
    """Performs web research on leads using Tavily and other sources."""

    def __init__(self):
        tavily_key = os.getenv("TAVILY_API_KEY")
        self.tavily = TavilyClient(api_key=tavily_key) if tavily_key else None

    def research_lead(
        self,
        email: str,
        company: str = "",
        title: str = ""
    ) -> Dict:
        """Research lead using web search.

        Args:
            email: Lead email
            company: Company name
            title: Lead's job title

        Returns:
            Dict with research results
        """
        if not self.tavily:
            return {
                "summary": "Web research not available - Tavily API key not configured",
                "sources": []
            }

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

            return {
                "summary": summary,
                "sources": sources,
                "query": query
            }

        except Exception as e:
            return {
                "summary": f"Research failed: {str(e)}",
                "sources": [],
                "error": str(e)
            }

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
