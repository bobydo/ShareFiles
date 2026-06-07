# Discussion: EA-Style QA Copilot Project

## Microsoft Recommendation (source idea)

Build a portfolio project to target AI Engineer roles, framed as:

**Enterprise QA Copilot — Multi-Agent LangGraph + Semantic Kernel Platform**
> Built an AI copilot integrating Jira, test management systems, vector search,
> memory management, evaluation pipelines, and role-based guardrails.

### Architecture

```
User
 ↓
LangGraph Orchestrator
 ↓
Test Agent / Bug Agent / Knowledge Agent
 ↓
Jira / TestRail / Confluence / Qdrant
 ↓
Response
```

### Features
- **Ask:** e.g. "Show failed tests from Sprint 24"
- **Agent flow:** reads test data → queries Jira → retrieves documentation → produces summary
- **Memory:** stores user preferences, stores previous investigations
- **Evaluation:** Langfuse tracing, user feedback scores
- **Guardrails:** RBAC, prompt injection detection, audit logging

### Suggested time allocation (40-60 hrs)
- 10 hrs Semantic Kernel
- 10 hrs LangGraph
- 40 hrs building the QA Copilot

## My take

The architecture maps closely onto what enterprise AI engineering job descriptions
ask for, and calling out guardrails/evaluation explicitly (Langfuse, RBAC,
prompt-injection detection) signals production maturity most portfolio projects skip.

**Main tradeoff:** building real integrations against four external systems
(Jira, TestRail, Confluence, Qdrant) plus a full eval pipeline plus guardrails is
a lot of shallow surface area for 40-60 hours. Better to mock/stub 2-3 of the
integrations (keep Jira + Qdrant real, fake TestRail/Confluence with seeded data)
and spend the saved time going deep on the multi-agent orchestration and
evaluation loop — that's the part that actually differentiates "I called an LLM"
from "I built a platform."

## Next steps (when ready)
- Scaffold the AIEngineer folder structure
- Sketch agent/tool interfaces (Test Agent, Bug Agent, Knowledge Agent)
- Decide which integrations are real vs. stubbed
