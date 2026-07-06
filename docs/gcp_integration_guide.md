# CruiseMode — Google Cloud Platform Production Setup & Integration Guide

This guide describes how to configure, observe, and manage the live CruiseMode production environment deployed in your Google Cloud Project: `cruisemode-501605`.

---

## 🏁 1. Live Google Cloud Resources Created

We have successfully initialized and bound the following resources on your GCP project:

1. **Google Cloud Storage (GCS) Bucket:**
   - **Name:** `gs://cruisemode-reports-501605`
   - **Region:** `us-central1`
   - **Purpose:** Stores PR reports (`pr_report.md`), suggested changes diffs, and verification artifacts for audit logs and collaboration.
2. **BigQuery Dataset:**
   - **Name:** `cruisemode`
   - **Table:** `validation_runs` (Auto-generated on first run)
   - **Purpose:** Telemetry logging of pre-push agent runs for smart city/enterprise security trend dashboards.
3. **Cloud Run Service:**
   - **Service Name:** `cruisemode-dashboard`
   - **Live URL:** **[https://cruisemode-dashboard-137159140496.us-central1.run.app](https://cruisemode-dashboard-137159140496.us-central1.run.app)**

---

## 🔑 2. How to Configure Your Gemini API Key

By default, the deployed dashboard uses offline mock fallback responses for the chat advisor. To enable real, grounded Gemini 1.5 Flash API calls, update the Cloud Run service environment variables with your Gemini key:

```bash
gcloud run services update cruisemode-dashboard \
    --update-env-vars GOOGLE_API_KEY=YOUR_GEMINI_API_KEY \
    --project=cruisemode-501605 \
    --region=us-central1
```

Once updated, the **CruiseMode AI Advisor** sidebar chatbot and patching engine will automatically switch from mock mode to real LLM calls!

---

## 🔮 3. Walkthrough of the Production Roadmap Demos

The dashboard has an interactive **"Future Roadmap"** tab featuring demonstrations for the following 6 pillars:

### 1. 🧠 Gemini AI-Powered Intelligent Patching
- **Concept:** Transition from template-based regex checks to zero-shot LLM refactoring.
- **Demo:** Enter a code snippet in the text area on Tab 3, press the patch button, and see the model instantly narrow exceptions to specific targets.

### 2. 🔗 Real Jenkins Pipeline Integration
- **Concept:** Triggers a Jenkins feature build automatically after pre-push checks pass.
- **Demo:** Hook your Jenkins server by sending the structured CruiseMode validation payload to:
  `POST https://jenkins.municipal.gov/job/cruisemode-pipeline/buildWithParameters?token=BUILD_TOKEN&branch=feature/boilerplate`

### 3. 🐙 GitHub PR Auto-Creation
- **Concept:** Auto-creates branches and raises Pull Requests containing the sandbox security patches.
- **Demo:** Click the simulation button in Tab 3 to visualize the CLI staging, pushing, and raising a PR.

### 4. 📈 BigQuery Trend Dashboards with RAPIDS
- **Concept:** Query millions of compliance telemetry rows in BigQuery using Spark RAPIDS.
- **Demo:** Visualize monthly compliance trends in Tab 2, backed by SQL queries like:
  ```sql
  SELECT service_name, COUNT(run_id) as total_runs, AVG(duration_seconds)
  FROM `cruisemode-501605.cruisemode.validation_runs`
  GROUP BY service_name
  ```

### 5. 🐳 Docker-Based Sandbox Isolation
- **Concept:** Upgrade local folder sandboxes to isolated, short-lived Docker containers to secure test execution fully.
- **CLI Trigger:**
  `docker run --rm -v $(pwd):/workspace -w /workspace python:3.9-slim pytest generated_tests/`

### 6. 🕸️ LangGraph-Based Agent Orchestration
- **Concept:** Moves from sequential graphs to cycles with validation feedback loops.
- **Visualization:** View the state graph in Tab 3 showing how validation errors trigger automatic test rewrites.
