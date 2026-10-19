"""llm_client.py — provider abstraction for GLM (OpenAI-compatible) calls.

One public interface: GLMClient.generate(messages, schema=None, ...).

Provider selection is env-driven (LLM_PROVIDER=auto|glm|offline) and the
pipeline owns the fallback to the offline engine when ProviderUnavailable is
raised (missing key, auth failure, repeated 429s, timeouts).

Security: the API key is accepted via constructor/env only and never logged.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

MAX_JSON_RETRIES = 2  # validation retries, per challenge spec (retry up to 2 times)
MAX_RATE_LIMITS = 2  # consecutive 429s before declaring provider unavailable
TIMEOUT_S = 45.0


class LLMError(RuntimeError):
    """Base error for LLM provider failures."""


class ProviderUnavailable(LLMError):
    """Raised when the live provider cannot serve the request — pipeline
    should fall back to the offline engine."""


@dataclass
class LLMResult:
    content: str
    model: str
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    attempts: int = 1
    notes: list[str] = field(default_factory=list)


def _strip_fences(text: str) -> str:
    """Remove ```json fences some models emit despite instructions."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1] if t.count("```") >= 2 else t
        for marker in ("json", "JSON"):
            if t.lstrip().startswith(marker):
                t = t.lstrip()[len(marker):]
        t = t.strip().rstrip("`").strip()
    return t


class GLMClient:
    """OpenAI-compatible client for Zhipu / Z.ai GLM endpoints.

    Works against both https://open.bigmodel.cn/api/paas/v4 (default, free
    glm-4-flash) and https://api.z.ai/api/paas/v4 (international) — both
    expose /chat/completions in OpenAI shape.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_s: float = TIMEOUT_S,
    ) -> None:
        self.api_key = api_key or os.environ.get("GLM_API_KEY", "")
        self.base_url = (
            base_url
            or os.environ.get("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
        ).rstrip("/")
        self.model = model or os.environ.get("GLM_MODEL", "glm-4-flash")
        self.timeout_s = timeout_s
        self._consecutive_429 = 0
        if not self.api_key:
            raise ProviderUnavailable(
                "No GLM API key configured (GLM_API_KEY / constructor)."
            )
        try:
            from openai import OpenAI  # local import keeps offline mode light
        except ImportError as exc:  # pragma: no cover
            raise ProviderUnavailable(f"openai package unavailable: {exc}") from exc
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=f"{self.base_url}",
            timeout=self.timeout_s,
            max_retries=1,
        )

    # -- public API --------------------------------------------------------

    def generate(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 900,
        retry_feedback: str | None = None,
    ) -> LLMResult:
        """One completion. If `schema` is given, parse+validate JSON and retry
        (bounded, with the validation error fed back) up to MAX_JSON_RETRIES."""
        start = time.perf_counter()
        attempts = 0
        last_err: Exception | None = None
        convo = list(messages)
        while attempts <= MAX_JSON_RETRIES:
            attempts += 1
            content, usage = self._raw_chat(convo, temperature, max_tokens)
            if schema is None:
                return LLMResult(
                    content=content,
                    model=self.model,
                    latency_ms=int((time.perf_counter() - start) * 1000),
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    attempts=attempts,
                )
            try:
                parsed = json.loads(_strip_fences(content))
                schema.model_validate(parsed)
                return LLMResult(
                    content=content,
                    model=self.model,
                    latency_ms=int((time.perf_counter() - start) * 1000),
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    attempts=attempts,
                )
            except (json.JSONDecodeError, ValidationError) as exc:
                last_err = exc
                convo = list(messages) + [
                    {"role": "assistant", "content": content},
                    {
                        "role": "user",
                        "content": retry_feedback
                        or f"Your answer failed validation: {str(exc)[:400]}. "
                        "Return corrected JSON only.",
                    },
                ]
        raise LLMError(
            f"Schema validation failed after {attempts} attempts: {last_err}"
        )

    # -- internals -----------------------------------------------------------

    def _raw_chat(
        self, messages: list[dict[str, str]], temperature: float, max_tokens: int
    ) -> tuple[str, dict[str, int]]:
        from openai import APIStatusError, APIConnectionError, RateLimitError

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )
            self._consecutive_429 = 0
            content = resp.choices[0].message.content or ""
            usage = {
                "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(resp.usage, "completion_tokens", 0) or 0,
            }
            return content, usage
        except RateLimitError as exc:
            self._consecutive_429 += 1
            if self._consecutive_429 >= MAX_RATE_LIMITS:
                raise ProviderUnavailable(
                    f"Rate-limited {self._consecutive_429}x in a row: {exc}"
                ) from exc
            raise LLMError(f"Rate limited (will retry upstream): {exc}") from exc
        except APIConnectionError as exc:
            raise ProviderUnavailable(f"Cannot reach {self.base_url}: {exc}") from exc
        except APIStatusError as exc:
            status = getattr(exc, "status_code", None)
            if status in (401, 403):
                raise ProviderUnavailable(
                    f"Auth rejected (status {status}) — check GLM_API_KEY."
                ) from exc
            if status == 429:
                self._consecutive_429 += 1
                if self._consecutive_429 >= MAX_RATE_LIMITS:
                    raise ProviderUnavailable("Repeated 429s.") from exc
            if status is not None and 500 <= status < 600:
                raise LLMError(f"Provider {status}; transient.") from exc
            raise LLMError(f"Provider error {status}: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise ProviderUnavailable(f"Timeout after {self.timeout_s}s: {exc}") from exc


def provider_from_env() -> str:
    """Resolve the requested provider from LLM_PROVIDER (default auto)."""
    return (os.environ.get("LLM_PROVIDER") or "auto").strip().lower()


def glm_available(api_key: str | None = None) -> bool:
    """True if a GLM key is present (does not make a network call)."""
    return bool(api_key or os.environ.get("GLM_API_KEY"))


def resolve_provider(api_key: str | None = None) -> str:
    """auto → glm if key present else offline; explicit values pass through."""
    p = provider_from_env()
    if p == "auto":
        return "glm" if glm_available(api_key) else "offline"
    return p


__all__ = [
    "GLMClient",
    "LLMResult",
    "LLMError",
    "ProviderUnavailable",
    "resolve_provider",
    "glm_available",
    "provider_from_env",
    "Any",
]
