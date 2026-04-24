from __future__ import annotations

import json
import subprocess
from datetime import date, datetime, timezone

from .models import Issue, Reply


class GitHubCLIError(RuntimeError):
    pass


class GitHubClient:
    _ISSUE_FIELDS = "title,body,author,createdAt,labels,state,url,comments"

    def __init__(self, executable: str = "gh") -> None:
        self._executable = executable

    def fetch_issue(self, repo: str, number: int) -> Issue:
        payload = self._run_json([
            "issue", "view", str(number),
            "--repo", repo,
            "--json", self._ISSUE_FIELDS,
        ])
        return self._to_issue(repo, number, payload)

    def fetch_todays_issues(self, repo: str, today: date | None = None) -> list[Issue]:
        day = today or datetime.now(timezone.utc).date()
        day_str = day.isoformat()
        search = f"updated:>={day_str} OR created:>={day_str}"
        payload = self._run_json([
            "issue", "list",
            "--repo", repo,
            "--search", search,
            "--json", "number",
            "--limit", "200",
        ])
        numbers = [int(item["number"]) for item in payload]
        return [self.fetch_issue(repo, n) for n in numbers]

    def _to_issue(self, repo: str, number: int, payload: dict) -> Issue:
        replies: list[Reply] = []
        for i, comment in enumerate(payload.get("comments", []) or [], start=1):
            replies.append(Reply(
                index=i,
                author=(comment.get("author") or {}).get("login", "unknown"),
                created_at=comment.get("createdAt", ""),
                body=(comment.get("body") or "").strip(),
            ))
        labels = [lbl.get("name", "") for lbl in payload.get("labels", []) or []]
        author = (payload.get("author") or {}).get("login", "unknown")
        return Issue(
            repo=repo,
            number=number,
            url=payload.get("url", ""),
            title=payload.get("title", ""),
            body=payload.get("body") or "",
            author=author,
            created_at=payload.get("createdAt", ""),
            labels=labels,
            state=payload.get("state", ""),
            replies=replies,
        )

    def _run_json(self, args: list[str]) -> dict | list:
        raw = self._run([self._executable, *args])
        try:
            return json.loads(raw)
        except json.JSONDecodeError as err:
            raise GitHubCLIError(f"gh returned invalid JSON: {err}\n{raw[:500]}") from err

    def _run(self, cmd: list[str]) -> str:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise GitHubCLIError(result.stderr.strip() or f"gh exited {result.returncode}")
        return result.stdout.strip()
