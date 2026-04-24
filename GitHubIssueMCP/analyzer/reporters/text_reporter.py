from __future__ import annotations

from io import StringIO
from pathlib import Path

from ..models import AnalysisReport, Reply
from .base import Reporter


class TextLogReporter(Reporter):
    extension = "txt"

    def write(self, report: AnalysisReport, out_dir: Path) -> Path:
        path = self._output_path(report, out_dir)
        path.write_text(self._render(report), encoding="utf-8")
        return path

    def _render(self, report: AnalysisReport) -> str:
        buf = StringIO()
        issue = report.issue
        buf.write("=" * 70 + "\n")
        buf.write(f"REPO:    {issue.repo}\n")
        buf.write(f"ISSUE:   #{issue.number}  [{issue.state}]\n")
        buf.write(f"URL:     {issue.url}\n")
        buf.write(f"AUTHOR:  {issue.author}  ({issue.created_at[:10]})\n")
        buf.write(f"LABELS:  {', '.join(issue.labels) or 'none'}\n")
        buf.write(f"MODEL:   {report.model}\n")
        buf.write(f"RUN AT:  {report.generated_at}\n")
        buf.write("=" * 70 + "\n\n")

        buf.write("── CLARITY ─────────────────────────────────────────────────────────\n")
        buf.write(f"Score: {report.clarity.score}/10\n")
        buf.write(f"Rationale: {report.clarity.rationale}\n")
        buf.write("Recommendations:\n")
        for rec in report.clarity.recommendations:
            buf.write(f"  - {rec}\n")
        buf.write("\n")

        buf.write("── ISSUE BODY ──────────────────────────────────────────────────────\n")
        buf.write((issue.body or "(no description provided)") + "\n\n")

        if not issue.replies:
            buf.write("── REPLIES ─────────────────────────────────────────────────────────\n")
            buf.write("(no replies)\n")
            return buf.getvalue()

        buf.write(f"── REPLIES ({len(issue.replies)}) ───────────────────────────────────────────\n\n")
        for reply in issue.replies:
            self._render_reply(buf, reply)
        return buf.getvalue()

    def _render_reply(self, buf: StringIO, reply: Reply) -> None:
        tag = (reply.classification or "unclassified").upper()
        buf.write(f"[Reply {reply.index}] {reply.author} — {reply.created_at[:10]}  <{tag}>\n")
        buf.write("-" * 60 + "\n")
        buf.write(reply.body + "\n")
        if reply.feasibility:
            f = reply.feasibility
            buf.write("\n  FEASIBILITY:\n")
            buf.write(f"    complexity: {f.complexity}\n")
            buf.write(f"    effort:     {f.effort}\n")
            buf.write(f"    risk:       {f.risk}\n")
            buf.write(f"    rationale:  {f.rationale}\n")
        buf.write("\n")
