from __future__ import annotations

"""
CruiseMode Workflow — main orchestrator that runs all agents in sequence.

Execution order:
1. Load acceptance criteria
2. Analyze scan reports
3. Create sandbox and apply safe patches
4. Generate OSS advisory (no auto-patching)
5. Generate unit and API tests
6. Run local validation (pytest)
7. Generate PR report and output files
"""

import logging
import os
import time
from typing import Any

from src.agents.acceptance_criteria import AcceptanceCriteriaAgent
from src.agents.scan_analysis import ScanAnalysisAgent
from src.agents.sandbox_patch import SandboxPatchAgent
from src.agents.oss_advisor import OSSAdvisorAgent
from src.agents.test_generation import TestGenerationAgent
from src.agents.validation import ValidationAgent
from src.agents.pr_report import PRReportAgent

logger = logging.getLogger("cruisemode.workflow")


class CruiseModeWorkflow:
    """
    Main orchestrator for the CruiseMode multi-agent validation system.

    Runs all agents in sequence, passing a shared workflow state dictionary
    through each agent. The state accumulates results from each stage.
    """

    def __init__(self):
        self.agents = [
            AcceptanceCriteriaAgent(),
            ScanAnalysisAgent(),
            SandboxPatchAgent(),
            OSSAdvisorAgent(),
            TestGenerationAgent(),
            ValidationAgent(),
            PRReportAgent(),
        ]

    def run(self) -> dict[str, Any]:
        """
        Execute the full CruiseMode workflow.

        Returns:
            Final workflow state with all agent results.
        """
        logger.info("=" * 60)
        logger.info("🚀 CruiseMode Workflow Starting")
        logger.info("=" * 60)

        # Initialize shared workflow state
        state: dict[str, Any] = {
            "feature_name": "Refund API",
            "inputs": {
                "acceptance_criteria_file": "inputs/acceptance_criteria.md",
            },
            "sample_app_dir": "sample_app",
            "sandbox_dir": ".sandbox",
            "generated_tests_dir": "generated_tests",
            "output_dir": "outputs",
            "started_at": time.time(),
        }

        # Ensure output directories exist
        os.makedirs(state["output_dir"], exist_ok=True)
        os.makedirs(state["generated_tests_dir"], exist_ok=True)

        # Run each agent in sequence
        for agent in self.agents:
            logger.info("-" * 40)
            logger.info(f"▶ Running agent: {agent.name}")
            try:
                state = agent.run(state)
                logger.info(f"✅ Agent '{agent.name}' completed successfully.")
            except Exception as e:
                logger.error(f"❌ Agent '{agent.name}' failed: {e}")
                state[f"{agent.name}_error"] = str(e)

        state["completed_at"] = time.time()
        state["duration_seconds"] = round(state["completed_at"] - state["started_at"], 2)

        logger.info("=" * 60)
        recommendation = state.get("pr_report", {}).get("recommendation", "UNKNOWN")
        logger.info(f"🏁 CruiseMode Workflow Complete — Recommendation: {recommendation}")
        logger.info(f"⏱  Duration: {state['duration_seconds']}s")
        logger.info("=" * 60)

        # Print output file locations
        output_files = state.get("pr_report", {}).get("output_files", [])
        if output_files:
            logger.info("📄 Output files:")
            for f in output_files:
                logger.info(f"   → {f}")

        return state
