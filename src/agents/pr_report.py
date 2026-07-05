from __future__ import annotations

"""
PRReportAgent — generates the final pull request report in markdown.

Produces:
- outputs/pr_report.md (full PR report)
- outputs/suggested_changes.md (diff summary of changes)
- outputs/validation_results.json (structured test results)
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Any

from src.agents.base import BaseAgent


class PRReportAgent(BaseAgent):
    """Generate PR report, suggested changes, and validation results."""

    def __init__(self):
        super().__init__(
            name="pr_report",
            description="Generates PR report and suggested changes summary",
        )

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        self.log("Generating PR report...")

        output_dir = state.get("output_dir", "outputs")
        os.makedirs(output_dir, exist_ok=True)

        # Determine final recommendation
        recommendation = self._determine_recommendation(state)

        # Generate all output files
        pr_report_path = os.path.join(output_dir, "pr_report.md")
        self._write_pr_report(pr_report_path, state, recommendation)

        suggested_changes_path = os.path.join(output_dir, "suggested_changes.md")
        self._write_suggested_changes(suggested_changes_path, state)

        # Write outputs/jenkins_handoff.json
        jenkins_handoff_path = os.path.join(output_dir, "jenkins_handoff.json")
        self._write_jenkins_handoff(jenkins_handoff_path, state, recommendation)

        # Upload artifacts to GCS
        from src.cloud.gcs_uploader import GCSUploader
        uploader = GCSUploader()
        artifacts_to_upload = [
            pr_report_path,
            suggested_changes_path,
            jenkins_handoff_path
        ]
        gcs_urls = uploader.upload_artifacts(artifacts_to_upload, state.get("feature_name", "Refund API"))
        state["cloud_gcs"] = {
            "uploaded": True,
            "bucket": uploader.bucket_name or "mock-bucket",
            "artifacts": gcs_urls
        }

        # Load validation run to BigQuery
        from src.cloud.bigquery_loader import BigQueryLoader
        bq_loader = BigQueryLoader()
        
        scan_analysis = state.get("scan_analysis", {})
        validation = state.get("validation", {})
        oss = state.get("oss_advisory", {})
        sandbox = state.get("sandbox", {})

        branch_name = "feature/boilerplate"
        try:
            import subprocess
            res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                branch_name = res.stdout.strip()
        except Exception:
            pass

        run_id = f"run_{int(time.time())}"
        jenkins_rec = self._get_jenkins_recommendation_text(recommendation)

        bq_data = {
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "feature_name": state.get("feature_name", "Refund API"),
            "branch_name": branch_name,
            "final_status": recommendation,
            "total_findings": scan_analysis.get("total_findings", 0),
            "auto_patchable_findings": len(scan_analysis.get("auto_patchable", [])),
            "review_required_findings": len(scan_analysis.get("requires_review", [])),
            "patches_applied": sandbox.get("total_patches", 0),
            "tests_passed": validation.get("passed", 0),
            "tests_failed": validation.get("failed", 0),
            "tests_errors": validation.get("errors", 0),
            "oss_alert_count": len(oss.get("findings", [])),
            "oss_alert_required": oss.get("oss_alert_required", False),
            "oss_blocking": False,
            "duration_seconds": round(time.time() - state.get("started_at", time.time()), 2),
            "report_generation_mode": "MOCK" if not os.getenv("GOOGLE_API_KEY") else "REAL",
            "jenkins_recommendation": jenkins_rec
        }
        
        bq_loader.load_validation_run(bq_data)
        state["cloud_bq"] = {
            "loaded": True,
            "table": f"{bq_loader.project_id or 'mock-project'}.{bq_loader.dataset}.validation_runs",
            "run_id": run_id,
            "fields": bq_data
        }

        # Write outputs/validation_results.json
        validation_results_path = os.path.join(output_dir, "validation_results.json")
        self._write_validation_results(validation_results_path, state, recommendation)

        # Upload validation_results.json and oss_alerts.json to GCS as well
        oss_alerts_path = os.path.join(output_dir, "oss_alerts.json")
        gcs_urls_final = uploader.upload_artifacts([validation_results_path, oss_alerts_path], state.get("feature_name", "Refund API"))
        state["cloud_gcs"]["artifacts"].update(gcs_urls_final)

        # Re-write outputs/validation_results.json with GCS URLs updated
        self._write_validation_results(validation_results_path, state, recommendation)

        state["pr_report"] = {
            "recommendation": recommendation,
            "output_files": [
                pr_report_path,
                suggested_changes_path,
                jenkins_handoff_path,
                validation_results_path,
                oss_alerts_path
            ],
        }

        self.log(f"PR report generated. Recommendation: {recommendation}")
        return state

    def _determine_recommendation(self, state: dict) -> str:
        """Determine final recommendation based on validation, patches, and unresolved findings.

        READY_FOR_PR:
          - Tests pass
          - No unresolved HIGH/CRITICAL code/security findings

        REVIEW_NEEDED:
          - Tests pass
          - Safe patches were applied
          - Security/Sonar review items remain
          - Human approval required before Jenkins

        BLOCKED:
          - Tests fail
          - Sandbox validation fails
          - Sensitive data leak remains unpatched
          - Critical code/security issue remains unresolved

        NOTE: OSS findings are advisory-only and do NOT impact this recommendation.
        """
        validation = state.get("validation", {})
        sandbox = state.get("sandbox", {})
        scan = state.get("scan_analysis", {})
        ac = state.get("acceptance_criteria", [])
        test_gen = state.get("test_generation", {})

        # Check tests execution
        tests_pass = validation.get("status") == "PASSED"
        tests_fail = validation.get("status") in ("FAILED", "ERROR") or (validation.get("return_code") is not None and validation.get("return_code") != 0)

        # Check patching execution
        patching_failed = "sandbox_patch_error" in state

        # Check acceptance criteria coverage
        testable_ac_count = sum(1 for c in ac if c.get("testable", True))
        tests_generated_count = test_gen.get("total_tests", 0)
        ac_coverage_insufficient = tests_generated_count < testable_ac_count if testable_ac_count > 0 else False

        # Identify patched vs unresolved findings
        patched_ids = set()
        for patch in sandbox.get("patches_applied", []):
            patched_ids.update(patch.get("finding_ids", []))

        all_findings = scan.get("all_findings", [])
        non_oss_findings = [f for f in all_findings if f.get("source_report") != "oss"]
        unresolved_non_oss = [f for f in non_oss_findings if f.get("id") not in patched_ids]

        # PII Leak unresolved
        unresolved_pii = [
            f for f in unresolved_non_oss
            if f.get("category") == "pii_logging" and f.get("severity", "").upper() in ("HIGH", "CRITICAL")
        ]

        # Critical OWASP/code security issue unresolved
        unresolved_critical_non_oss = [
            f for f in unresolved_non_oss
            if f.get("severity", "").upper() == "CRITICAL"
        ]

        # Unresolved high non-OSS findings
        unresolved_high_non_oss = [
            f for f in unresolved_non_oss
            if f.get("severity", "").upper() == "HIGH"
        ]

        # OSS Alerts
        oss_advisory = state.get("oss_advisory", {})
        oss_alert_required = oss_advisory.get("oss_alert_required", False)

        # Optional non-blocking clean-code or SonarQube review items (MEDIUM/LOW/INFO non-OSS findings)
        optional_non_blocking_exist = any(
            f.get("source_report") in ("clean_code", "sonarqube") and f.get("severity", "").upper() not in ("HIGH", "CRITICAL")
            for f in unresolved_non_oss
        )

        # --- BLOCKED ---
        if tests_fail:
            return "BLOCKED"
        if patching_failed:
            return "BLOCKED"
        if bool(unresolved_pii):
            return "BLOCKED"
        if bool(unresolved_critical_non_oss):
            return "BLOCKED"
        if ac_coverage_insufficient:
            return "BLOCKED"

        # --- REVIEW_NEEDED ---
        # A non-OSS high finding requires human review
        if bool(unresolved_high_non_oss):
            return "REVIEW_NEEDED"
        # Patch skipped because it is risky
        if sandbox.get("patches_skipped"):
            return "REVIEW_NEEDED"

        # --- READY_WITH_ALERTS ---
        if tests_pass and (oss_alert_required or optional_non_blocking_exist):
            return "READY_WITH_ALERTS"

        # --- READY_FOR_PR ---
        if tests_pass:
            return "READY_FOR_PR"

        return "BLOCKED"

    def _write_pr_report(self, filepath: str, state: dict, recommendation: str):
        """Generate the full PR report markdown."""
        ac = state.get("acceptance_criteria", [])
        scan = state.get("scan_analysis", {})
        sandbox = state.get("sandbox", {})
        oss = state.get("oss_advisory", {})
        tests = state.get("test_generation", {})
        validation = state.get("validation", {})
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Get Jenkins handoff recommendation text
        jenkins_rec = self._get_jenkins_recommendation_text(recommendation)

        report = f"""# CruiseMode PR Report

