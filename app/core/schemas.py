"""schemas.py — Pydantic models for every structured output in the pipeline.

All LLM outputs and offline-engine outputs conform to these models; validation
failures trigger the bounded retry loop in the pipeline (max 2 retries with the
validation error fed back to the model).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

SERVICE_IDS = Literal["ai_automation", "software_dev", "cloud", "seo_marketing"]
SCHEMA_VERSION = "1.2"

# ---------------------------------------------------------------------------
# Step outputs
# ---------------------------------------------------------------------------


class SanitizationResult(BaseModel):
    """Output of step 1 — pure-Python sanitizer (no LLM involved)."""

    pii_masked: bool = False
    pii_types: list[str] = Field(default_factory=list)
    injection_suspected: bool = False
    injection_patterns: list[str] = Field(default_factory=list)
    language: Literal["english", "hinglish", "other"] = "english"
    length_chars: int = 0
    warnings: list[str] = Field(default_factory=list)
    sanitized_text: str = ""
    delimited_text: str = ""
    note_for_model: str = ""


class ServiceMatch(BaseModel):
    """One matched Cynbit service line, grounded in the public catalog."""

    service_id: SERVICE_IDS
    service_name: str
    fit: Literal["primary", "secondary"] = "primary"
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = ""
    source_url: str = ""

    @field_validator("confidence")
    @classmethod
    def _round_conf(cls, v: float) -> float:
        return round(float(v), 2)


class Extraction(BaseModel):
    """Structured facts lifted from the inquiry (nullable = not stated)."""

    goal: str | None = None
    deliverables: list[str] = Field(default_factory=list)
    industry: str | None = None
    budget_signal: str | None = None
    timeline_signal: str | None = None
    tech_constraints: list[str] = Field(default_factory=list)
    communication_language: Literal["english", "hinglish", "other"] = "english"


class Estimate(BaseModel):
    """Deterministic complexity/effort estimate (rules-based by design)."""

    complexity: Literal["S", "M", "L"]
    complexity_rationale: str
    effort_range_weeks: list[int] = Field(min_length=2, max_length=2)
    confidence: Literal["high", "medium", "low"]
    needs_human_review: bool = True
    disclaimer: str = "Draft heuristic banding for triage only — not a quote."


class RiskFlag(BaseModel):
    risk: str
    severity: Literal["low", "medium", "high"]
    mitigation: str


class ClarifyingQuestion(BaseModel):
    question: str
    priority: Literal["must_ask", "should_ask", "nice_to_have"]
    why: str


class NextStep(BaseModel):
    step: str
    owner: str
    when: str


# ---------------------------------------------------------------------------
# LLM step envelopes
# ---------------------------------------------------------------------------


class ClassifyExtract(BaseModel):
    """Schema for LLM call 1 (also the offline classifier target)."""

    intent: Literal[
        "new_project", "audit_consult", "exploratory", "out_of_scope", "unclear"
    ]
    out_of_scope: bool
    out_of_scope_reason: str | None = None
    suggested_response: str | None = None
    services: list[SERVICE_IDS] = Field(default_factory=list)
    goal: str | None = None
    deliverables: list[str] = Field(default_factory=list)
    industry: str | None = None
    budget_signal: str | None = None
    timeline_signal: str | None = None
    tech_constraints: list[str] = Field(default_factory=list)


class Advise(BaseModel):
    """Schema for LLM call 2: risks, questions, next steps."""

    risks: list[RiskFlag] = Field(default_factory=list)
    clarifying_questions: list[ClarifyingQuestion] = Field(default_factory=list)
    next_steps: list[NextStep] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Final assembled brief
# ---------------------------------------------------------------------------


class Provenance(BaseModel):
    """How this output was produced — always surfaced in the UI."""

    mode: Literal[
        "glm_live",
        "glm_live_fallback_offline",
        "offline_rules",
        "offline_cached",
        "baseline_rules",
    ]
    model: str
    prompt_version: str
    schema_version: str = SCHEMA_VERSION
    latency_ms: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    llm_calls: int = 0
    cache_hit: bool = False
    notes: list[str] = Field(default_factory=list)


class LeadBrief(BaseModel):
    """The final deliverable of the Discovery Copilot pipeline."""

    schema_version: str = SCHEMA_VERSION
    input_summary: str = Field(
        description="First 160 chars of the sanitized inquiry, for display"
    )
    sanitization: SanitizationResult
    intent: Literal[
        "new_project", "audit_consult", "exploratory", "out_of_scope", "unclear"
    ]
    out_of_scope: bool = False
    out_of_scope_reason: str | None = None
    suggested_response: str | None = None
    services: list[ServiceMatch] = Field(default_factory=list)
    extraction: Extraction = Field(default_factory=Extraction)
    estimate: Estimate | None = None
    risks: list[RiskFlag] = Field(default_factory=list)
    clarifying_questions: list[ClarifyingQuestion] = Field(default_factory=list)
    next_steps: list[NextStep] = Field(default_factory=list)
    process_alignment: list[str] = Field(default_factory=list)
    grounding_evidence: list[str] = Field(default_factory=list)
    provenance: Provenance
