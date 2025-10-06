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