**Generated:** {timestamp}
**Feature:** Refund API Validation
**Recommendation:** `{recommendation}`

---

## 1. Feature Summary

Multi-agent pre-Jenkins validation for the Refund API feature. CruiseMode analyzed
acceptance criteria, scan reports, applied safe patches in a sandbox, generated tests,
and ran local validation.

---

## 2. Acceptance Criteria Coverage

| ID | Description | Category | Testable |
|----|-------------|----------|----------|
"""
        for criterion in ac:
            report += (
                f"| {criterion['id']} | {criterion['description']} "
                f"| {criterion['category']} | {'✅' if criterion['testable'] else '❌'} |\n"
            )

        report += f"""
---

## 3. Scan Summary

- **Total Findings:** {scan.get('total_findings', 0)}
- **By Severity:** {json.dumps(scan.get('by_severity', {}), indent=2)}
- **Auto-patchable:** {len(scan.get('auto_patchable', []))}
- **Requires Review:** {len(scan.get('requires_review', []))}
- **Critical OSS:** {len(scan.get('oss_critical', []))}

---

## 4. Safe Patches Applied

| Patch ID | Type | Description |
|----------|------|-------------|
"""
        for patch in sandbox.get("patches_applied", []):
            report += f"| {patch['id']} | {patch['type']} | {patch['description']} |\n"

        report += f"""
