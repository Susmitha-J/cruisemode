from __future__ import annotations

"""
CruiseMode Streamlit Dashboard v0.2 (Hackathon Scaling Edition)

Two Tab Layout:
- Tab 1: 🚗 Active Validation Run
  Displays the results of a CruiseMode workflow run with safety controls,
  visual code diffs, simulated Jenkins handoff simulation, and artifact-grounded AI Advisor chatbot sidebar.
- Tab 2: ⚡ NVIDIA RAPIDS Telemetry Analytics
  Simulates a workspace with 50,000 historical code scans/validation logs.
  Benchmarks standard CPU pandas vs NVIDIA GPU cuDF to prove acceleration impact.
"""

import json
import os
import shutil
import time
import pandas as pd
import streamlit as st
from src.tools.diff_viewer import DiffViewer
from src.tools.gemini_client import GeminiClient
from src.tools.telemetry_analyzer import TelemetryAnalyzer


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

    # Load validation results & alerts
    results = load_json("outputs/validation_results.json")
    oss_alerts = load_json("outputs/oss_alerts.json")
    jenkins_handoff = load_json("outputs/jenkins_handoff.json")

    # --- Sidebar Chatbot Assistant ---
    st.sidebar.title("💬 CruiseMode AI Advisor")
    st.sidebar.caption("CruiseMode AI Advisor — explains this validation run")
    
    if not results:
        st.sidebar.warning("Run `python3 -m src.main` first to generate CruiseMode artifacts.")
    else:
        # Suggested questions helper UI
        st.sidebar.markdown("""
        **Try asking:**
        - *Why is the status READY_WITH_ALERTS?*
        - *What PII issue was patched?*
        - *Why did CruiseMode not patch OSS?*
        - *Can this proceed to Jenkins?*
        - *What should I review before PR?*
        """)
        st.sidebar.markdown("---")

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

    # User chat input (only allowed if artifacts exist)
    if results:
        if user_prompt := st.sidebar.chat_input("Ask about this validation run..."):
            # Add user message to history
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            with st.sidebar.chat_message("user"):
                st.markdown(user_prompt)

            # Build context from the 5 validation artifacts
            context = ""
            artifacts = {
                "outputs/validation_results.json": "Validation Results (JSON)",
                "outputs/pr_report.md": "PR Report (Markdown)",
                "outputs/suggested_changes.md": "Suggested Changes (Markdown)",
                "outputs/oss_alerts.json": "OSS Alerts (JSON)",
                "outputs/jenkins_handoff.json": "Jenkins Handoff (JSON)"
            }
            
            for filepath, desc in artifacts.items():
                if os.path.exists(filepath):
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            context += f"\n=== ARTIFACT: {desc} ===\n{f.read()}\n"
                    except Exception:
                        pass
            
            # Grounded prompt instruction
            system_instruction = (
                "You are CruiseMode AI Advisor. Answer only using the provided CruiseMode run artifacts. "
                "If the answer is not available in the artifacts, say that the current run artifacts do "
                "not contain enough information. Do not invent test results, Jenkins results, scan results, "
                "files, counts, or security conclusions."
            )
            
            full_prompt = (
                f"{system_instruction}\n\n"
                f"Context from CruiseMode run artifacts:\n{context}\n\n"
                f"User Question: {user_prompt}"
            )

            # Generate response using GeminiClient
            gemini = GeminiClient()
            agent_response = gemini.generate_text(full_prompt)

            # Add assistant message to history
            st.session_state.messages.append({"role": "assistant", "content": agent_response})
            with st.sidebar.chat_message("assistant"):
                st.markdown(agent_response)

    # --- Two Tab Navigation Layout ---
    tab_run, tab_telemetry = st.tabs(["🚗 Active Validation Run", "⚡ NVIDIA RAPIDS Telemetry Analytics"])

    # =========================================================================
    # TAB 1: ACTIVE VALIDATION RUN
    # =========================================================================
    with tab_run:
        if not results:
            st.warning(
                "⚠️ No validation results found. "
                "Run the workflow first: `python3 -m src.main`"
            )
        else:
            # --- 1. Feature Readiness ---
            st.subheader("1. Feature Readiness")
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

            # Honest Jenkins Handoff Simulation UI
            st.caption("This simulation does not run a real Jenkins job. It visualizes how CruiseMode's validation results and handoff artifact would guide a Jenkins feature build.")
            
            col_sim_1, col_sim_2 = st.columns([1, 4])
            with col_sim_1:
                if st.button("🚀 Run Jenkins Handoff Simulation"):
                    st.session_state["show_jenkins_sim"] = True
            
            if st.session_state.get("show_jenkins_sim"):
                st.info("🔄 Initiating Jenkins handoff simulation...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                steps = [
                    (20, "Simulated checkout of git workspace..."),
                    (40, "Simulated SonarQube quality gate scan..."),
                    (60, "Simulated OSS dependency scan analysis..."),
                    (80, "Simulated unit/API test validation run..."),
                    (100, "Simulated Jenkins handoff recommendation evaluated.")
                ]
                
                for val, text in steps:
                    time.sleep(0.8)
                    progress_bar.progress(val)
                    status_text.text(text)
                    
                st.success(f"🎉 Simulated Jenkins handoff completed with recommendation: {recommendation}")
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

            # --- 5. Safe Sandbox Patches ---
            st.subheader("5. Safe Sandbox Patches")
            st.metric("Safe Patches Applied", results.get("safe_patches_applied", results.get("patches_applied", 0)))

            # Safety Warning & Promotion Controls
            st.info("CruiseMode applies patches only inside the sandbox by default. Review the side-by-side diff before promoting changes to local source. Promoting patches modifies the local sample_app workspace but does not commit or push code.")

            if st.button("🔧 Promote Reviewed Sandbox Patches to Local Source"):
                try:
                    shutil.copy(".sandbox/app.py", "sample_app/app.py")
                    shutil.copy(".sandbox/refund_service.py", "sample_app/refund_service.py")
                    st.success("✅ Reviewed sandbox patches were promoted to the local source workspace. Review and commit these changes manually.")
                except Exception as e:
                    st.error(f"❌ Failed to promote sandbox patches: {e}")

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

            # --- 7. Local Test Validation ---
            st.subheader("7. Local Test Validation")
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

            # --- 8. Cloud Evidence Storage ---
            st.subheader("8. Cloud Evidence Storage")
            cloud_gcs = results.get("cloud_gcs", {})
            if cloud_gcs.get("uploaded"):
                st.success(f"✅ GCS Upload Active: bucket `{cloud_gcs.get('bucket')}`")
                for name, uri in cloud_gcs.get("artifacts", {}).items():
                    st.markdown(f"- **{name}:** `{uri}`")
            else:
                st.info("ℹ️ Cloud upload running in demo/mock mode.")
                st.markdown("- **pr_report.md:** `gs://mock-bucket/reports/Refund API/pr_report.md`")
                st.markdown("- **validation_results.json:** `gs://mock-bucket/reports/Refund API/validation_results.json`")
                st.markdown("- **suggested_changes.md:** `gs://mock-bucket/reports/Refund API/suggested_changes.md`")
                st.markdown("- **jenkins_handoff.json:** `gs://mock-bucket/reports/Refund API/jenkins_handoff.json`")
                st.markdown("- **oss_alerts.json:** `gs://mock-bucket/reports/Refund API/oss_alerts.json`")

            st.markdown("---")

            # --- 9. BigQuery Run History ---
            st.subheader("9. BigQuery Run History")
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
            with st.expander("View PR Report Detail", expanded=True):
                st.markdown(pr_report)

    # =========================================================================
    # TAB 2: NVIDIA RAPIDS TELEMETRY ANALYTICS
    # =========================================================================
    with tab_telemetry:
        st.subheader("⚡ NVIDIA RAPIDS Telemetry Analytics")
        st.caption("Analyzing historical compliance runs across 50,000 municipal smart community code repositories.")

        st.info(
            "💡 **Decision Bottleneck:** Running safety audits and trend reports across thousands of municipal repositories "
            "causes severe data processing lag on standard CPUs. Transitioning the pandas pipeline to GPU-accelerated cuDF "
            "solves this data bottleneck, providing real-time decision intelligence for city and enterprise stakeholders."
        )

        with st.spinner("Running historical logs benchmark (50,000 runs)..."):
            benchmark = TelemetryAnalyzer.run_benchmark()

        # Display Metrics
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Telemetry Record Scale", f"{benchmark['row_count']:,} runs")
        col_m2.metric("CPU Pandas Time", f"{benchmark['cpu_time_ms']:.2f} ms")
        
        gpu_label = "NVIDIA cuDF Time"
        if benchmark["simulated"]:
            gpu_label += " (Simulated GPU)"
        
        col_m3.metric(gpu_label, f"{benchmark['gpu_time_ms']:.2f} ms")
        col_m4.metric("NVIDIA RAPIDS Speedup", f"{benchmark['speedup']:.1f}x Faster")

        # Bar chart comparing processing speeds
        st.markdown("#### Processing Time Comparison (Lower is Better)")
        speed_data = pd.DataFrame({
            "Execution Mode": ["Standard CPU (Pandas)", "Accelerated GPU (cuDF / RAPIDS)"],
            "Time (ms)": [benchmark["cpu_time_ms"], benchmark["gpu_time_ms"]]
        }).set_index("Execution Mode")
        st.bar_chart(speed_data)

        # Plot compliance trends
        st.markdown("#### 📈 Historical Compliance Readiness Trends (Monthly)")
        monthly_df = benchmark["monthly_trends"].set_index("month")
        st.line_chart(monthly_df)

        # Group summary breakdown
        st.markdown("#### 🏢 Smart Community Repository Compliance Summary")
        st.dataframe(
            benchmark["service_breakdown"].rename(columns={
                "service_name": "Municipal Service Repo",
                "total_runs": "Validation Runs",
                "avg_vulnerabilities": "Avg Vulns Detected",
                "total_patches": "Patches Promoted",
                "pass_rate": "Local Test Pass Rate"
            }),
            use_container_width=True
        )


if __name__ == "__main__":
    main()
