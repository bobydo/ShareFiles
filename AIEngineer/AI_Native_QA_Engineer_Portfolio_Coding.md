# AI_Native_QA_Engineer_Portfolio.md

> **Document Standard**
>
> This document is the **single source of truth** for the AI Native QA
> Engineer portfolio project.
>
> It is written for: 1. Human readers 2. Interviewers 3. Claude Code /
> Codex / Gemini CLI
>
> The document is **append-only**. Existing sections should not be
> removed; new sections are added over time.

------------------------------------------------------------------------

# Documentation Style Guide

## Philosophy

Prefer visual workflows over long paragraphs.

Use diagrams whenever possible.

The goal is for someone to understand a feature within 30 seconds.

------------------------------------------------------------------------

# Preferred Formats

## 1. Workflow

Use arrow diagrams.

``` text
Jira Ticket
      │
      ▼
Requirement Agent
      │
      ├── Read Summary
      ├── Read Description
      ├── Read Acceptance Criteria
      └── Read Attachments
      │
      ▼
Requirement Analysis
      │
      ▼
Coverage Agent
      │
      ▼
Automation Agent
      │
      ▼
Execution Agent
      │
      ▼
Reporting Agent
```

------------------------------------------------------------------------

## 2. Architecture

``` text
                 User
                   │
                   ▼
            Streamlit UI
                   │
                   ▼
       LangGraph Orchestrator
                   │
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
Requirement   Knowledge     Execution
    Agent        Agent          Agent
     │             │             │
     ▼             ▼             ▼
 Jira API      Qdrant RAG   Playwright
     │             │             │
     ▼             ▼             ▼
  SQLite      Confluence   GitHub Actions
```

------------------------------------------------------------------------

## 3. Repository Structure

``` text
qa-copilot/
│
├── agents/
├── tools/
├── integrations/
├── prompts/
├── memory/
├── evaluation/
├── ui/
├── tests/
├── docker/
└── docs/
```

------------------------------------------------------------------------

## 4. Horizontal Tables

  Component    Purpose
  ------------ ------------------------
  Jira         Read and update issues
  Xray         Test management
  Playwright   UI automation
  LangGraph    Agent orchestration
  Qdrant       Vector search

------------------------------------------------------------------------

## 5. Sprint Layout

Every sprint should follow this structure.

``` text
Sprint X
      │
      ▼
Goal
      │
      ▼
Tasks
      ├── Task 1
      ├── Task 2
      ├── Task 3
      └── Task 4
      │
      ▼
Deliverables
      ├── Source files
      ├── Tests
      ├── Documentation
      └── Demo
      │
      ▼
Acceptance Criteria
      │
      ▼
Claude Code Prompt
```

------------------------------------------------------------------------

# Claude Code Friendly Sections

Every implementation chapter should include:

  Section               Required
  --------------------- ----------
  Goal                  ✅
  Inputs                ✅
  Outputs               ✅
  Workflow              ✅
  Folder Structure      ✅
  Dependencies          ✅
  Classes               ✅
  Interfaces            ✅
  Error Handling        ✅
  Acceptance Criteria   ✅
  Unit Tests            ✅
  Integration Tests     ✅
  Future Improvements   ✅
  Claude Code Prompt    ✅

------------------------------------------------------------------------

# Horizontal Before Vertical

Prefer compact tables when descriptions are short.

Example:

  Agent         Responsibility    Output
  ------------- ----------------- ---------------------
  Requirement   Parse Jira        RequirementAnalysis
  Coverage      Coverage Matrix   CoverageReport
  Risk          Risk Score        RiskAssessment
  Execution     Run Tests         TestResult

Use bullet lists only when explanations are long.

------------------------------------------------------------------------

# Mermaid Support

Whenever possible, provide both:

-   ASCII diagram
-   Mermaid diagram

This improves readability on GitHub while remaining AI-friendly.

------------------------------------------------------------------------

# Rule

Do NOT replace existing sections.

Do NOT rename this document.

Always append new sections.

Filename must remain:

AI_Native_QA_Engineer_Portfolio.md
