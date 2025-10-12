"""Galileo evaluation wrapper for SDR outreach workflow."""
import os
from typing import Dict, Optional
from datetime import datetime
from galileo import galileo_context
from galileo.handlers.langchain import GalileoAsyncCallback
from langchain_core.runnables import RunnableConfig
from dotenv import load_dotenv
from evaluation.metrics import evaluate_workflow_output

load_dotenv()


class GalileoEvaluator:
    """Galileo evaluation wrapper for SDR outreach workflow.

    Each workflow run creates an isolated session in Galileo Console.
    """

    def __init__(self, project_name: str = None):
        """Initialize Galileo evaluator.

        Args:
            project_name: Galileo project name (defaults to env var or 'sdr-outreach-assistant')
        """
        self.project_name = project_name or os.getenv(
            "GALILEO_PROJECT",
            os.getenv("GALILEO_PROJECT_NAME", "sdr-outreach-assistant")
        )

    def run_workflow(
        self,
        workflow_func,
        input_data: Dict,
        log_stream: Optional[str] = "production"
    ) -> Dict:
        """Run workflow with Galileo logging.

        Args:
            workflow_func: The graph execution function (should accept config param)
            input_data: Input state for the workflow
            log_stream: Log stream name (defaults to 'production')

        Returns:
            Workflow output with Galileo tracking
        """
        # Initialize Galileo context
        galileo_context.init(
            project=self.project_name,
            log_stream=log_stream
        )

        # Create unique session for this lead
        session_name = f"lead_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        external_id = input_data.get("lead_email", input_data.get("lead_id", "unknown"))

        galileo_context.start_session(
            name=session_name,
            external_id=external_id
        )

        # Create callback that auto-detects current session
        galileo_callback = GalileoAsyncCallback()

        try:
            # Create config with Galileo callback
            config: RunnableConfig = RunnableConfig(
                callbacks=[galileo_callback]
            )

            # Execute workflow
            result = workflow_func(input_data, config=config)

            # Calculate and log metrics
            metrics = evaluate_workflow_output(input_data, result)
            print(f"\n📊 Metrics for {external_id}:")
            for metric_name, metric_value in metrics.items():
                if isinstance(metric_value, float):
                    print(f"  - {metric_name}: {metric_value:.2f}")

            return result

        finally:
            # Always cleanup session
            galileo_context.flush()
            galileo_context.clear_session()
