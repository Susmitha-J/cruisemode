from __future__ import annotations

"""
ScanAnalysisAgent — analyzes scan reports and produces unified findings summary.

Reads clean code, OWASP, SonarQube, and OSS scan reports, then classifies
each finding as auto-patchable or requiring human review.
"""

import json
from typing import Any

from src.agents.base import BaseAgent


class ScanAnalysisAgent(BaseAgent):
    """Analyze scan reports and produce unified findings summary."""

    def __init__(self):
        super().__init__(
            name="scan_analysis",
            description="Analyzes scan reports into unified findings summary",
        )

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        self.log("Analyzing scan reports...")

        report_files = {
            "clean_code": "inputs/clean_code_report.json",
            "owasp": "inputs/owasp_scan_report.json",
            "sonarqube": "inputs/sonarqube_report.json",
            "oss": "inputs/oss_scan_report.json",
        }

        all_findings = []
        reports_loaded = {}

        for report_type, filepath in report_files.items():
            try:
                with open(filepath, "r") as f:
                    report = json.load(f)
                reports_loaded[report_type] = report
                findings = report.get("findings", [])
                for finding in findings:
                    finding["source_report"] = report_type
                all_findings.extend(findings)
                self.log(f"Loaded {len(findings)} findings from {report_type}")
            except FileNotFoundError:
                self.log(f"Report not found: {filepath}", level="warning")
            except json.JSONDecodeError:
                self.log(f"Invalid JSON in: {filepath}", level="error")

        # Classify findings
        auto_patchable = []
        requires_review = []
        oss_critical = []

        for finding in all_findings:
            source = finding.get("source_report", "")
            severity = finding.get("severity", "").upper()

            if source == "oss":
                # OSS findings are never auto-patched
                if severity in ("HIGH", "CRITICAL"):
                    oss_critical.append(finding)
                requires_review.append(finding)
            elif severity in ("CRITICAL",):
                requires_review.append(finding)
            else:
                auto_patchable.append(finding)

        # Build severity breakdown
        by_severity = {}
        for finding in all_findings:
            sev = finding.get("severity", "UNKNOWN").upper()
            by_severity[sev] = by_severity.get(sev, 0) + 1

        # Build category breakdown
        by_category = {}
        for finding in all_findings:
            cat = finding.get("source_report", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1

        state["scan_analysis"] = {
            "total_findings": len(all_findings),
            "by_severity": by_severity,
            "by_category": by_category,
            "auto_patchable": auto_patchable,
            "requires_review": requires_review,
            "oss_critical": oss_critical,
            "all_findings": all_findings,
        }

        # Generate AI-powered analysis summary using Gemini
        from src.tools.gemini_client import GeminiClient
        gemini = GeminiClient()
        if gemini.is_enabled and all_findings:
            findings_text = "\n".join(
                f"- [{f.get('severity')}] {f.get('type', f.get('category', 'UNKNOWN'))}: "
                f"{f.get('message', 'N/A')} (file: {f.get('file', 'N/A')}, line: {f.get('line', '?')})"
                for f in all_findings[:20]
            )
            prompt = (
                f"You are a security analyst. Summarize these {len(all_findings)} code scan findings "
                f"in 2-3 sentences. Focus on the most critical issues and actionable recommendations.\n\n"
                f"Findings:\n{findings_text}"
            )
            system_instruction = (
                "Respond in 2-3 concise sentences only. No markdown, no bullet points. "
                "Focus on severity, affected files, and recommended actions."
            )
            try:
                summary = gemini.generate_text(prompt, system_instruction=system_instruction)
                state["scan_analysis"]["ai_summary"] = summary
                self.log(f"🧠 Gemini AI analysis summary generated.")
            except Exception as e:
                self.log(f"⚠️ Gemini analysis summary failed: {e}", level="warning")

        self.log(
            f"Analysis complete: {len(all_findings)} findings, "
            f"{len(auto_patchable)} auto-patchable, "
            f"{len(oss_critical)} critical OSS"
        )
        return state
