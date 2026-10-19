"""Unit tests: offline engine (classifier, OOS rules, extraction, cache)."""

from app.core.offline import (
    OfflineEngine,
    extract_budget,
    extract_industry,
    extract_timeline,
    get_engine,
)
from app.core.pipeline import sanitize


def test_classifier_obvious_cases():
    eng = get_engine()
    cases = {
        "We need a mobile app with payments and push notifications.": "software_dev",
        "Migrate our servers to AWS with Kubernetes and CI/CD pipelines.": "cloud",
        "We want an AI chatbot that answers from our own documents.": "ai_automation",
        "We need technical SEO and Google Ads campaigns for lead generation.": "seo_marketing",
    }
    for text, expected in cases.items():
        picks, _ = eng.predict_services(text)
        assert expected in picks, f"{text[:40]} -> {picks}"


def test_oos_rules():
    eng = get_engine()
    oos_texts = [
        "I am a final-year student looking for an internship. My resume attached.",
        "We are a staffing agency with offshore developer rates.",
        "Our summit is looking for sponsors, platinum slot Rs 2 lakh.",
        "Can you help recover my hacked Instagram account?",
    ]
    for t in oos_texts:
        san = sanitize(t)
        ce = eng.classify_extract(san.sanitized_text, san)
        assert ce.out_of_scope, f"not flagged OOS: {t[:40]}"
        assert ce.services == []
        assert ce.suggested_response


def test_oos_templates_all_caught():
    """The 8 OOS template bodies must all be routed out of scope."""
    import re

    from app.core.offline import OOS_PATTERNS

    bodies = [
        "Hello, I am a final-year student looking for an internship at Cynbit. Please find my resume attached. Do you have any openings?",
        "We are a staffing agency placing offshore developers.",
        "saw your work, we are building a similar agency — partnership or referral exchange?",
        "We are organizing a tech summit and looking for sponsors. Platinum slot is Rs 2 lakh.",
        "Can you help recover my hacked Instagram account?",
        "my son has a school project on artificial intelligence",
        "Do you sell refurbished laptops? Looking for 10 units.",
        "Requesting a media kit and your latest press releases.",
    ]
    for b in bodies:
        assert any(re.search(p, b, re.I) for p, _ in OOS_PATTERNS), b


def test_budget_extraction():
    assert extract_budget("Our budget is roughly INR 3 lakh for this") is not None
    assert "3" in extract_budget("Our budget is roughly INR 3 lakh for this")
    assert extract_budget("we can spend up to $12000") is not None
    assert extract_budget("Budget thoda tight hai but quality kaam chahiye") is not None
    assert extract_budget("We have no money talk here") is None


def test_timeline_extraction():
    assert extract_timeline("We'd like this within 3 months") is not None
    assert extract_timeline("go live by Diwali") is not None
    assert extract_timeline("no hard deadline, this year would be nice") is not None
    assert extract_timeline("We need quality work.") is None


def test_industry_extraction():
    assert extract_industry("booking system for our clinic") == "healthcare"
    assert extract_industry("online ordering for our restaurant") == "food"
    assert extract_industry("tenant management for properties") == "real_estate"


def test_cache_lookup_miss_returns_none():
    eng = get_engine()
    assert eng.cache_lookup("definitely not a cached example text 12345") is None


def test_cache_lookup_structure_if_present():
    eng = get_engine()
    hit = eng.cache_lookup("anything")
    if hit is not None:  # only when cache file exists with examples
        assert "provenance" in hit or "intent" in hit


def test_complexity_model_valid_bands():
    eng = get_engine()
    model = eng.complexity_model()
    for t in (
        "Simple landing page plus contact form for our studio. Nothing fancy.",
        "Enterprise real-time ticketing platform with waitlist engine and AR features.",
    ):
        assert model.predict(t) in ("S", "M", "L")


def test_advise_shapes():
    eng = get_engine()
    san = sanitize("We need a mobile app with payments. We'd like this within 2 weeks.")
    ce = eng.classify_extract(san.sanitized_text, san)
    adv = eng.advise(ce, san, "M")
    assert 1 <= len(adv.clarifying_questions) <= 5
    assert adv.risks and adv.next_steps
    assert all(q.priority in ("must_ask", "should_ask", "nice_to_have") for q in adv.clarifying_questions)


def test_offline_engine_reload_deterministic(tmp_path):
    """Same train file → same predictions (determinism check)."""
    import json

    from app.core.offline import TRAIN_PATH

    rows = [
        json.loads(l)
        for l in TRAIN_PATH.read_text(encoding="utf-8").splitlines()
        if l.strip() and not l.startswith("#")
    ]
    e1, e2 = OfflineEngine(), OfflineEngine()
    t = "We need an AI chatbot for our website."
    assert e1.predict_services(t)[0] == e2.predict_services(t)[0]
    assert len(rows) == 120
