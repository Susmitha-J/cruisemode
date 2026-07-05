# CruiseMode Demo Script

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

## Demo Flow (3–5 minutes)

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
