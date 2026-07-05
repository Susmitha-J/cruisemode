from __future__ import annotations

"""
CruiseMode — Main entry point.

Runs the full multi-agent validation workflow with a single command:
    python -m src.main

Output files are written to the outputs/ directory:
    - outputs/validation_results.json
    - outputs/suggested_changes.md
    - outputs/pr_report.md
"""

import logging
import sys

from src.orchestrator.workflow import CruiseModeWorkflow


def setup_logging():
    """Configure logging for the CruiseMode workflow."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    """Run the CruiseMode workflow."""
    setup_logging()

    print()
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║        🚗  CruiseMode v0.1.0                        ║")
    print("  ║  Multi-Agent Pre-Jenkins Validation System           ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print()

    workflow = CruiseModeWorkflow()
    state = workflow.run()

    # Print final summary
    recommendation = state.get("pr_report", {}).get("recommendation", "UNKNOWN")
    print()
    print(f"  📋 Final Recommendation: {recommendation}")
    print()
    print("  📄 Output files:")
    for f in state.get("pr_report", {}).get("output_files", []):
        print(f"     → {f}")
    print()
    print("  🖥  To view the dashboard:")
    print("     streamlit run src/ui/dashboard.py")
    print()

    return state


if __name__ == "__main__":
    main()
