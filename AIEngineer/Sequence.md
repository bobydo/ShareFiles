# Sequence: Building the QA Copilot

Build order, frameworks per phase, and the client-style requirements each phase
should satisfy. Sequenced so the agent core works end-to-end early, then
eval/guardrails/UI layer on top — see [[Discussion]] for the why behind this order.

## Example target run
- Repository: bobydo/ShareFiles (Share files)
- Contact email: baoshenyi@gmail.com
- Goal: use the QA copilot workflow to intake a ticket, search for similar
  requirements, clarify gaps, create or link Xray tests, and help with test
  scripts for this project.
- If Git commit fails due to missing identity, set it with:
  - `git config --global user.name "bobydo"`
  - `git config --global user.email baoshenyi@gmail.com`

## Step-by-step workflow for a Jira ticket

This is the core operating flow the QA copilot should support from ticket intake
to test execution.

1. Receive and parse the Jira ticket
   - Read the summary, description, acceptance criteria, labels, linked issues,
     and any attachments.
2. Search for similar requirements in Jira
   - Find related tickets, past bugs, and prior implementations to reuse patterns
     and avoid missed expectations.
3. Clarify unclear or missing requirements
   - Flag gaps, ambiguous acceptance criteria, and open questions for follow-up
     with the product owner, developer, or QA lead.
4. Link or create the test in Xray
   - Create a test case in Xray when the ticket needs new coverage, or link the
     ticket to an existing test case when one already exists.
5. Pick up an existing test case or create a new one
   - Prefer reusing a matching test case; otherwise create a new one with clear
     coverage and traceability back to the ticket.
6. Help create or refine test scripts
   - Support manual test steps, automation outlines, or new automated test
     scripts for the scenario.
7. Execute and track results
   - Run the test, capture evidence, log defects if needed, and update the ticket
     and Xray test status.
8. Summarize and hand off
   - Provide a concise result summary, any blockers, and recommended next steps.

## Phase 0 — Setup (2-4 hrs)
- Frameworks: Python, LangGraph, Semantic Kernel (just enough to compare the two)
- Steps:
  - Stand up a minimal LangGraph "hello world" graph (single node, single tool call)
  - Repeat the same flow in Semantic Kernel to compare DX/mental model
  - Pick one as primary orchestrator for the project (recommendation: LangGraph —
    better fit for explicit multi-agent graphs)
- Client requirement addressed: "Can you justify framework choices, not just use them?"

## Phase 1 — Core Agent Loop (10-14 hrs)
- Frameworks: LangGraph, OpenAI/Anthropic SDK, a single mocked data source
- Steps:
  - Build the orchestrator graph with one agent (Test Agent) and one stubbed tool
    (fake "Sprint 24 failed tests" dataset as JSON)
  - Get a full request → tool call → summarized response loop working via CLI
  - Add the Bug Agent and Knowledge Agent as additional graph nodes
- Client requirement addressed: "Show me the agent reasoning over real workflow data,
  not just chatting"

## Phase 2 — Real Integrations (8-12 hrs)
- Frameworks: Jira REST API (or Atlassian MCP server), Qdrant client
- Steps:
  - Wire the Test Agent to a real Jira project (read-only: search issues/sprints)
  - Stand up Qdrant locally (docker), embed a small Confluence/TestRail-style
    doc set, wire Knowledge Agent to retrieve from it
  - Stub TestRail/Confluence behind the same interface (Adapter pattern) so they
    can later be swapped for real APIs without touching agent logic
- Client requirement addressed: "Does it work against live enterprise systems,
  or only canned demos?"

## Phase 3 — Memory & Evaluation (6-10 hrs)
- Frameworks: Langfuse, a simple key-value or SQLite store for memory
- Steps:
  - Add session memory: store user preferences + prior investigation summaries
  - Wire Langfuse tracing around every agent step (latency, token cost, tool calls)
  - Add a lightweight feedback capture (thumbs up/down on each response, logged
    alongside the trace)
- Client requirement addressed: "How do you know the copilot is actually helping,
  and how do you improve it over time?"

## Phase 4 — Guardrails (4-8 hrs)
- Frameworks: simple RBAC middleware (role → allowed tools/data scopes), a
  prompt-injection check (regex/heuristic pass or a small classifier), structured
  audit log (JSON lines to file or SQLite)
- Steps:
  - Add a Chain-of-Responsibility-style middleware chain: auth → RBAC check →
    injection check → agent call → audit log
  - Demonstrate a blocked scenario (wrong role tries to query Jira data it
    shouldn't see; injected prompt gets flagged)
- Client requirement addressed: "Enterprise security/compliance sign-off —
  can this be trusted with real data?"

## Phase 5 — Thin UI + Demo Polish (4-8 hrs, last)
- Frameworks: Streamlit or Gradio (not React — see [[Discussion]] on why a thin
  UI beats a frontend build here)
- Steps:
  - Wrap the CLI flow in a simple chat UI: input box, streamed response, trace
    link (Langfuse), feedback buttons
  - Record a 2-3 minute demo video/GIF for the README
  - Optional: deploy to Hugging Face Spaces / Render free tier for a live link
- Client requirement addressed: "Can a non-technical stakeholder actually use
  and evaluate this?"

## Running totals
- Core build (Phases 0-3): ~26-40 hrs — this is the part that must not be skipped
- Guardrails + UI (Phases 4-5): ~8-16 hrs — sequenced last so they layer onto a
  working core rather than gating it

## Open questions to revisit during build
- Real vs. stubbed TestRail/Confluence — revisit after Phase 2 once real Jira
  integration effort is known
- LangGraph vs. Semantic Kernel as primary — lock in after Phase 0 comparison
- Whether RBAC needs to be "real" (actual auth) or simulated (role passed as a
  param) for portfolio purposes — simulated is fine, call it out explicitly in README
