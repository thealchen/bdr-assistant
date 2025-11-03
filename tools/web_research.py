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

    def research_lead_enhanced(
        self,
        email: str,
        company: str = "",
        title: str = "",
        industry: str = ""
    ) -> Dict:
        """Run 3 targeted searches for better personalization signals.

        Args:
            email: Lead email
            company: Company name
            title: Lead's job title
            industry: Company industry

        Returns:
            Dict with recent_events, pain_signals, and combined summary
        """
        if not self.tavily:
            return {
                "recent_events": [],
                "pain_signals": [],
                "summary": "Web research not available - Tavily API key not configured",
                "sources": []
            }

        results = {
            "recent_events": [],
            "pain_signals": [],
            "sources": []
        }

        # Search 1: Recent company news/events
        try:
            news_query = f"{company} funding OR launch OR hiring OR acquisition recent"
            news_results = self.tavily.search(
                query=news_query,
                search_depth="basic",
                max_results=2,
                days=60
            )
            for r in news_results.get("results", []):
                content = r.get("content", "")
                if content:
                    results["recent_events"].append(content)
                    results["sources"].append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "category": "news"
                    })
        except Exception as e:
            print(f"News search failed: {e}")

        # Search 2: Industry pain points/challenges
        try:
            pain_query = f"{company} {industry} challenges OR problems OR issues 2025"
            pain_results = self.tavily.search(
                query=pain_query,
                search_depth="basic",
                max_results=2
            )
            for r in pain_results.get("results", []):
                content = r.get("content", "")
                if content:
                    results["pain_signals"].append(content)
                    results["sources"].append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "category": "pain_points"
                    })
        except Exception as e:
            print(f"Pain points search failed: {e}")

        # Combine into summary
        all_content = results["recent_events"] + results["pain_signals"]
        results["summary"] = " ".join(all_content)[:800]  # Limit length

        return results

    def _run(
        self,
        email: str,
        company: str = "",
        title: str = ""
    ) -> str:
        """Research lead using enhanced multi-query search.

        Args:
            email: Lead email
            company: Company name
            title: Lead's job title

        Returns:
            JSON string with research results
        """
        # Use enhanced research
        enriched = self.research_lead_enhanced(email, company, title)
        return json.dumps(enriched)

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
