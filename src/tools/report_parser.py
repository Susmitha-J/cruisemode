from __future__ import annotations

"""
Report parser for CruiseMode scan reports.

Reads and normalizes scan reports from different tools into a unified format.
"""

import json
from typing import Any


class ReportParser:
    """Parse and normalize scan reports from various tools."""

    SUPPORTED_TYPES = ["clean_code", "owasp", "sonarqube", "oss_dependency"]

    @staticmethod
    def parse(filepath: str) -> dict[str, Any]:
        """
        Parse a scan report JSON file.

        Returns:
            Parsed report dict with normalized structure.
        """
        with open(filepath, "r") as f:
            report = json.load(f)

        return {
            "type": report.get("report_type", "unknown"),
            "tool": report.get("tool", "unknown"),
            "timestamp": report.get("timestamp", ""),
            "target": report.get("target", ""),
            "findings": report.get("findings", []),
            "summary": report.get("summary", {}),
        }

    @staticmethod
    def get_findings_by_severity(report: dict, severity: str) -> list[dict]:
        """Filter findings by severity level."""
        return [
            f for f in report.get("findings", [])
            if f.get("severity", "").upper() == severity.upper()
        ]

    @staticmethod
    def get_auto_patchable(findings: list[dict]) -> list[dict]:
        """Return findings that are safe for auto-patching."""
        non_oss = [f for f in findings if f.get("category") != "oss_dependency"]
        return [f for f in non_oss if f.get("severity", "").upper() not in ("CRITICAL",)]
