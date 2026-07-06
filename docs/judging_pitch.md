# CruiseMode — Judging Pitch

## One-Liner
**CruiseMode: A developer-side multi-agent validation system that helps feature code cruise smoothly into Jenkins and PR review.**

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

## Problem
Developers push code, then wait for Jenkins to flag scan failures, PII violations, and test gaps. This creates long feedback loops, build failures, and security risk.

## Solution
CruiseMode runs **before Jenkins** — right on the developer's machine. It uses a pipeline of 7 specialized agents to:

1. Parse acceptance criteria
2. Analyze scan reports (OWASP, SonarQube, clean code, OSS)
3. Auto-patch safe issues in a sandbox (PII logging, code smells)
4. Flag critical OSS vulnerabilities for human review
5. Generate unit and API tests
6. Run local validation
7. Produce a PR-ready report with a clear recommendation

## Differentiators

| Feature | CruiseMode | Traditional CI |
|---------|-----------|----------------|
| When it runs | Before push | After push |
| Feedback time | Seconds | Minutes to hours |
| Auto-patching | Safe issues only, in sandbox | None |
| OSS safety | Human-in-the-loop for CRITICAL | Build fails |
| Test generation | Automatic | Manual |
| PR report | Auto-generated | Manual |

## Technical Highlights
- **Multi-agent architecture**: 7 specialized Python agents with clean BaseAgent abstraction
- **Sandbox safety**: Patches only in isolated workspace — never modifies original code
- **Deterministic demo**: Works fully offline, no API keys needed
- **Extensible**: Ready for Gemini AI, GCS, BigQuery, Jenkins, GitHub integration

## Impact
- ⏱ Reduces build-fix-rebuild cycles by catching issues pre-push
- 🔒 Prevents PII leaks from reaching CI/CD
- 🧪 Automated test generation improves coverage
- 👁 Human-in-the-loop for risky OSS decisions

## Future Roadmap
- Gemini-powered intelligent patching
- GitHub PR auto-creation
- BigQuery trend dashboards
- Jenkins pipeline integration
- RAPIDS-accelerated batch analysis
