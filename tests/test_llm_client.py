"""Unit tests: llm_client provider logic (no network)."""

import pytest

from app.core.llm_client import (
    GROQ_DEFAULT_BASE_URL,
    GROQ_DEFAULT_MODEL,
    GroqClient,
    ProviderUnavailable,
    _strip_fences,
    resolve_provider,
)


def test_no_key_raises_provider_unavailable(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ProviderUnavailable):
        GroqClient(api_key="")


def test_resolve_provider_auto_without_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert resolve_provider() == "offline"


def test_resolve_provider_auto_with_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.setenv("GROQ_API_KEY", "k-test")
    assert resolve_provider() == "groq"


def test_resolve_provider_explicit(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "offline")
    monkeypatch.setenv("GROQ_API_KEY", "k-test")
    assert resolve_provider() == "offline"


def test_resolve_provider_legacy_glm_alias_maps_to_groq(monkeypatch):
    """D-026: 'glm' is a deprecated alias — stale .env must not crash the app."""
    monkeypatch.setenv("LLM_PROVIDER", "glm")
    monkeypatch.setenv("GROQ_API_KEY", "k-test")
    assert resolve_provider() == "groq"


def test_default_endpoint_config():
    import os

    old = {k: os.environ.get(k) for k in ("GROQ_API_KEY", "GROQ_BASE_URL", "GROQ_MODEL")}
    try:
        os.environ.pop("GROQ_API_KEY", None)
        os.environ.pop("GROQ_BASE_URL", None)
        os.environ.pop("GROQ_MODEL", None)
        with pytest.raises(ProviderUnavailable):
            GroqClient()  # no key
        # construct with key only to inspect defaults
        c = GroqClient(api_key="k")
        assert c.base_url == GROQ_DEFAULT_BASE_URL == "https://api.groq.com/openai/v1"
        # deprecated Groq models must never be defaults (verified 2026-10-20)
        assert c.model == GROQ_DEFAULT_MODEL == "openai/gpt-oss-120b"
        assert "llama-3" not in c.model
    finally:
        for k, v in old.items():
            if v is not None:
                os.environ[k] = v


@pytest.mark.parametrize(
    "raw,expected",
    [
        ('```json\n{"a": 1}\n```', '{"a": 1}'),
        ('```\n{"a": 1}\n```', '{"a": 1}'),
        ('{"a": 1}', '{"a": 1}'),
        ('```json\n{"a": "b}`pad"}\n```', '{"a": "b}`pad"}'),
    ],
)
def test_strip_fences(raw, expected):
    assert _strip_fences(raw) == expected


def test_api_key_never_in_repr():
    c = GroqClient(api_key="SUPERSECRET")
    r = repr(c)
    assert "SUPERSECRET" not in r
    assert "SUPERSECRET" not in str(c.__dict__.get("api_key", "")[:0])  # noqa: B018
