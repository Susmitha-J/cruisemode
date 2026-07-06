# CruiseMode Architecture

## System Overview

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


```
┌─────────────────────────────────────────────────────────────────┐
│                      CruiseMode Workflow                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │ Acceptance       │───▶│ Scan Analysis   │                    │
│  │ Criteria Agent   │    │ Agent           │                    │
│  └─────────────────┘    └────────┬────────┘                    │
│                                  │                              │
│                    ┌─────────────┴─────────────┐               │
│                    ▼                           ▼               │
│          ┌─────────────────┐       ┌─────────────────┐        │
│          │ Sandbox Patch   │       │ OSS Advisor     │        │
│          │ Agent           │       │ Agent           │        │
│          └────────┬────────┘       └────────┬────────┘        │
│                   │                         │                  │
│                   └────────────┬────────────┘                  │
│                                ▼                               │
│                    ┌─────────────────┐                         │
│                    │ Test Generation │                         │
│                    │ Agent           │                         │
│                    └────────┬────────┘                         │
│                             ▼                                  │
│                    ┌─────────────────┐                         │
│                    │ Validation      │                         │
│                    │ Agent           │                         │
│                    └────────┬────────┘                         │
│                             ▼                                  │
│                    ┌─────────────────┐                         │
│                    │ PR Report       │                         │
│                    │ Agent           │                         │
│                    └─────────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Descriptions

| Agent | Responsibility |
|-------|---------------|
| AcceptanceCriteriaAgent | Parses acceptance criteria markdown into structured checklist |
| ScanAnalysisAgent | Analyzes scan reports and classifies findings |
| SandboxPatchAgent | Applies safe patches in isolated sandbox (never touches original) |
| OSSAdvisorAgent | Flags critical OSS issues for human approval (never auto-patches) |
| TestGenerationAgent | Generates pytest unit and API tests |
| ValidationAgent | Runs pytest and captures structured results |
| PRReportAgent | Generates PR report with final recommendation |

## Key Design Decisions

1. **Sandbox isolation**: All patches happen in `.sandbox/`, never in `sample_app/`
2. **OSS safety**: OSS dependency findings are NEVER auto-patched
3. **Deterministic demo**: Works fully offline with mock Gemini responses
4. **Shared state**: Simple Python dict passed through agent sequence
5. **Extensible**: Agents extend `BaseAgent` ABC — easy to add new agents

## Future Integrations

- **Gemini AI**: Intelligent patch generation and test writing
- **Google Cloud Storage**: Upload reports and diffs for team sharing
- **BigQuery**: Store validation run history for trend analysis
- **Jenkins**: Trigger feature builds after CruiseMode validation
- **GitHub**: Auto-create PRs with suggested changes
- **RAPIDS**: Accelerate batch scan analysis
