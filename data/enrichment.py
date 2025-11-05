import json
import csv
from typing import List, Dict, Union
from pathlib import Path


class EnrichmentLoader:
    """Load lead enrichment data from various sources."""

    @staticmethod
    def load_from_json(file_path: Union[str, Path]) -> List[Dict]:
        """Load enrichment data from JSON file.

        Expected format:
        [
            {
                "lead_id": "123",
                "email": "john@acme.com",
                "company": "Acme Corp",
                "industry": "Software",
                "revenue": "10M-50M",
                "title": "VP Engineering",
                "location": "San Francisco, CA",
                "enrichment_text": "Additional context..."
            }
        ]
        """
        with open(file_path, 'r') as f:
            return json.load(f)

    @staticmethod
    def load_from_csv(file_path: Union[str, Path]) -> List[Dict]:
        """Load enrichment data from CSV file.

        Expected columns: lead_id, email, company, industry, revenue,
                         title, location, enrichment_text
        """
        leads = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                leads.append(dict(row))
        return leads

    @staticmethod
    def load_from_apollo_export(file_path: Union[str, Path]) -> List[Dict]:
        """Load data from Apollo.io CSV export.

        Maps Apollo fields to standardized format.
        """
        leads = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                lead = {
                    "lead_id": row.get("Contact ID", row.get("Email", "")),
                    "email": row.get("Email", ""),
                    "company": row.get("Company", ""),
                    "industry": row.get("Industry", ""),
                    "revenue": row.get("Revenue Range", ""),
                    "title": row.get("Title", ""),
                    "location": row.get("City", "") + ", " + row.get("State", ""),
                    "enrichment_text": f"Company Size: {row.get('Company Size', '')}. "
                                      f"Technologies: {row.get('Technologies', '')}."
                }
                leads.append(lead)
        return leads

    @staticmethod
    def load_from_leads_csv(file_path: Union[str, Path]) -> List[Dict]:
        """Load data from leads CSV with specific column mapping.

        Maps columns from the leads CSV format:
        - Lead ID, Name, Email, Company, Industry, Title, Location, Company Info, LinkedIn
        
        Args:
            file_path: Path to the leads CSV file
            
        Returns:
            List of standardized lead dictionaries
        """
        leads = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip empty rows
                if not row.get("Email", "").strip():
                    continue
                
                # Build enrichment text from available fields
                enrichment_parts = []
                
                # Add contact name
                name = row.get("Name", "").strip()
                if name:
                    enrichment_parts.append(f"Contact: {name}")
                
                # Add company information (main enrichment content)
                company_info = row.get("Company Info", "").strip()
                if company_info:
                    enrichment_parts.append(f"Company Details: {company_info}")
                
                # Add LinkedIn profile
                linkedin = row.get("LinkedIn", "").strip()
                if linkedin:
                    enrichment_parts.append(f"LinkedIn: {linkedin}")
                
                enrichment_text = "\n\n".join(enrichment_parts)
                
                lead = {
                    "lead_id": row.get("Lead ID", "").strip(),
                    "email": row.get("Email", "").strip(),
                    "company": row.get("Company", "").strip(),
                    "industry": row.get("Industry", "").strip(),
                    "revenue": "",  # Not provided in this CSV format
                    "title": row.get("Title", "").strip(),
                    "location": row.get("Location", "").strip(),
                    "enrichment_text": enrichment_text
                }
                
                leads.append(lead)
        
        return leads
