from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from ..models import AnalysisReport


class Reporter(ABC):
    extension: str = ""

    @abstractmethod
    def write(self, report: AnalysisReport, out_dir: Path) -> Path:
        raise NotImplementedError

    def _output_path(self, report: AnalysisReport, out_dir: Path) -> Path:
        safe_repo = report.issue.repo.replace("/", "_")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_repo}_{report.issue.number}_{stamp}.{self.extension}"
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / filename


class ReporterFactory:
    def __init__(self) -> None:
        self._registry: dict[str, type[Reporter]] = {}

    def register(self, kind: str, cls: type[Reporter]) -> None:
        self._registry[kind] = cls

    def create(self, kind: str) -> Reporter:
        try:
            return self._registry[kind]()
        except KeyError as err:
            known = ", ".join(sorted(self._registry)) or "(none registered)"
            raise ValueError(f"unknown reporter kind: {kind!r}; known: {known}") from err

    def create_many(self, kinds: list[str]) -> list[Reporter]:
        return [self.create(k) for k in kinds]
