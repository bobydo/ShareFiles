from __future__ import annotations

from datetime import datetime, timezone

from .clarity_analyzer import ClarityAnalyzer
from .feasibility_estimator import FeasibilityEstimator
from .models import AnalysisReport, Issue
from .reply_classifier import ReplyClassifier


class IssueAnalysisPipeline:
    def __init__(
        self,
        clarity: ClarityAnalyzer,
        classifier: ReplyClassifier,
        feasibility: FeasibilityEstimator,
        model_name: str,
    ) -> None:
        self._clarity = clarity
        self._classifier = classifier
        self._feasibility = feasibility
        self._model_name = model_name

    def analyze(self, issue: Issue) -> AnalysisReport:
        clarity = self._clarity.analyze(issue)
        for reply in issue.replies:
            reply.classification = self._classifier.classify(reply, issue.title)
            if reply.classification == "proposed_solution":
                reply.feasibility = self._feasibility.estimate(reply, issue)
        return AnalysisReport(
            issue=issue,
            clarity=clarity,
            generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            model=self._model_name,
        )
