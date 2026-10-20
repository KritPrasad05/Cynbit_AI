"""llm_client.py — provider abstraction for Groq (OpenAI-compatible) calls.

One public interface: GroqClient.generate(messages, schema=None, ...).

Provider selection is env-driven (LLM_PROVIDER=auto|groq|offline) and the
pipeline owns the fallback to the offline engine when ProviderUnavailable is
raised (missing key, auth failure, repeated 429s, timeouts).

Groq facts verified 2026-10-20 (decision.md D-026):
- Endpoint: https://api.groq.com/openai/v1 (OpenAI-compatible /chat/completions).
- Production text models: openai/gpt-oss-120b (default) and openai/gpt-oss-20b.
  NOTE: llama-3.1-8b-instant and llama-3.3-70b-versatile were deprecated on
  2026-08-16 — do NOT hardcode them (https://console.groq.com/docs/deprecations).
- Free-tier limits (per model): 30 RPM, 1K RPD, 8K TPM, 200K TPD
  (https://console.groq.com/docs/rate-limits).
- JSON mode: response_format {"type": "json_object"} — the word "JSON" must
  appear in the prompt; our prompts always demand JSON output.

History: this client previously targeted Zhipu/Z.ai GLM. It was migrated to
Groq on user instruction (decision.md D-026). "glm" is still accepted as a
deprecated LLM_PROVIDER alias for "groq" so stale .env files fail loudly
elsewhere but not here.

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

GROQ_DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_DEFAULT_MODEL = "openai/gpt-oss-120b"  # verified production model, 2026-10-20


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


class GroqClient:
    """OpenAI-compatible client for the Groq API (https://api.groq.com).

    Works with any Groq chat model; defaults to openai/gpt-oss-120b. JSON
    mode is requested whenever a schema is supplied, and gpt-oss models get
    a low reasoning effort to keep demo latency and token spend small. If
    the endpoint rejects an optional parameter, the call is retried once
    without the optional params (never without auth).
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_s: float = TIMEOUT_S,
    ) -> None:
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        self.base_url = (
            base_url
            or os.environ.get("GROQ_BASE_URL", GROQ_DEFAULT_BASE_URL)
        ).rstrip("/")
        self.model = model or os.environ.get("GROQ_MODEL", GROQ_DEFAULT_MODEL)
        self.timeout_s = timeout_s
        self._consecutive_429 = 0
        if not self.api_key:
            raise ProviderUnavailable(
                "No Groq API key configured (GROQ_API_KEY / constructor). "
                "Get a free key at https://console.groq.com/keys."
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
        max_tokens: int = 1500,
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
            content, usage = self._raw_chat(
                convo, temperature, max_tokens, json_mode=schema is not None
            )
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
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        json_mode: bool = False,
    ) -> tuple[str, dict[str, int]]:
        from openai import APIStatusError, APIConnectionError, RateLimitError

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if "gpt-oss" in self.model:
            # low reasoning keeps 2-call pipeline latency + token spend small
            kwargs["extra_body"] = {"reasoning_effort": "low"}

        try:
            resp = self._client.chat.completions.create(**kwargs)
            self._consecutive_429 = 0
            content = resp.choices[0].message.content or ""
            usage = {
                "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(resp.usage, "completion_tokens", 0) or 0,
            }
            return content, usage
        except APIStatusError as exc:
            status = getattr(exc, "status_code", None)
            msg = str(exc)
            # Some models/endpoints reject response_format or reasoning_effort —
            # retry once with the plain call before giving up.
            if status == 400 and any(
                p in msg for p in ("response_format", "reasoning_effort", "json_object")
            ):
                kwargs.pop("response_format", None)
                kwargs.pop("extra_body", None)
                try:
                    resp = self._client.chat.completions.create(**kwargs)
                    self._consecutive_429 = 0
                    content = resp.choices[0].message.content or ""
                    usage = {
                        "prompt_tokens": getattr(resp.usage, "prompt_tokens", 0) or 0,
                        "completion_tokens": getattr(resp.usage, "completion_tokens", 0) or 0,
                    }
                    return content, usage
                except APIStatusError as exc2:
                    exc = exc2
                    status = getattr(exc2, "status_code", None)
                    msg = str(exc2)
            if status in (401, 403):
                raise ProviderUnavailable(
                    f"Auth rejected (status {status}) — check GROQ_API_KEY."
                ) from exc
            if status == 429:
                self._consecutive_429 += 1
                if self._consecutive_429 >= MAX_RATE_LIMITS:
                    raise ProviderUnavailable(
                        f"Rate-limited {self._consecutive_429}x in a row (Groq free tier: "
                        "30 RPM / 1K RPD per model)."
                    ) from exc
                raise LLMError(f"Rate limited (will retry upstream): {exc}") from exc
            if status is not None and 500 <= status < 600:
                raise LLMError(f"Provider {status}; transient.") from exc
            raise LLMError(f"Provider error {status}: {msg[:200]}") from exc
        except RateLimitError as exc:
            self._consecutive_429 += 1
            if self._consecutive_429 >= MAX_RATE_LIMITS:
                raise ProviderUnavailable(
                    f"Rate-limited {self._consecutive_429}x in a row: {exc}"
                ) from exc
            raise LLMError(f"Rate limited (will retry upstream): {exc}") from exc
        except APIConnectionError as exc:
            raise ProviderUnavailable(f"Cannot reach {self.base_url}: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise ProviderUnavailable(f"Timeout after {self.timeout_s}s: {exc}") from exc


def provider_from_env() -> str:
    """Resolve the requested provider from LLM_PROVIDER (default auto).

    "glm" is a deprecated alias for "groq" (provider migration, D-026)."""
    p = (os.environ.get("LLM_PROVIDER") or "auto").strip().lower()
    return {"glm": "groq"}.get(p, p)


def groq_available(api_key: str | None = None) -> bool:
    """True if a Groq key is present (does not make a network call)."""
    return bool(api_key or os.environ.get("GROQ_API_KEY"))


def resolve_provider(api_key: str | None = None) -> str:
    """auto → groq if key present else offline; explicit values pass through."""
    p = provider_from_env()
    if p == "auto":
        return "groq" if groq_available(api_key) else "offline"
    return p


__all__ = [
    "GroqClient",
    "LLMResult",
    "LLMError",
    "ProviderUnavailable",
    "resolve_provider",
    "groq_available",
    "provider_from_env",
    "GROQ_DEFAULT_BASE_URL",
    "GROQ_DEFAULT_MODEL",
    "Any",
]
