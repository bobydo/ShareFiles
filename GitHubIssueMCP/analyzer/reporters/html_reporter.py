from __future__ import annotations

from html import escape
from io import StringIO
from pathlib import Path

from ..models import AnalysisReport, Reply
from .base import Reporter


class HtmlReporter(Reporter):
    extension = "html"

    _CSS = """
    :root {
        --bg: #0d1117; --fg: #e6edf3; --muted: #8b949e;
        --card: #161b22; --border: #30363d;
        --ok: #3fb950; --warn: #d29922; --bad: #f85149;
        --link: #58a6ff;
    }
    * { box-sizing: border-box; }
    body { background: var(--bg); color: var(--fg); font-family: -apple-system, Segoe UI, sans-serif; margin: 0; padding: 2rem; line-height: 1.55; }
    a { color: var(--link); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .container { max-width: 960px; margin: 0 auto; }
    header.issue { border-bottom: 1px solid var(--border); padding-bottom: 1rem; margin-bottom: 1.5rem; }
    header.issue h1 { margin: 0 0 .25rem 0; font-size: 1.5rem; }
    .meta { color: var(--muted); font-size: .9rem; }
    .meta span { margin-right: 1rem; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem; margin-bottom: 1.25rem; }
    .clarity { display: flex; align-items: center; gap: 1.5rem; }
    .score-badge { font-size: 2.5rem; font-weight: 700; min-width: 4rem; text-align: center; padding: .5rem 1rem; border-radius: 8px; border: 2px solid var(--border); }
    .score-ok { border-color: var(--ok); color: var(--ok); }
    .score-warn { border-color: var(--warn); color: var(--warn); }
    .score-bad { border-color: var(--bad); color: var(--bad); }
    .clarity-body { flex: 1; }
    .clarity h2 { margin-top: 0; }
    ul.recs { margin: .25rem 0 0 1.25rem; padding: 0; }
    .body-text { white-space: pre-wrap; background: #0b0f15; border: 1px solid var(--border); padding: 1rem; border-radius: 6px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .85rem; }
    .reply { margin-bottom: 1rem; }
    .reply-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: .5rem; }
    .reply-author { font-weight: 600; }
    .reply-date { color: var(--muted); font-size: .85rem; }
    .chip { display: inline-block; padding: .15rem .6rem; border-radius: 999px; font-size: .75rem; font-weight: 600; letter-spacing: .03em; border: 1px solid var(--border); }
    .chip-sol { background: rgba(63,185,80,.15); color: var(--ok); border-color: var(--ok); }
    .chip-disc { background: rgba(139,148,158,.15); color: var(--muted); }
    .chip-low { color: var(--ok); border-color: var(--ok); }
    .chip-medium { color: var(--warn); border-color: var(--warn); }
    .chip-high { color: var(--bad); border-color: var(--bad); }
    .feasibility { margin-top: .75rem; padding: .75rem; border-left: 3px solid var(--link); background: rgba(88,166,255,.05); }
    .feasibility-row { display: flex; gap: 1rem; margin-bottom: .5rem; flex-wrap: wrap; }
    .feasibility-label { color: var(--muted); font-size: .8rem; text-transform: uppercase; margin-right: .25rem; }
    .footer { color: var(--muted); font-size: .8rem; text-align: center; margin-top: 2rem; }
    """

    def write(self, report: AnalysisReport, out_dir: Path) -> Path:
        path = self._output_path(report, out_dir)
        path.write_text(self._render(report), encoding="utf-8")
        return path

    def _render(self, report: AnalysisReport) -> str:
        issue = report.issue
        buf = StringIO()
        buf.write("<!doctype html>\n<html lang=\"en\"><head>\n")
        buf.write("<meta charset=\"utf-8\">\n")
        buf.write(f"<title>{escape(issue.repo)} #{issue.number} — {escape(issue.title)}</title>\n")
        buf.write(f"<style>{self._CSS}</style>\n</head><body><div class=\"container\">\n")

        self._render_header(buf, report)
        self._render_clarity(buf, report)
        self._render_body(buf, issue.body)
        self._render_replies(buf, issue.replies)
        buf.write(f"<div class=\"footer\">Generated {escape(report.generated_at)} · model <code>{escape(report.model)}</code></div>\n")
        buf.write("</div></body></html>\n")
        return buf.getvalue()

    def _render_header(self, buf: StringIO, report: AnalysisReport) -> None:
        issue = report.issue
        labels = ", ".join(escape(l) for l in issue.labels) or "none"
        buf.write("<header class=\"issue\">\n")
        buf.write(f"<h1>#{issue.number} — {escape(issue.title)}</h1>\n")
        buf.write("<div class=\"meta\">")
        buf.write(f"<span>repo <strong>{escape(issue.repo)}</strong></span>")
        buf.write(f"<span>state <strong>{escape(issue.state)}</strong></span>")
        buf.write(f"<span>author {escape(issue.author)}</span>")
        buf.write(f"<span>opened {escape(issue.created_at[:10])}</span>")
        buf.write(f"<span>labels {labels}</span>")
        if issue.url:
            buf.write(f"<span><a href=\"{escape(issue.url)}\" target=\"_blank\">view on GitHub</a></span>")
        buf.write("</div></header>\n")

    def _render_clarity(self, buf: StringIO, report: AnalysisReport) -> None:
        c = report.clarity
        score_class = "score-bad" if c.score <= 3 else "score-warn" if c.score <= 6 else "score-ok"
        buf.write("<section class=\"card clarity\">\n")
        buf.write(f"<div class=\"score-badge {score_class}\">{c.score}<span style=\"font-size:1rem;\">/10</span></div>\n")
        buf.write("<div class=\"clarity-body\">\n<h2>Requirement clarity</h2>\n")
        buf.write(f"<p>{escape(c.rationale)}</p>\n")
        if c.recommendations:
            buf.write("<strong>Recommendations</strong><ul class=\"recs\">\n")
            for rec in c.recommendations:
                buf.write(f"<li>{escape(rec)}</li>\n")
            buf.write("</ul>\n")
        buf.write("</div></section>\n")

    def _render_body(self, buf: StringIO, body: str) -> None:
        buf.write("<section class=\"card\"><h2>Issue body</h2>\n")
        buf.write(f"<div class=\"body-text\">{escape(body or '(no description provided)')}</div>\n")
        buf.write("</section>\n")

    def _render_replies(self, buf: StringIO, replies: list[Reply]) -> None:
        buf.write(f"<section class=\"card\"><h2>Replies ({len(replies)})</h2>\n")
        if not replies:
            buf.write("<p class=\"meta\">No replies yet.</p></section>\n")
            return
        for reply in replies:
            self._render_reply(buf, reply)
        buf.write("</section>\n")

    def _render_reply(self, buf: StringIO, reply: Reply) -> None:
        chip_class, chip_label = self._classification_chip(reply)
        buf.write("<div class=\"reply\">\n")
        buf.write("<div class=\"reply-head\">\n")
        buf.write(
            f"<div><span class=\"reply-author\">{escape(reply.author)}</span> "
            f"<span class=\"reply-date\">· #{reply.index} · {escape(reply.created_at[:10])}</span></div>\n"
        )
        buf.write(f"<span class=\"chip {chip_class}\">{chip_label}</span>\n</div>\n")
        buf.write(f"<div class=\"body-text\">{escape(reply.body)}</div>\n")
        if reply.feasibility:
            self._render_feasibility(buf, reply)
        buf.write("</div>\n")

    def _classification_chip(self, reply: Reply) -> tuple[str, str]:
        if reply.classification == "proposed_solution":
            return "chip-sol", "proposed solution"
        if reply.classification == "discussion":
            return "chip-disc", "discussion"
        return "chip-disc", "unclassified"

    def _render_feasibility(self, buf: StringIO, reply: Reply) -> None:
        f = reply.feasibility
        assert f is not None
        buf.write("<div class=\"feasibility\">\n<div class=\"feasibility-row\">\n")
        buf.write(f"<span><span class=\"feasibility-label\">complexity</span><span class=\"chip chip-{escape(f.complexity)}\">{escape(f.complexity)}</span></span>\n")
        buf.write(f"<span><span class=\"feasibility-label\">effort</span>{escape(f.effort)}</span>\n")
        buf.write(f"<span><span class=\"feasibility-label\">risk</span><span class=\"chip chip-{escape(f.risk)}\">{escape(f.risk)}</span></span>\n")
        buf.write("</div>\n")
        buf.write(f"<div>{escape(f.rationale)}</div>\n</div>\n")
