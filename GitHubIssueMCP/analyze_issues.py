#!/usr/bin/env python3
"""
analyze_issues.py — Local-LLM GitHub issue analyzer.

Fetches a GitHub issue (by number, or all issues touched today), runs it
through Ollama to produce a clarity score, classifies each reply, estimates
feasibility for proposed solutions, and writes JSON + HTML + text reports.

Usage:
    python3 analyze_issues.py --repo OWNER/REPO --issue N
    python3 analyze_issues.py --repo OWNER/REPO --today

Requires: `gh` CLI authenticated, and Ollama running locally.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import config
from analyzer.clarity_analyzer import ClarityAnalyzer
from analyzer.feasibility_estimator import FeasibilityEstimator
from analyzer.github_client import GitHubCLIError, GitHubClient
from analyzer.models import AnalysisReport, Issue
from analyzer.ollama_client import OllamaClient, OllamaError
from analyzer.pipeline import IssueAnalysisPipeline
from analyzer.reply_classifier import ReplyClassifier
from analyzer.reporters import default_factory


class AnalyzeIssuesApp:
    def __init__(
        self,
        github: GitHubClient,
        pipeline: IssueAnalysisPipeline,
        reporters: list,
        out_dir: Path,
    ) -> None:
        self._github = github
        self._pipeline = pipeline
        self._reporters = reporters
        self._out_dir = out_dir

    def run(self, repo: str, issue_number: int | None, use_today: bool) -> int:
        issues = self._collect_issues(repo, issue_number, use_today)
        if not issues:
            print("No issues matched the selection.", file=sys.stderr)
            return 0
        for issue in issues:
            self._analyze_and_report(issue)
        return 0

    def _collect_issues(self, repo: str, issue_number: int | None, use_today: bool) -> list[Issue]:
        if issue_number is not None:
            return [self._github.fetch_issue(repo, issue_number)]
        return self._github.fetch_todays_issues(repo)

    def _analyze_and_report(self, issue: Issue) -> None:
        print(f"→ analyzing {issue.repo}#{issue.number}: {issue.title[:80]}", file=sys.stderr)
        report = self._pipeline.analyze(issue)
        self._write_reports(report)

    def _write_reports(self, report: AnalysisReport) -> None:
        for reporter in self._reporters:
            path = reporter.write(report, self._out_dir)
            print(f"  wrote {path}", file=sys.stderr)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze GitHub issues with a local Ollama LLM.",
    )
    parser.add_argument("--repo", required=True, help="owner/repo")
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--issue", type=int, help="specific issue number")
    selection.add_argument("--today", action="store_true", help="all issues updated or created today (UTC)")
    parser.add_argument(
        "--model",
        default=os.environ.get("OLLAMA_MODEL", config.OLLAMA_MODEL),
        help=f"Ollama model name (env: OLLAMA_MODEL; default {config.OLLAMA_MODEL})",
    )
    parser.add_argument(
        "--ollama-url",
        default=os.environ.get("OLLAMA_BASE_URL", config.OLLAMA_BASE_URL),
        help=f"Ollama base URL (env: OLLAMA_BASE_URL; default {config.OLLAMA_BASE_URL})",
    )
    parser.add_argument(
        "--format",
        default="json,html,text",
        help="comma-separated reporters: json,html,text (default: all)",
    )
    parser.add_argument("--out", default="reports", help="output directory (default: reports/)")
    args = parser.parse_args(argv)

    if "/" not in args.repo:
        parser.error(f"--repo must be in owner/repo format, got: {args.repo}")
    return args


def _build_app(args: argparse.Namespace) -> AnalyzeIssuesApp:
    prompt_dir = Path(__file__).resolve().parent / "analyzer" / "prompts"
    ollama = OllamaClient(base_url=args.ollama_url, model=args.model)
    pipeline = IssueAnalysisPipeline(
        clarity=ClarityAnalyzer(ollama, prompt_dir / "clarity.txt"),
        classifier=ReplyClassifier(ollama, prompt_dir / "classification.txt"),
        feasibility=FeasibilityEstimator(ollama, prompt_dir / "feasibility.txt"),
        model_name=args.model,
    )
    factory = default_factory()
    kinds = [k.strip() for k in args.format.split(",") if k.strip()]
    reporters = factory.create_many(kinds)
    return AnalyzeIssuesApp(
        github=GitHubClient(),
        pipeline=pipeline,
        reporters=reporters,
        out_dir=Path(args.out),
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    try:
        app = _build_app(args)
        return app.run(args.repo, args.issue, args.today)
    except (GitHubCLIError, OllamaError, ValueError) as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
