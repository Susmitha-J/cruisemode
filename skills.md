# CruiseMode Playbook — Development Skills & Best Practices (`skills.md`)

This document serves as the repository playbook. Every time a new feature, agent, or integration is modified or added, the developer (or AI coding assistant) **must** verify alignment against these five core development pillars:

---

## 🧠 1. Hallucination Prevention (Grounded AI)

To ensure all CruiseMode agents and dashboard advisors remain strictly grounded in reality and never generate fake metrics, mock test results, or non-existent files:

- **Strict Prompt Grounding:** All LLM prompts must include explicit grounding instructions restricting responses to provided inputs.
- **System Instructions:** When calling Gemini API via the `google-generativeai` SDK, always configure `system_instruction` in the `GenerativeModel` instance rather than appending it to user prompts.
- **Validation Checkpoints:** Ensure agents verify structured JSON files (e.g. `outputs/validation_results.json`) before generating markdown summaries, rather than estimating status or coverage.
- **Offline Fallback:** Maintain the deterministic mock response dictionary (`src/tools/gemini_client.py`) for offline environments, returning `The current run artifacts do not contain enough information.` for queries outside the scope of current findings.

---

## 🧹 2. Clean Code & Repository Standards

Maintain production-grade code readability, modularity, and correctness:

- **Type Hinting:** Annotate all function signatures and variable returns using Python type hints (`str`, `dict[str, Any]`, `list[Any]`, etc.).
- **Docstring Compliance:** Use Google-style docstrings for every class, method, and function, specifying Arguments, Returns, and Raises.
- **Separation of Concerns:** Keep tools, agents, and orchestrators modular. Agents must only handle prompt engineering and response parsing; tools must perform all raw calculations, file edits, and system operations.
- **Zero Telemetry Leaks:** Never hardcode log outputs containing raw local paths, username strings, or debug files. Ensure all temp files reside inside `.sandbox/` and are ignored in `.gitignore`.

---

## 🛡️ 3. Security Guardrails

Ensure sandbox execution and data parsing are secure against malicious inputs or code injection:

- **Safe Sandbox Execution:** When executing generated test files in the sandbox:
  - Use `subprocess.run()` with `shell=False` and pass arguments as list tokens (e.g. `["pytest", "generated_tests/"]`).
  - Set tight execution timeouts (e.g., `timeout=15` seconds) to prevent infinite loops or denial of service.
- **PII Leak Prevention:** The `PIIDetector` tool must sanitize data before it leaves the developer's workstation. Never upload unmasked PII (emails, cards, secrets) to GCS or BigQuery.
- **Input Sanitization:** Avoid raw SQL concatenation when querying BigQuery or local databases. Always use parameterized queries or client-provided parameter dictionaries.

---

## 🔑 4. Authentication & Secret Management

Ensure credentials and access keys are managed securely and comply with enterprise-grade cloud practices:

- **No Hardcoded Credentials:** Never check in API keys (`GOOGLE_API_KEY`, GCP service account keys) to version control.
- **Application Default Credentials (ADC):** Trust Google Cloud Application Default Credentials (ADC) for GCS and BigQuery. The code should instantiate clients simply:
  ```python
  from google.cloud import storage
  client = storage.Client(project=project_id)
  ```
  On Cloud Run, this automatically inherits the Service Account IAM permissions without needing service account JSON key files.
- **Environment Fallbacks:** Always wrap GCP client initializations in `try-except` blocks. If credentials are not present, fall back to mock demo mode gracefully instead of crashing the process.

---

## ⚡ 5. Real-Time Workflows & Event Processing

To scale CruiseMode from a batch-oriented pre-commit CLI to a real-time developer decision companion:

- **File System Watchers (Watchdog):** Integrate `watchdog` to monitor files in `sample_app/`. When a developer saves a file, automatically trigger CruiseMode's validation agent in the background.
- **Asynchronous Task Queues:** Use Python's `asyncio` or task runners to process GCS uploads and BigQuery loading asynchronously, keeping the CLI run time under 1 second.
- **Streamlit Live State:** Utilise Streamlit's `st.session_state` and component updates to refresh visual git diffs and test statuses instantly as file watcher events fire in the workspace.