**Files Modified:** {len(sandbox.get('files_modified', []))}

---

## 5. OSS Dependency Alerts

OSS dependency findings are surfaced as alerts, not auto-patched or treated as local validation blockers. Dependency upgrades require regression testing, compatibility review, license/security review, and downstream Jenkins/security pipeline validation.

"""
        findings = oss.get("findings", [])
        if findings:
            for alert in findings:
                emoji = "🔴" if alert["severity"] == "CRITICAL" else "🟡" if alert["severity"] == "HIGH" else "🟢"
                report += (
                    f"- {emoji} **{alert['package']}@{alert['current_version']}** — "
                    f"{alert['cve']} ({alert['severity']})\n"
                    f"  - Recommended Action: {alert['recommended_action']}\n"
                    f"  - Auto-Patch Applied: {'Yes' if alert['auto_patch_applied'] else 'No'}\n\n"
                )
        else:
            report += "No OSS dependency alerts.\n"

        report += f"""---

## 6. Generated Tests

- **Test files:** {len(tests.get('generated_files', []))}
- **Total tests:** {tests.get('total_tests', 0)}
- **Test types:** {', '.join(tests.get('test_types', []))}

---

## 7. Local Validation Results

- **Status:** {validation.get('status', 'NOT_RUN')}
- **Passed:** {validation.get('passed', 0)}/{validation.get('total_tests', 0)}
- **Failed:** {validation.get('failed', 0)}
- **Errors:** {validation.get('errors', 0)}
- **Duration:** {validation.get('duration_seconds', 0)}s

