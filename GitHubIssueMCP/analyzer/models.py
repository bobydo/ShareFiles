from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Classification = Literal["discussion", "proposed_solution"]
Severity = Literal["low", "medium", "high"]


@dataclass
class FeasibilityReport:
    complexity: Severity
    effort: str
    risk: Severity
    rationale: str


@dataclass
class Reply:
    index: int
    author: str
    created_at: str
    body: str
    classification: Classification | None = None
    feasibility: FeasibilityReport | None = None


@dataclass
class Issue:
    repo: str
    number: int
    url: str
    title: str
    body: str
    author: str
    created_at: str
    labels: list[str]
    state: str
    replies: list[Reply] = field(default_factory=list)


@dataclass
class ClarityReport:
    score: int
    recommendations: list[str]
    rationale: str


@dataclass
class AnalysisReport:
    issue: Issue
    clarity: ClarityReport
    generated_at: str
    model: str
