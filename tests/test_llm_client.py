"""Unit tests: llm_client provider logic (no network)."""

import pytest

from app.core.llm_client import (
    GLMClient,
    ProviderUnavailable,
    _strip_fences,
    resolve_provider,
)


def test_no_key_raises_provider_unavailable(monkeypatch):
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    with pytest.raises(ProviderUnavailable):
        GLMClient(api_key="")


def test_resolve_provider_auto_without_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    assert resolve_provider() == "offline"


def test_resolve_provider_auto_with_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.setenv("GLM_API_KEY", "k-test")
    assert resolve_provider() == "glm"


def test_resolve_provider_explicit(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "offline")
    monkeypatch.setenv("GLM_API_KEY", "k-test")
    assert resolve_provider() == "offline"


def test_default_endpoint_config():
    monkeypatch = None  # noqa: F841 — clarity
    import os

    old = {k: os.environ.get(k) for k in ("GLM_API_KEY", "GLM_BASE_URL", "GLM_MODEL")}
    try:
        os.environ.pop("GLM_API_KEY", None)
        os.environ.pop("GLM_BASE_URL", None)
        os.environ.pop("GLM_MODEL", None)
        with pytest.raises(ProviderUnavailable):
            GLMClient()  # no key
        # construct with key only to inspect defaults
        c = GLMClient(api_key="k")
        assert c.base_url == "https://open.bigmodel.cn/api/paas/v4"
        assert c.model == "glm-4-flash"
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
    c = GLMClient(api_key="SUPERSECRET")
    r = repr(c)
    assert "SUPERSECRET" not in r
    assert "SUPERSECRET" not in str(c.__dict__.get("api_key", "")[:0])  # noqa: B018
