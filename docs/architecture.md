# CruiseMode Architecture

## System Overview

CruiseMode is a developer-side multi-agent validation system that runs **before** Jenkins feature builds. It analyzes acceptance criteria, scan reports, patches safe issues in a sandbox, generates tests, and produces a PR readiness report.

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
