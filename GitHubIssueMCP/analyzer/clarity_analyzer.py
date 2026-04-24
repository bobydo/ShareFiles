from __future__ import annotations

from pathlib import Path

from .models import ClarityReport, Issue
from .ollama_client import OllamaClient, OllamaError


class ClarityAnalyzer:
    _VALID_SCORE_RANGE = range(1, 11)

    def __init__(self, ollama: OllamaClient, prompt_path: Path) -> None:
        self._ollama = ollama
        self._prompt_path = prompt_path
        self._system: str | None = None

    def analyze(self, issue: Issue) -> ClarityReport:
        user = self._build_user_message(issue)
        data = self._ollama.chat_json(self._load_system(), user)
        return self._to_report(data)

    def _load_system(self) -> str:
        if self._system is None:
            self._system = self._prompt_path.read_text(encoding="utf-8")
        return self._system

    def _build_user_message(self, issue: Issue) -> str:
        labels = ", ".join(issue.labels) or "none"
        body = issue.body.strip() or "(no description provided)"
        return (
            f"Repository: {issue.repo}\n"
            f"Issue #{issue.number}: {issue.title}\n"
            f"State: {issue.state}\n"
            f"Labels: {labels}\n"
            f"\n--- ISSUE BODY ---\n{body}\n"
        )

    def _to_report(self, data: dict) -> ClarityReport:
        score = data.get("score")
        if not isinstance(score, int) or score not in self._VALID_SCORE_RANGE:
            raise OllamaError(f"clarity score out of range or not int: {score!r}")
        recs = data.get("recommendations") or []
        if not isinstance(recs, list) or not all(isinstance(r, str) for r in recs):
            raise OllamaError(f"recommendations not a list[str]: {recs!r}")
        rationale = data.get("rationale") or ""
        return ClarityReport(score=score, recommendations=recs, rationale=str(rationale))
