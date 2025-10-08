"""Galileo v2.0 evaluation wrapper for SDR outreach workflow."""
import os
from typing import Dict, Any, Optional
from datetime import datetime
from galileo import galileo_context
from galileo.handlers.langchain import GalileoAsyncCallback
from langchain_core.runnables import RunnableConfig
from dotenv import load_dotenv
from evaluation.metrics import evaluate_workflow_output

load_dotenv()


class GalileoEvaluator:
    """Galileo v2.0 evaluation wrapper for SDR outreach workflow.

    Uses LangGraph callback handler for automatic tracing of all workflow nodes.
    """

    def __init__(self, project_name: str = None, log_stream: str = None):
        """Initialize Galileo evaluator.

        Args:
            project_name: Galileo project name (defaults to env var or 'sdr-outreach-assistant')
            log_stream: Log stream name (defaults to 'production')
        """
        self.project_name = project_name or os.getenv(
            "GALILEO_PROJECT",
            os.getenv("GALILEO_PROJECT_NAME", "sdr-outreach-assistant")
        )
        self.log_stream = log_stream or "production"

    def run_workflow(
        self,
        workflow_func,
        input_data: Dict,
        experiment_name: Optional[str] = None
    ) -> Dict:
        """Run workflow with Galileo v2.0 logging.

        Args:
            workflow_func: The graph execution function (should accept config param)
            input_data: Input state for the workflow
            experiment_name: Optional experiment name for tracking (used as log_stream)

        Returns:
            Workflow output with Galileo tracking
        """
        # Reset and initialize Galileo context (ensures fresh session on every run)
        log_stream = experiment_name or self.log_stream

        # Force reload .env to get fresh API key (prevents Streamlit caching issues)
        load_dotenv(override=True)

        # Clear any existing session to ensure clean slate
        try:
            galileo_context.clear_session()
            print("🔄 Cleared previous Galileo session")
        except Exception as e:
            print(f"ℹ️  No previous session to clear: {e}")

        # Initialize Galileo context (reinit is safe - SDK handles if already initialized)
        galileo_context.init(
            project=self.project_name,
            log_stream=log_stream
        )
        print(f"✓ Initialized Galileo context - Project: {self.project_name}, Log Stream: {log_stream}")

        # Start NEW session with unique identifier (timestamp ensures uniqueness)
        session_name = f"{experiment_name or 'sdr_outreach'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        external_id = input_data.get("lead_id", input_data.get("lead_email", "unknown"))

        galileo_context.start_session(
            name=session_name,
            external_id=external_id
        )
        print(f"🆕 Started NEW Galileo session: '{session_name}' (External ID: {external_id})")

        # Create Galileo callback handler for LangGraph
        galileo_callback = GalileoAsyncCallback()

        try:
            # Create RunnableConfig with Galileo callback
            # This follows LangGraph best practices for callback handling
            config: RunnableConfig = RunnableConfig(
                callbacks=[galileo_callback]
            )

            # Execute workflow with callback (auto-traces all LangGraph nodes)
            result = workflow_func(
                input_data,
                config=config
            )

            # Calculate custom metrics using metrics.py functions
            metrics = evaluate_workflow_output(input_data, result)

            # Log custom metrics summary
            print(f"\n📊 Workflow Metrics:")
            for metric_name, metric_value in metrics.items():
                print(f"  - {metric_name}: {metric_value:.2f}" if isinstance(metric_value, float) else f"  - {metric_name}: {metric_value}")

            # Clear session and flush logs to Galileo
            galileo_context.clear_session()
            print(f"✅ Cleared Galileo session: '{session_name}'")
            galileo_context.flush()
            print("📤 Flushed traces to Galileo")

            return result

        except Exception as e:
            print(f"❌ Error during workflow execution: {e}")
            # Clear session even on error
            try:
                galileo_context.clear_session()
                print(f"🧹 Cleared session after error")
            except:
                pass
            galileo_context.flush()
            raise


class ExperimentRunner:
    """Run A/B test experiments with Galileo v2.0.

    Each variant uses a different log_stream for easy comparison in Galileo Console.
    """

    def __init__(self, evaluator: GalileoEvaluator):
        """Initialize experiment runner.

        Args:
            evaluator: GalileoEvaluator instance to use for logging
        """
        self.evaluator = evaluator

    def run_experiment(
        self,
        experiment_name: str,
        workflow_func,
        test_leads: list[Dict],
        variants: Dict[str, Any]
    ) -> Dict:
        """Run A/B test experiment across multiple variants.

        Args:
            experiment_name: Name for the experiment
            workflow_func: Workflow function to test
            test_leads: List of test lead data
            variants: Dict of variant configurations to test

        Returns:
            Dict mapping variant names to their results
        """
        results = {}

        print(f"\n🧪 Starting experiment: {experiment_name}")
        print(f"   Variants: {list(variants.keys())}")
        print(f"   Test leads: {len(test_leads)}")
        print(f"   Project: {self.evaluator.project_name}")

        for variant_name, variant_config in variants.items():
            print(f"\n{'='*60}")
            print(f"Running variant: {variant_name}")
            print(f"{'='*60}")

            variant_results = []
            log_stream_name = f"{experiment_name}_{variant_name}"

            for i, lead in enumerate(test_leads, 1):
                print(f"\n  [{i}/{len(test_leads)}] Processing lead: {lead.get('lead_email', lead.get('lead_id', 'unknown'))}")

                try:
                    # Apply variant config if needed
                    # (In a real implementation, variant_config would modify prompts/parameters)
                    result = self.evaluator.run_workflow(
                        workflow_func,
                        lead,
                        experiment_name=log_stream_name
                    )
                    variant_results.append(result)

                except Exception as e:
                    print(f"  ❌ Error processing lead: {e}")
                    variant_results.append({"error": str(e)})

            results[variant_name] = variant_results
            print(f"\n✓ Variant '{variant_name}' completed: {len(variant_results)} runs")

        print(f"\n{'='*60}")
        print(f"✓ Experiment '{experiment_name}' completed!")
        print(f"{'='*60}")
        print(f"\n📊 View results in Galileo Console:")
        print(f"   https://console.galileo.ai")
        print(f"   Project: {self.evaluator.project_name}")
        print(f"   Log streams:")
        for variant_name in variants.keys():
            print(f"     - {experiment_name}_{variant_name}")

        return results
