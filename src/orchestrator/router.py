from __future__ import annotations

"""
Router — routes workflow decisions based on agent output.

Determines which agent to run next based on the current state.
For v0.1, routing is linear. Future versions will support conditional routing,
e.g., skipping test generation if patches fail, or branching based on OSS severity.

# TODO: Integrate with LangGraph conditional edges
"""

from typing import Any


class WorkflowRouter:
    """
    Routes workflow execution based on agent results.

    For v0.1, implements a simple pass-through. Future enhancements:
    - Skip test generation if sandbox patching fails
    - Block PR report if critical OSS issues are unresolved
    - Route to human-in-the-loop for OSS approval
    """

    def should_continue(self, state: dict[str, Any], next_agent: str) -> bool:
        """
        Determine if the workflow should proceed to the next agent.

        Args:
            state: Current workflow state.
            next_agent: Name of the next agent to run.

        Returns:
            True if the next agent should run, False to skip.
        """
        # Check for fatal errors in previous stages
        for key in state:
            if key.endswith("_error"):
                # For now, continue even on errors — agents handle gracefully
                pass

        return True

    def get_recommendation_override(self, state: dict[str, Any]) -> str | None:
        """
        Check if any condition should override the final recommendation.

        Returns:
            Override recommendation string, or None.
        """
        # If any critical error occurred, force BLOCKED
        errors = [k for k in state if k.endswith("_error")]
        if errors:
            return "BLOCKED"

        return None