---

## 8. Remaining Review Items

"""
        # Compute unresolved findings for the report
        patched_ids = set()
        for patch in sandbox.get("patches_applied", []):
            patched_ids.update(patch.get("finding_ids", []))
        all_findings = scan.get("all_findings", [])
        non_oss_findings = [f for f in all_findings if f.get("source_report") != "oss"]
        unresolved = [f for f in non_oss_findings if f.get("id") not in patched_ids]

        if validation.get("failed", 0) > 0:
            report += f"- 🔴 {validation['failed']} test(s) failed — review test output\n"
        if unresolved:
            report += f"- ⚠️ {len(unresolved)} unresolved code/security finding(s) remain:\n"
            for f in unresolved:
                report += f"  - `{f.get('id')}` ({f.get('severity')}) — {f.get('message', '')[:80]}\n"
        if sandbox.get("total_patches", 0) > 0:
            report += f"- 🔧 {sandbox['total_patches']} safe patch(es) applied — human review recommended before Jenkins\n"
        if oss.get("oss_alert_required", False):
            report += f"- ℹ️ OSS advisory alert(s) logged (non-blocking)\n"
        if not unresolved and validation.get("status") == "PASSED" and sandbox.get("total_patches", 0) == 0:
            report += "- ✅ No blocking items remaining\n"

        report += f"""
---

## 9. Jenkins Handoff Recommendation

**Handoff Recommendation:** {jenkins_rec}

---

## 10. Suggested PR Summary

"""
        if recommendation == "READY_WITH_ALERTS":
            report += (
                "> **Refund API Feature — Pre-Jenkins Validation Complete (Ready with Alerts)**\n>\n"
                "> CruiseMode local validation passed and safe sandbox patches were applied. Generated unit/API tests passed. "
                "A critical OSS dependency alert was detected and should be reviewed through the normal dependency and regression process. "
                "CruiseMode recommends triggering Jenkins with awareness of the OSS alert.\n"
            )
        else:
            report += (
                f"> **Refund API Feature — Pre-Jenkins Validation Complete ({recommendation})**\n>\n"
                f"> CruiseMode automated validation has completed. {len(sandbox.get('patches_applied', []))} safe patches "
                f"were applied (PII logging, clean code, code smells). {tests.get('total_tests', 0)} tests were generated "
                f"and {'all passed' if validation.get('status') == 'PASSED' else 'some require review'}.\n"
            )

        report += f"""
---

## 11. Final Recommendation

### `{recommendation}`

