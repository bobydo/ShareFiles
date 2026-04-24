from __future__ import annotations

from pathlib import Path
from typing import get_args

from .models import Classification, Reply
from .ollama_client import OllamaClient, OllamaError


class ReplyClassifier:
    _VALID = set(get_args(Classification))

    def __init__(self, ollama: OllamaClient, prompt_path: Path) -> None:
        self._ollama = ollama
        self._prompt_path = prompt_path
        self._system: str | None = None

    def classify(self, reply: Reply, issue_title: str) -> Classification:
        data = self._ollama.chat_json(
            self._load_system(),
            self._build_user_message(reply, issue_title),
        )
        label = data.get("classification")
        if label not in self._VALID:
            raise OllamaError(f"invalid classification label: {label!r}")
        return label  # type: ignore[return-value]

    def _load_system(self) -> str:
        if self._system is None:
            self._system = self._prompt_path.read_text(encoding="utf-8")
        return self._system

    def _build_user_message(self, reply: Reply, issue_title: str) -> str:
        body = reply.body.strip() or "(empty reply)"
        return (
            f"Issue title: {issue_title}\n"
            f"Reply #{reply.index} by {reply.author} on {reply.created_at[:10]}:\n"
            f"---\n{body}\n---\n"
        )
