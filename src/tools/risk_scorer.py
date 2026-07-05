from __future__ import annotations

"""
Risk scorer for CruiseMode.

Scores and prioritizes scan findings based on severity, category, and
configurable risk rules.
"""

from typing import Any


class RiskScorer:
    """Score and prioritize scan findings."""

    SEVERITY_WEIGHTS = {
        "CRITICAL": 10,
        "HIGH": 7,
        "MEDIUM": 4,
        "LOW": 2,
        "INFO": 1,
    }

    CATEGORY_WEIGHTS = {
        "oss_dependency": 1.5,
        "pii_logging": 1.3,
        "owasp_validation": 1.2,
        "input_validation": 1.2,
        "clean_code": 1.0,
        "broad_exception": 1.0,
        "code_smell": 0.8,
        "code_style": 0.6,
        "maintainability": 0.6,
        "security_headers": 0.8,
    }

    @classmethod
    def score_finding(cls, finding: dict[str, Any]) -> float:
        """
        Calculate a risk score for a single finding.

        Score = severity_weight × category_weight
        """
        severity = finding.get("severity", "INFO").upper()
        category = finding.get("category", "unknown")

        sev_weight = cls.SEVERITY_WEIGHTS.get(severity, 1)
        cat_weight = cls.CATEGORY_WEIGHTS.get(category, 1.0)

        return round(sev_weight * cat_weight, 2)

    @classmethod
    def score_all(cls, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Score all findings and return them sorted by risk score (descending)."""
        scored = []
        for finding in findings:
            score = cls.score_finding(finding)
            scored.append({**finding, "risk_score": score})
        return sorted(scored, key=lambda x: x["risk_score"], reverse=True)

    @classmethod
    def total_risk_score(cls, findings: list[dict[str, Any]]) -> float:
        """Calculate the total risk score for a list of findings."""
        return sum(cls.score_finding(f) for f in findings)

    @classmethod
    def get_recommendation(cls, total_score: float, has_critical: bool) -> str:
        """Get build recommendation based on total risk score."""
        if has_critical or total_score >= 30:
            return "BLOCKED"
        elif total_score >= 15:
            return "REVIEW_NEEDED"
        return "READY_FOR_PR"
