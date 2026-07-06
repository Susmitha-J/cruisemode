# CruiseMode Demo Script

## Overview

CruiseMode Hackathon Scaling Edition adds an interactive developer dashboard on top of the multi-agent pre-Jenkins validation workflow. Developers can inspect side-by-side diffs between original and sandbox-patched code, ask a grounded AI Advisor questions about the current validation run, simulate a Jenkins handoff using generated artifacts, and promote reviewed sandbox patches to the local workspace. CruiseMode preserves human oversight by applying patches in a sandbox first, surfacing OSS dependency findings as non-blocking alerts, and generating transparent PR and Jenkins handoff reports.

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

## Prerequisites

- Python 3.10+
- pip

## Setup (1 minute)

```bash
# Install dependencies
pip install -r requirements.txt

# (Optional) Copy and configure .env
cp .env.example .env
```

## Demo Flow Detailed Steps

### Step 1: Show the Problem

> "Here's a typical refund API with common issues that would fail a Jenkins build."

Open `sample_app/app.py` and point out:
- Line 36: Unsafe PII logging (full request object including email & card number)
- `refund_service.py`: Broad exception handling, code smells

### Step 2: Show the Scan Reports

> "We have scan reports from four tools. Let's see what they found."

Open `inputs/` and highlight:
- OWASP: PII logging violation
- Clean Code: Broad exception, complexity
- SonarQube: Code smell
- OSS: **CRITICAL** pyjwt vulnerability (CVE-2022-29217, CVSS 9.8)

### Step 3: Run CruiseMode

```bash
python -m src.main
```

> "CruiseMode runs 7 agents in sequence. Watch it analyze, patch, test, and report."

### Step 4: Show the Results

Open `outputs/`:
- `pr_report.md` — Full PR report with recommendation
- `suggested_changes.md` — Patches applied
- `validation_results.json` — Structured test results

### Step 5: Launch the Dashboard

```bash
streamlit run src/ui/dashboard.py
```

> "The dashboard gives a real-time view of feature readiness."

### Step 6: Key Takeaways

- ✅ PII logging was automatically fixed
- ✅ Code smells were patched
- ✅ Tests were generated and passed
- ⚠️ Critical OSS vulnerability flagged — **human approval required**
- 📋 PR report recommends **REVIEW_NEEDED**

## Talking Points

- "CruiseMode runs **before** Jenkins — catching issues at the developer's desk"
- "It **never** auto-patches OSS dependencies — that requires human judgment"
- "All patches happen in a **sandbox** — the original code is untouched"
- "One command to validate, one dashboard to review"
