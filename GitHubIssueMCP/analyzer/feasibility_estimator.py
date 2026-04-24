from __future__ import annotations

from pathlib import Path
from typing import get_args

from .models import FeasibilityReport, Issue, Reply, Severity
from .ollama_client import OllamaClient, OllamaError


class FeasibilityEstimator:
    _VALID_SEVERITY = set(get_args(Severity))

    def __init__(self, ollama: OllamaClient, prompt_path: Path) -> None:
        self._ollama = ollama
        self._prompt_path = prompt_path
        self._system: str | None = None

    def estimate(self, reply: Reply, issue: Issue) -> FeasibilityReport:
        data = self._ollama.chat_json(
            self._load_system(),
            self._build_user_message(reply, issue),
        )
        return self._to_report(data)

    def _load_system(self) -> str:
        if self._system is None:
            self._system = self._prompt_path.read_text(encoding="utf-8")
        return self._system

    def _build_user_message(self, reply: Reply, issue: Issue) -> str:
        labels = ", ".join(issue.labels) or "none"
        issue_body = issue.body.strip() or "(no description provided)"
        proposal = reply.body.strip() or "(empty reply)"
        return (
            f"Repository: {issue.repo}\n"
            f"Issue #{issue.number}: {issue.title}\n"
            f"Labels: {labels}\n"
            f"\n--- ISSUE BODY ---\n{issue_body}\n"
            f"\n--- PROPOSED SOLUTION (reply #{reply.index} by {reply.author}) ---\n"
            f"{proposal}\n"
        )

    def _to_report(self, data: dict) -> FeasibilityReport:
        complexity = data.get("complexity")
        risk = data.get("risk")
        effort = data.get("effort")
        rationale = data.get("rationale") or ""
        if complexity not in self._VALID_SEVERITY:
            raise OllamaError(f"invalid complexity: {complexity!r}")
        if risk not in self._VALID_SEVERITY:
            raise OllamaError(f"invalid risk: {risk!r}")
        if not isinstance(effort, str) or not effort.strip():
            raise OllamaError(f"effort must be a non-empty string: {effort!r}")
        return FeasibilityReport(
            complexity=complexity,  # type: ignore[arg-type]
            effort=effort.strip(),
            risk=risk,  # type: ignore[arg-type]
            rationale=str(rationale),
        )
