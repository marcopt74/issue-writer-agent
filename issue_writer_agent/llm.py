from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


Message = dict[str, str]


class LlmError(RuntimeError):
    """Raised when the model backend cannot produce a response."""


@dataclass(frozen=True)
class OpenAICompatibleClient:
    api_key: str
    model_url: str
    model_name: str
    timeout_seconds: int = 120

    def chat(self, messages: Iterable[Message], temperature: float = 0.2) -> str:
        endpoint = f"{self.model_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": list(messages),
            "temperature": temperature,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise LlmError(f"LLM request failed with HTTP {exc.code}: {error_body}") from exc
        except URLError as exc:
            raise LlmError(f"Could not reach LLM backend at {endpoint}: {exc}") from exc
        except TimeoutError as exc:
            raise LlmError(f"LLM request timed out after {self.timeout_seconds}s.") from exc

        try:
            body = json.loads(raw_body)
            return str(body["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LlmError(f"LLM backend returned an unexpected response: {raw_body}") from exc

