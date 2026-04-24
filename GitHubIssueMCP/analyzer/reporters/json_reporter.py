from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ..models import AnalysisReport
from .base import Reporter


class JsonReporter(Reporter):
    extension = "json"

    def write(self, report: AnalysisReport, out_dir: Path) -> Path:
        path = self._output_path(report, out_dir)
        path.write_text(
            json.dumps(asdict(report), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path
