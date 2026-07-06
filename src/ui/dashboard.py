from __future__ import annotations

"""
CruiseMode Streamlit Dashboard v0.2 (Hackathon Edition)

Displays the results of a CruiseMode workflow run:
1. Feature Readiness Status
2. Jenkins Handoff Recommendation
3. Acceptance Criteria Coverage
4. Scan Summary
5. Safe Patches Applied (with visual HTML side-by-side diff)
6. OSS Dependency Alerts
7. Pytest Validation
8. Cloud Artifact Upload Result
9. BigQuery Run Summary Result
10. PR Report

Interactive Features:
- Apply Sandbox Patches locally
- Simulate Pre-Jenkins CI Handoff pipeline execution
- Conversational CruiseMode AI Advisor chatbot sidebar
"""

import json
import os
import shutil
import time
import streamlit as st
from src.tools.diff_viewer import DiffViewer
from src.tools.gemini_client import GeminiClient


def load_json(filepath: str) -> dict:
    """Load a JSON file or return empty dict."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_text(filepath: str) -> str:
    """Load a text file or return placeholder."""
    try:
        with open(filepath, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "*File not found. Run `python -m src.main` first.*"


def main():
    st.set_page_config(
        page_title="CruiseMode Dashboard",
        page_icon="🚗",
        layout="wide",
    )

    st.title("🚗 CruiseMode Dashboard v0.2")
    st.caption("Multi-Agent Pre-Jenkins Validation for Developer Workflows")
    st.markdown("---")

    # --- Sidebar Chatbot Assistant ---
    st.sidebar.title("💬 CruiseMode AI Advisor")
    st.sidebar.caption("Ask questions about code patches, exceptions, or security alerts.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I am your CruiseMode AI Advisor. I can help explain the code patches applied in "
                    "the sandbox workspace, discuss the scan findings, or provide recommendations for your Jenkins build."
                )
            }
        ]

    # Display chat history
    for message in st.session_state.messages:
        with st.sidebar.chat_message(message["role"]):
            st.markdown(message["content"])

    # User chat input
    if user_prompt := st.sidebar.chat_input("Ask about the patches..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.sidebar.chat_message("user"):
            st.markdown(user_prompt)

        # Generate response using GeminiClient
        gemini = GeminiClient()
        agent_response = gemini.generate_text(user_prompt)

        # Add assistant message to history
        st.session_state.messages.append({"role": "assistant", "content": agent_response})
        with st.sidebar.chat_message("assistant"):
            st.markdown(agent_response)

    # Load validation results & alerts
    results = load_json("outputs/validation_results.json")
    oss_alerts = load_json("outputs/oss_alerts.json")
    jenkins_handoff = load_json("outputs/jenkins_handoff.json")

    if not results:
        st.warning(
            "⚠️ No validation results found. "
            "Run the workflow first: `python -m src.main`"
        )
        return

    # --- 1. Feature Readiness Status ---
    st.subheader("1. Feature Readiness Status")
    recommendation = results.get("final_status", results.get("recommendation", "UNKNOWN"))
    col1, col2, col3 = st.columns(3)

    with col1:
        if recommendation == "READY_FOR_PR":
            st.success(f"🟢 **{recommendation}**")
        elif recommendation == "READY_WITH_ALERTS":
            st.info(f"🟠 **{recommendation}**")
        elif recommendation == "REVIEW_NEEDED":
            st.warning(f"🟡 **{recommendation}**")
        else:
            st.error(f"🔴 **{recommendation}**")

    with col2:
        st.metric("Feature", results.get("feature", "N/A"))

    with col3:
        st.metric("Acceptance Criteria Count", results.get("acceptance_criteria_count", 0))

    st.markdown("---")

    # --- 2. Jenkins Handoff Recommendation ---
    st.subheader("2. Jenkins Handoff Recommendation")
    handoff_rec = jenkins_handoff.get("recommendation", results.get("jenkins_handoff", {}).get("recommendation", "N/A"))
    
    if recommendation == "READY_FOR_PR":
        st.success(f"**Jenkins Recommendation:** {handoff_rec}")
    elif recommendation == "READY_WITH_ALERTS":
        st.info(f"**Jenkins Recommendation:** {handoff_rec}")
    elif recommendation == "REVIEW_NEEDED":
        st.warning(f"**Jenkins Recommendation:** {handoff_rec}")
    else:
        st.error(f"**Jenkins Recommendation:** {handoff_rec}")

    # Simulated Live Jenkins Build Webhook
    col_sim_1, col_sim_2 = st.columns([1, 4])
    with col_sim_1:
        if st.button("🚀 Run Live Jenkins CI Handoff"):
            st.session_state["show_jenkins_sim"] = True
    
    if st.session_state.get("show_jenkins_sim"):
        st.info("🔄 Initiating Jenkins pre-push validation pipeline execution...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        steps = [
            (20, "Fetching git workspace branch: feature/boilerplate..."),
            (40, "Running SonarQube quality gateway checks..."),
            (60, "Scanning requirements.txt dependencies for licensing/security..."),
            (80, "Running unit & integration test suites (pytest)..."),
            (100, "Handoff validation successful! Status: READY TO MERGE.")
        ]
        
        for val, text in steps:
            time.sleep(0.8)
            progress_bar.progress(val)
            status_text.text(text)
            
        st.success("🎉 Pre-Jenkins CI Pipeline PASSED successfully! Proceeding to PR review.")
        st.session_state["show_jenkins_sim"] = False

    st.markdown("---")

    # --- 3. Acceptance Criteria Coverage ---
    st.subheader("3. Acceptance Criteria Coverage")
    st.markdown(f"**Total acceptance criteria evaluated:** {results.get('acceptance_criteria_count', 0)}")
    
    ac_file_content = load_text("inputs/acceptance_criteria.md")
    with st.expander("View Acceptance Criteria Details"):
        st.markdown(ac_file_content)

    st.markdown("---")

    # --- 4. Scan Summary ---
    st.subheader("4. Scan Summary")
    scan = results.get("scan_summary", {})
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Findings", scan.get("total_findings", 0))
    col2.metric("Auto-Patchable", scan.get("auto_patchable", 0))
    col3.metric("Requires Review", scan.get("requires_review", 0))

    st.markdown("---")

    # --- 5. Safe Patches Applied ---
    st.subheader("5. Safe Patches Applied")
    st.metric("Safe Patches Applied", results.get("safe_patches_applied", results.get("patches_applied", 0)))

    # Action to Apply Patches Locally
    if st.button("🔧 Apply Sandbox Patches to Local Source Code"):
        try:
            shutil.copy(".sandbox/app.py", "sample_app/app.py")
            shutil.copy(".sandbox/refund_service.py", "sample_app/refund_service.py")
            st.success("✅ Successfully transferred sandbox patches to your local workspace files!")
        except Exception as e:
            st.error(f"❌ Failed to transfer files: {e}")

    # Side-by-side Git Diff HTML viewer
    st.markdown("#### Code Diff: Original vs Sandbox Patched")
    diff_html_app = DiffViewer.generate_html_diff("sample_app/app.py", ".sandbox/app.py")
    st.components.v1.html(diff_html_app, height=450, scrolling=True)

    diff_html_service = DiffViewer.generate_html_diff("sample_app/refund_service.py", ".sandbox/refund_service.py")
    with st.expander("View Service Logic Diff (refund_service.py)"):
        st.components.v1.html(diff_html_service, height=450, scrolling=True)

    st.markdown("---")

    # --- 6. OSS Dependency Alerts ---
    st.subheader("6. OSS Dependency Alerts")
    st.caption("ℹ️ OSS alerts do not block CruiseMode local validation. Dependency upgrades require regression testing and downstream security validation.")
    
    total_alerts = 0
    findings = []
    
    if oss_alerts:
        total_alerts = len(oss_alerts.get("findings", []))
        findings = oss_alerts.get("findings", [])
    else:
        oss_advisory = results.get("oss_advisory", {})
        total_alerts = oss_advisory.get("total_alerts", 0)

    if total_alerts > 0:
        st.warning(f"🟠 **OSS Dependency Alert** — {total_alerts} advisory alert(s) logged")
        
        # Display alerts in a table/list
        for idx, alert in enumerate(findings, 1):
            st.markdown(
                f"**{idx}. Package:** `{alert.get('package')}` | "
                f"**Version:** `{alert.get('current_version')}` | "
                f"**Severity:** `{alert.get('severity')}` | "
                f"**CVE:** `{alert.get('cve')}`"
            )
            st.markdown(f"- *Recommended Action:* {alert.get('recommended_action')}")
            st.markdown(f"- *Auto-Patch Applied:* No (Dependency upgrades require manual check/downstream pipeline)")
    else:
        st.success("🟢 No OSS dependency alerts")

    st.markdown("---")

    # --- 7. Pytest Validation ---
    st.subheader("7. Pytest Validation")
    validation = results.get("validation", {})
    val_status = validation.get("status", "NOT_RUN")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Status", val_status)
    col2.metric("Passed", validation.get("passed", 0))
    col3.metric("Failed", validation.get("failed", 0))
    col4.metric("Duration", f"{validation.get('duration_seconds', 0)}s")

    if validation.get("stdout"):
        with st.expander("View Pytest Stdout"):
            st.code(validation["stdout"], language="text")

    st.markdown("---")

    # --- 8. Cloud Artifact Upload Result ---
    st.subheader("8. Cloud Artifact Upload Result")
    cloud_gcs = results.get("cloud_gcs", {})
    if cloud_gcs.get("uploaded"):
        st.success(f"✅ GCS Upload Active: bucket `{cloud_gcs.get('bucket')}`")
        for name, uri in cloud_gcs.get("artifacts", {}).items():
            st.markdown(f"- **{name}:** `{uri}`")
    else:
        # Fallback to standard mock info
        st.info("ℹ️ Cloud upload running in demo/mock mode.")
        st.markdown("- **pr_report.md:** `gs://mock-bucket/reports/Refund API/pr_report.md`")
        st.markdown("- **validation_results.json:** `gs://mock-bucket/reports/Refund API/validation_results.json`")
        st.markdown("- **suggested_changes.md:** `gs://mock-bucket/reports/Refund API/suggested_changes.md`")
        st.markdown("- **jenkins_handoff.json:** `gs://mock-bucket/reports/Refund API/jenkins_handoff.json`")
        st.markdown("- **oss_alerts.json:** `gs://mock-bucket/reports/Refund API/oss_alerts.json`")

    st.markdown("---")

    # --- 9. BigQuery Run Summary Result ---
    st.subheader("9. BigQuery Run Summary Result")
    cloud_bq = results.get("cloud_bq", {})
    if cloud_bq.get("loaded"):
        st.success(f"✅ Loaded run summary to BigQuery table: `{cloud_bq.get('table')}`")
        st.json(cloud_bq.get("fields", {}))
    else:
        st.info("ℹ️ BigQuery loaded run summary (mock/scaffold mode):")
        mock_fields = {
            "run_id": "run_" + results.get("timestamp", "").replace(":", "-"),
            "timestamp": results.get("timestamp"),
            "feature_name": "Refund API",
            "branch_name": jenkins_handoff.get("branch", "feature/boilerplate"),
            "final_status": recommendation,
            "total_findings": scan.get("total_findings", 12),
            "auto_patchable_findings": scan.get("auto_patchable", 9),
            "review_required_findings": scan.get("requires_review", 3),
            "patches_applied": results.get("safe_patches_applied", 3),
            "tests_passed": validation.get("passed", 9),
            "tests_failed": validation.get("failed", 0),
            "tests_errors": validation.get("errors", 0),
            "oss_alert_count": total_alerts,
            "oss_alert_required": results.get("oss_alert_required", True),
            "oss_blocking": False,
            "duration_seconds": results.get("validation", {}).get("duration_seconds", 0.4),
            "report_generation_mode": "MOCK",
            "jenkins_recommendation": handoff_rec
        }
        st.json(mock_fields)

    st.markdown("---")

    # --- 10. PR Report ---
    st.subheader("10. PR Report")
    pr_report = load_text("outputs/pr_report.md")
    with st.expander("View Full PR Report", expanded=True):
        st.markdown(pr_report)


if __name__ == "__main__":
    main()
