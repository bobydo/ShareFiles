from __future__ import annotations

import json
import urllib.error
import urllib.request

from config import OLLAMA_BASE_URL, OLLAMA_MODEL


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        timeout: int = 120,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    @property
    def model(self) -> str:
        return self._model

    def chat_json(self, system: str, user: str) -> dict:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "stream": False,
        }

        raw = self._chat(payload)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            retry = self._chat(payload)
            try:
                return json.loads(retry)
            except json.JSONDecodeError as err:
                raise OllamaError(
                    f"model did not return valid JSON after one retry: {err}\n"
                    f"raw response: {retry[:1000]}"
                ) from err

    def _chat(self, payload: dict) -> str:
        data = self._post("/v1/chat/completions", payload)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as err:
            raise OllamaError(f"unexpected response shape: {data}") from err

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self._base_url}{path}"
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as err:
            raise OllamaError(f"cannot reach Ollama at {url}: {err}") from err
