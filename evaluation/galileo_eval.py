import os
from typing import Dict, Any, Optional
import promptquality as pq
from dotenv import load_dotenv

load_dotenv()


class GalileoEvaluator:
    """Galileo evaluation wrapper for SDR outreach workflow."""

    def __init__(self, project_name: str = None):
        self.project_name = project_name or os.getenv(
            "GALILEO_PROJECT_NAME",
            "sdr-outreach-assistant"
        )
        self._logged_in = False

    def login(self):
        """Authenticate with Galileo."""
        api_key = os.getenv("GALILEO_API_KEY")
        if not api_key:
            raise ValueError("GALILEO_API_KEY not set in environment")

        pq.login(api_key)
        self._logged_in = True

    def run_workflow(
        self,
        workflow_func,
        input_data: Dict,
        experiment_name: Optional[str] = None
    ) -> Dict:
        """Run workflow with Galileo logging.

        Args:
            workflow_func: The graph execution function
            input_data: Input state for the workflow
            experiment_name: Optional experiment name for tracking

        Returns:
            Workflow output with Galileo tracking
        """
        if not self._logged_in:
            self.login()

        # Set experiment if provided
        if experiment_name:
            pq.set_experiment(experiment_name)

        # Run workflow with Galileo logging
        with pq.project(self.project_name):
            # Log input
            pq.log_input({
                "lead_email": input_data.get("lead_email"),
                "lead_id": input_data.get("lead_id"),
            })

            # Execute workflow
            result = workflow_func(input_data)

            # Log output
            pq.log_output({
                "email_draft": result.get("email_draft"),
                "linkedin_draft": result.get("linkedin_draft"),
                "call_script": result.get("call_script"),
                "status": result.get("status"),
            })

            # Log custom metrics
            self._log_metrics(input_data, result)

            return result

    def _log_metrics(self, input_data: Dict, result: Dict):
        """Log custom metrics to Galileo."""

        # Personalization score (simple heuristic)
        personalization_score = self._calculate_personalization_score(
            result.get("email_draft", "")
        )
        pq.log_metric("personalization_score", personalization_score)

        # Research depth (did we do web research?)
        research_depth = 1 if result.get("research_results") else 0
        pq.log_metric("research_depth", research_depth)

        # Draft completion (all three drafts generated?)
        drafts_completed = sum([
            bool(result.get("email_draft")),
            bool(result.get("linkedin_draft")),
            bool(result.get("call_script"))
        ])
        pq.log_metric("drafts_completed", drafts_completed)

    def _calculate_personalization_score(self, text: str) -> float:
        """Calculate personalization score for draft text.

        Simple heuristic based on:
        - Length (longer = more personalized)
        - Presence of specific terms (company, industry, etc.)

        Returns:
            Score between 0 and 1
        """
        if not text:
            return 0.0

        score = 0.0

        # Length component (up to 0.4)
        length_score = min(len(text) / 500, 0.4)
        score += length_score

        # Personalization keywords (up to 0.6)
        keywords = [
            "company", "industry", "team", "role", "recently",
            "noticed", "saw", "read", "specific", "challenge"
        ]

        text_lower = text.lower()
        keyword_matches = sum(1 for kw in keywords if kw in text_lower)
        keyword_score = min(keyword_matches / len(keywords), 0.6)
        score += keyword_score

        return round(score, 2)


class ExperimentRunner:
    """Run experiments to test different prompts and strategies."""

    def __init__(self, evaluator: GalileoEvaluator):
        self.evaluator = evaluator

    def run_experiment(
        self,
        experiment_name: str,
        workflow_func,
        test_leads: list[Dict],
        variants: Dict[str, Any]
    ):
        """Run A/B test experiment.

        Args:
            experiment_name: Name for the experiment
            workflow_func: Workflow function to test
            test_leads: List of test lead data
            variants: Dict of variant configurations to test
        """
        self.evaluator.login()

        results = {}

        for variant_name, variant_config in variants.items():
            print(f"\nRunning variant: {variant_name}")

            variant_results = []

            for lead in test_leads:
                # Apply variant config (e.g., different prompts)
                # This would require parameterizing the workflow
                result = self.evaluator.run_workflow(
                    workflow_func,
                    lead,
                    experiment_name=f"{experiment_name}_{variant_name}"
                )

                variant_results.append(result)

            results[variant_name] = variant_results

        print(f"\nExperiment {experiment_name} completed. View results in Galileo dashboard.")
        return results