"""
        if recommendation == "READY_FOR_PR":
            report += (
                "✅ All checks passed. No unresolved high/critical findings. "
                "This feature is ready for PR submission and Jenkins build.\n"
            )
        elif recommendation == "READY_WITH_ALERTS":
            report += (
                "🟠 **READY_WITH_ALERTS** — Local tests pass, sandbox validation passes, and safe patches pass. "
                "OSS dependency alerts or non-blocking clean-code/SonarQube items exist. Proceed with awareness of alerts.\n"
            )
        elif recommendation == "REVIEW_NEEDED":
            report += (
                "⚠️ Tests pass and safe patches were applied, but security/Sonar review items remain. "
                "Human approval required before Jenkins build.\n"
            )
        else:
            report += (
                "🚫 **BLOCKED** — One or more critical issues prevent this feature from proceeding:\n"
                "tests failing, sandbox validation failure, unresolved sensitive data leak, "
                "or critical code/security issue.\n"
            )

        with open(filepath, "w") as f:
            f.write(report)

    def _get_jenkins_recommendation_text(self, recommendation: str) -> str:
        if recommendation == "READY_FOR_PR":
            return "Safe to trigger Jenkins feature build."
        elif recommendation == "READY_WITH_ALERTS":
            return "Safe to trigger Jenkins feature build, but review OSS and non-blocking alerts. Dependency upgrades should be handled with regression testing and security review."
        elif recommendation == "REVIEW_NEEDED":
            return "Review unresolved non-OSS code/security items before triggering Jenkins."
        else:
            return "Do not trigger Jenkins. Resolve blockers first."

    def _write_suggested_changes(self, filepath: str, state: dict):
        """Generate suggested changes markdown."""
        sandbox = state.get("sandbox", {})
        patches = sandbox.get("patches_applied", [])

        content = "# Suggested Changes\n\n"
        content += f"**Total Patches Applied:** {len(patches)}\n\n"

        for patch in patches:
            content += f"## {patch['id']}: {patch['type']}\n\n"
            content += f"**File:** `{patch['file']}`\n\n"
            content += f"{patch['description']}\n\n"
            content += f"**Related findings:** {', '.join(patch.get('finding_ids', []))}\n\n"
            content += "---\n\n"

        with open(filepath, "w") as f:
            f.write(content)

    def _write_jenkins_handoff(self, filepath: str, state: dict, recommendation: str):
        """Write structured Jenkins handoff JSON."""
        # Get branch name dynamically
        branch_name = "feature/boilerplate"
        try:
            import subprocess
            res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                branch_name = res.stdout.strip()
        except Exception:
            pass

        validation = state.get("validation", {})
        oss = state.get("oss_advisory", {})
        sandbox = state.get("sandbox", {})

        handoff_data = {
            "feature": state.get("feature_name", "Refund API") + " Enhancement",
            "branch": branch_name,
            "cruisemode_status": recommendation,
            "tests_passed": validation.get("passed", 0),
            "tests_failed": validation.get("failed", 0),
            "tests_errors": validation.get("errors", 0),
            "safe_patches_applied": sandbox.get("total_patches", 0),
            "oss_alert_required": oss.get("oss_alert_required", False),
            "oss_blocking": False,
            "recommendation": self._get_jenkins_recommendation_text(recommendation)
        }

        with open(filepath, "w") as f:
            json.dump(handoff_data, f, indent=2)

    def _write_validation_results(self, filepath: str, state: dict, recommendation: str):
        """Write structured validation results JSON."""
        validation = state.get("validation", {})
        oss = state.get("oss_advisory", {})
        sandbox = state.get("sandbox", {})
        scan = state.get("scan_analysis", {})

        jenkins_rec = self._get_jenkins_recommendation_text(recommendation)

        # Determine validation statuses
        code_validation_status = "PASSED" if validation.get("status") == "PASSED" else "FAILED"
        test_status = "PASSED" if validation.get("status") == "PASSED" else "FAILED"

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "feature": "Refund API",
            "recommendation": recommendation,
            "final_status": recommendation,
            "code_validation_status": code_validation_status,
            "test_status": test_status,
            "oss_alert_required": oss.get("oss_alert_required", False),
            "oss_blocking": False,
            "safe_patches_applied": sandbox.get("total_patches", 0),
            "jenkins_handoff": {
                "recommendation": jenkins_rec
            },
            "acceptance_criteria_count": len(state.get("acceptance_criteria", [])),
            "scan_summary": {
                "total_findings": scan.get("total_findings", 0),
                "auto_patchable": len(scan.get("auto_patchable", [])),
                "requires_review": len(scan.get("requires_review", [])),
            },
            "patches_applied": sandbox.get("total_patches", 0),
            "oss_advisory": {
                "total_alerts": len(oss.get("findings", [])),
                "blocking": False,
            },
            "validation": validation,
            "generated_tests": state.get("test_generation", {}).get("total_tests", 0),
        }

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)
