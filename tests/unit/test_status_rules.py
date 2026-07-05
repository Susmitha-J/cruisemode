from __future__ import annotations

import os
import json
import pytest
from src.agents.pr_report import PRReportAgent


def test_oss_finding_alone_not_blocked_or_review_needed():
    """
    1. Critical OSS finding alone does not produce BLOCKED.
    2. Critical OSS finding alone does not produce REVIEW_NEEDED.
    3. Passing tests + critical OSS alert produces READY_WITH_ALERTS.
    """
    agent = PRReportAgent()
    
    # State where tests pass, safe patches pass, but critical OSS alert exists
    state = {
        "validation": {"status": "PASSED"},
        "sandbox": {"patches_applied": [{"finding_ids": ["CC-001"], "type": "clean_code"}], "total_patches": 1},
        "scan_analysis": {
            "all_findings": [
                {"id": "OSS-001", "source_report": "oss", "severity": "CRITICAL", "package": "pyjwt"},
                {"id": "CC-001", "source_report": "clean_code", "severity": "MEDIUM"}
            ]
        },
        "oss_advisory": {
            "oss_alert_required": True,
            "findings": [
                {"package": "pyjwt", "severity": "CRITICAL", "cve": "CVE-2022-29217"}
            ]
        }
    }
    
    rec = agent._determine_recommendation(state)
    assert rec == "READY_WITH_ALERTS"
    assert rec != "BLOCKED"
    assert rec != "REVIEW_NEEDED"


def test_failing_tests_produce_blocked():
    """
    4. Failing tests produce BLOCKED.
    """
    agent = PRReportAgent()
    
    state = {
        "validation": {"status": "FAILED"},
        "sandbox": {"patches_applied": [], "total_patches": 0},
        "scan_analysis": {
            "all_findings": []
        },
        "oss_advisory": {
            "oss_alert_required": False,
            "findings": []
        }
    }
    
    rec = agent._determine_recommendation(state)
    assert rec == "BLOCKED"


def test_unresolved_critical_pii_security_produces_blocked():
    """
    5. Unresolved critical PII/security issue produces BLOCKED.
    """
    agent = PRReportAgent()
    
    state = {
        "validation": {"status": "PASSED"},
        "sandbox": {"patches_applied": [], "total_patches": 0},
        "scan_analysis": {
            "all_findings": [
                {"id": "OWASP-001", "source_report": "owasp", "category": "pii_logging", "severity": "CRITICAL"}
            ]
        },
        "oss_advisory": {
            "oss_alert_required": False,
            "findings": []
        }
    }
    
    rec = agent._determine_recommendation(state)
    assert rec == "BLOCKED"


def test_jenkins_recommendation_ready_with_alerts():
    """
    6. Jenkins handoff for READY_WITH_ALERTS recommends safe trigger with alert review caution.
    """
    agent = PRReportAgent()
    rec_text = agent._get_jenkins_recommendation_text("READY_WITH_ALERTS")
    assert "Safe to trigger Jenkins feature build, but review OSS and non-blocking alerts" in rec_text


def test_oss_alerts_json_non_blocking(tmp_path):
    """
    7. oss_alerts.json has blocking: false.
    """
    from src.agents.oss_advisor import OSSAdvisorAgent
    advisor = OSSAdvisorAgent()
    
    # Run the advisor with a critical OSS finding to generate oss_alerts.json
    outputs_dir = tmp_path / "outputs"
    os.makedirs(outputs_dir, exist_ok=True)
    
    state = {
        "output_dir": str(outputs_dir),
        "scan_analysis": {
            "all_findings": [
                {"id": "OSS-001", "source_report": "oss", "severity": "CRITICAL", "package": "pyjwt", "installed_version": "1.7.1", "cve": "CVE-2022-29217"}
            ]
        }
    }
    
    advisor.run(state)
    
    alerts_file = outputs_dir / "oss_alerts.json"
    assert os.path.exists(alerts_file)
    
    with open(alerts_file, "r") as f:
        data = json.load(f)
        
    assert data["alert_required"] is True
    assert data["blocking"] is False
    assert "findings" in data
    assert len(data["findings"]) == 1
    assert data["findings"][0]["package"] == "pyjwt"
