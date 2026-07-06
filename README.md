# 🚗 CruiseMode

**A developer-side multi-agent validation system that helps feature code cruise smoothly into Jenkins and PR review.**

CruiseMode Hackathon Scaling Edition adds an interactive developer dashboard on top of the multi-agent pre-Jenkins validation workflow. Developers can inspect side-by-side diffs between original and sandbox-patched code, ask a grounded AI Advisor questions about the current validation run, simulate a Jenkins handoff using generated artifacts, and promote reviewed sandbox patches to the local workspace. CruiseMode preserves human oversight by applying patches in a sandbox first, surfacing OSS dependency findings as non-blocking alerts, and generating transparent PR and Jenkins handoff reports.

---

## 📋 Interactive Demo Flow

1. Developer finishes a Refund API feature locally.
2. Developer runs CruiseMode before Jenkins.
3. CruiseMode agents analyze acceptance criteria and scan reports.
4. CruiseMode creates a sandbox copy and applies safe patches.
5. Dashboard shows side-by-side diffs of original vs sandbox-patched code.
6. Developer asks CruiseMode AI Advisor why the status is READY_WITH_ALERTS.
7. AI Advisor explains that local tests passed, safe patches were applied, and OSS is an alert.
8. Developer reviews the diff and promotes sandbox patches if acceptable.
9. CruiseMode simulates a Jenkins handoff using validation artifacts.
10. PR report and Jenkins handoff explain what is ready and what needs review.

---


## ✨ Features

- 🔍 **Multi-scan analysis** — OWASP, SonarQube, clean code, OSS dependency reports
- 🔧 **Safe auto-patching** — Fixes PII logging, code smells, and validation issues in a sandbox
- 🚫 **OSS safety** — Never auto-patches dependency issues; flags CRITICAL for human approval
- 🧪 **Test generation** — Generates pytest unit and API tests from acceptance criteria
- ✅ **Local validation** — Runs tests before you push
- 📄 **PR report** — Generates a suggested-changes report with clear recommendation
- 🖥 **Dashboard** — Streamlit UI for visualizing results

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Workflow

```bash
python -m src.main
```

This runs all 7 agents in sequence and generates output files:
- `outputs/validation_results.json`
- `outputs/suggested_changes.md`
- `outputs/pr_report.md`

### 3. View the Dashboard

```bash
streamlit run src/ui/dashboard.py
```

### 4. Run Tests

```bash
# Run generated tests
pytest generated_tests/ -v

# Run project tests
pytest tests/ -v
```

---

## 🏗 Architecture

```
Acceptance Criteria → Scan Analysis → Sandbox Patch → OSS Advisor
                                                          ↓
                                      Test Generation → Validation → PR Report
```

7 specialized agents, each extending `BaseAgent`, execute in sequence:

| Agent | Role |
|-------|------|
| `AcceptanceCriteriaAgent` | Parses AC markdown into structured checklist |
| `ScanAnalysisAgent` | Unifies findings from 4 scan reports |
| `SandboxPatchAgent` | Applies safe patches in `.sandbox/` only |
| `OSSAdvisorAgent` | Flags HIGH/CRITICAL OSS issues (no auto-patch) |
| `TestGenerationAgent` | Generates pytest unit & API tests |
| `ValidationAgent` | Runs pytest, captures results |
| `PRReportAgent` | Generates markdown PR report |

---

## 📁 Project Structure

```
cruisemode/
├── config/           # YAML configs and agent prompt templates
├── src/
│   ├── main.py       # Entry point
│   ├── orchestrator/ # Workflow, graph, router
│   ├── agents/       # 7 agent classes extending BaseAgent
│   ├── tools/        # File utils, scanners, Gemini client
│   ├── sandbox/      # Isolated workspace management
│   ├── cloud/        # GCS/BigQuery placeholders
│   └── ui/           # Streamlit dashboard
├── sample_app/       # Demo FastAPI refund API (with intentional issues)
├── inputs/           # Acceptance criteria & scan reports
├── generated_tests/  # Auto-generated test files
├── outputs/          # Workflow output (reports, results)
├── tests/            # Project tests (unit, integration, evals)
└── docs/             # Architecture, demo script, pitch
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` for optional API keys:

```bash
cp .env.example .env
```

The demo works fully offline without any API keys. Gemini, GCS, and BigQuery integrations are scaffolded but not required.

---

## 📋 Sample App

The `sample_app/` directory contains a FastAPI Refund API with **intentional issues**:

- ⚠️ Unsafe PII logging (full request body with email & card number)
- ⚠️ Broad exception handling (`except Exception`)
- ⚠️ Code smells (cognitive complexity)

CruiseMode detects and patches these in the sandbox.

---

## 🔮 Future Roadmap

- [ ] Gemini AI-powered intelligent patching
- [ ] Real Jenkins pipeline integration
- [ ] GitHub PR auto-creation
- [ ] BigQuery trend dashboards with RAPIDS
- [ ] Docker-based sandbox isolation
- [ ] LangGraph-based agent orchestration

---

## 📄 License

MIT
