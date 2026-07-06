from __future__ import annotations

"""
AcceptanceCriteriaAgent — parses acceptance criteria into structured checklist.

Reads the acceptance_criteria.md file and produces a machine-readable list of
requirements that downstream agents use for test generation and report coverage.
"""

import re
from typing import Any

from src.agents.base import BaseAgent


class AcceptanceCriteriaAgent(BaseAgent):
    """Parse acceptance criteria markdown into structured requirements."""

    def __init__(self):
        super().__init__(
            name="acceptance_criteria",
            description="Parses acceptance criteria into structured checklist",
        )

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        self.log("Parsing acceptance criteria...")

        ac_file = state.get("inputs", {}).get("acceptance_criteria_file", "inputs/acceptance_criteria.md")

        try:
            with open(ac_file, "r") as f:
                content = f.read()
        except FileNotFoundError:
            self.log(f"Acceptance criteria file not found: {ac_file}", level="error")
            state["acceptance_criteria"] = []
            return state

        criteria = self._parse_criteria(content)
        state["acceptance_criteria"] = criteria
        self.log(f"Parsed {len(criteria)} acceptance criteria.")
        return state

    def _parse_criteria(self, content: str) -> list[dict]:
        """Parse markdown acceptance criteria into structured list."""
        criteria = []
        current_id = None
        current_desc = None
        current_items = []

        for line in content.strip().split("\n"):
            line = line.strip()

            # Match section headers like "## AC-001: Refund Amount Validation" or "## AC-1: ..."
            # OR match list items like "- AC-1: Refund amount must be positive." or "- AC-001: ..."
            header_match = re.match(r"^(?:##|-)\s+(AC-\d+):\s+(.+)$", line)
            if header_match:
                # Save previous criteria if exists
                if current_id:
                    criteria.append(self._build_criterion(current_id, current_desc, current_items))

                current_id = header_match.group(1)
                current_desc = header_match.group(2)
                current_items = []
            elif line.startswith("- ") and current_id:
                # If we match a list item, but it doesn't match an AC-X identifier, treat it as a sub-item
                current_items.append(line[2:])

        # Save last criteria
        if current_id:
            criteria.append(self._build_criterion(current_id, current_desc, current_items))

        return criteria

    def _build_criterion(self, ac_id: str, description: str, items: list[str]) -> dict:
        """Build a structured criterion dict."""
        category = self._classify_category(description, items)
        return {
            "id": ac_id,
            "description": description,
            "items": items,
            "category": category,
            "testable": True,
            "verification_method": self._get_verification_method(category),
        }

    def _classify_category(self, description: str, items: list[str]) -> str:
        """Classify the category of an acceptance criterion."""
        text = (description + " ".join(items)).lower()
        if "log" in text or "pii" in text or "expose" in text:
            return "security"
        elif "test" in text:
            return "testing"
        elif "http" in text or "return" in text or "status" in text:
            return "validation"
        return "validation"

    def _get_verification_method(self, category: str) -> str:
        """Map category to verification method."""
        return {
            "validation": "api_test",
            "security": "log_audit",
            "testing": "unit_test",
            "logging": "log_audit",
        }.get(category, "code_review")
