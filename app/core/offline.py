"""offline.py — deterministic offline engine + precomputed live-LLM cache.

Offline Mode is a first-class provider (challenge requirement 6.4), not a stub:
  1. Exact-match cache: built-in demo examples replay REAL precomputed live-LLM
     outputs (data/synthetic/cached_outputs.json, generated 2026-10-19 via a
     live endpoint with the previous GLM provider — provenance in the file's
     meta block; regenerate any time with scripts/gen_cache.py + a Groq key).
  2. Deterministic engine for any other input:
     - service multi-label classification: TF-IDF (word 1-2 grams) +
       one-vs-rest logistic regression trained at load time on the TRAIN split
       (120 examples; eval split never touched — decision.md D-011);
     - out-of-scope detection: keyword rules applied BEFORE the classifier;
     - field extraction: regex (budget/timeline), industry dictionary,
       first-sentence goal heuristic;
     - complexity/effort estimation: shared deterministic rules (same rules
       used in live mode — estimates are never LLM-invented);
     - risks/questions/next-steps: feature-keyed template pools.

SYNTHETIC DATA notice: the training file is synthetic (banner inside).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .schemas import (
    Advise,
    ClassifyExtract,
    ClarifyingQuestion,
    NextStep,
    RiskFlag,
    SanitizationResult,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TRAIN_PATH = REPO_ROOT / "data" / "synthetic" / "leads_train.jsonl"
CACHE_PATH = REPO_ROOT / "data" / "synthetic" / "cached_outputs.json"

SERVICE_IDS = ["ai_automation", "software_dev", "cloud", "seo_marketing"]

# ---------------------------------------------------------------------------
# Out-of-scope keyword rules (checked before the classifier)
# ---------------------------------------------------------------------------

OOS_PATTERNS: list[tuple[str, str]] = [
    (r"\binternship\b|\bmy resume attached\b|\bjob application\b|\bany openings\b", "job_inquiry"),
    (r"staffing agency|talent pool|placement (rate|fee)|offshore developers", "vendor_pitch"),
    (r"partnership or referral|referral exchange|co-?sell", "partnership_pitch"),
    (r"sponsor(s|ship)?\b.*\b(slot|package|platinum|gold)\b|looking for sponsors", "event_sponsorship"),
    (r"hacked|recover my .*account|my laptop|my printer|virus", "personal_tech_help"),
    (r"school project|10th grade|neural networks work|for homework", "homework_help"),
    (r"refurbished|sell (us |me )?(laptops|hardware)|buy .*units", "product_purchase"),
    (r"media kit|press release|for a story we are writing", "media_request"),
]

OOS_RESPONSES = {
    "job_inquiry": "Thank you for your interest in Cynbit. Roles and internships are handled via the careers page (cynbit.in/careers) — please apply there so your profile reaches the right team.",
    "vendor_pitch": "Thanks for reaching out. Cynbit is not evaluating new vendor partnerships through this channel; if that changes we will contact you.",
    "partnership_pitch": "Appreciate the note. Partnership ideas can go to opportunities@cynbit.in with a one-page summary; this inbox is for client engagements.",
    "event_sponsorship": "Thank you for the sponsorship invitation. Sponsorship decisions are made separately — kindly email the details to opportunities@cynbit.in.",
    "personal_tech_help": "This request is outside Cynbit's service lines (AI automation, software development, cloud, digital marketing). We cannot help with personal device/account recovery.",
    "homework_help": "This is outside Cynbit's service lines, but Cynbit's training arm BitElevate may be relevant for structured learning (cynbit.in/bitelevate).",
    "product_purchase": "Cynbit is a software and AI services company, not a hardware reseller.",
    "media_request": "For media requests, please email opportunities@cynbit.in and the team will share what is public.",
}

# ---------------------------------------------------------------------------
# Extraction utilities (regex / dictionaries)
# ---------------------------------------------------------------------------

BUDGET_RE = re.compile(
    r"(?:rs\.?|inr|₹|\$)\s?([\d][\d,\.]*)\s?(lakh|lakhs|l\b|crore|k\b|thousand)?",
    re.I,
)
BUDGET_TIGHT_RE = re.compile(
    r"budget\b[^.\n]{0,30}?\b(tight|low|limited|small)\b|tight budget", re.I
)
TIMELINE_RE = re.compile(
    r"(?:within|in|by|before)\s+(?:the\s+)?(?:next\s+)?(\d+)\s*(week|month)s?|"
    r"(\d+)\s*(week|month)s?\b|next quarter|diwali|festive season|this year|"
    r"no hard deadline|urgent(?:ly)?|asap",
    re.I,
)

INDUSTRY_DICT = {
    "restaurant": "food", "cafe": "food", "food": "food", "kitchen": "food",
    "clinic": "healthcare", "dental": "healthcare", "patient": "healthcare",
    "health": "healthcare", "medical": "healthcare", "diagnostic": "healthcare",
    "gym": "fitness", "fitness": "fitness", "studio": "wellness",
    "school": "education", "academy": "education", "students": "education",
    "edtech": "edtech", "learning": "edtech", "coaching": "education",
    "fashion": "fashion", "clothing": "fashion", "apparel": "fashion",
    "store": "retail", "shop": "retail", "retail": "retail", "grocery": "retail",
    "ecommerce": "ecommerce", "storefront": "ecommerce", "marketplace": "ecommerce",
    "bank": "fintech", "fintech": "fintech", "payments": "fintech",
    "invoice": "fintech", "insurance": "fintech",
    "real estate": "real_estate", "property": "real_estate", "tenant": "real_estate",
    "rent": "real_estate", "landlord": "real_estate",
    "logistics": "logistics", "shipment": "logistics", "cargo": "logistics",
    "warehouse": "logistics", "fleet": "logistics",
    "hotel": "hospitality", "resort": "hospitality", "travel": "hospitality",
    "events": "events", "event": "events", "ticketing": "events", "summit": "events",
    "manufactur": "manufacturing", "factory": "manufacturing", "erp": "manufacturing",
    "farm": "agriculture", "agri": "agriculture", "export": "agriculture",
    "agency": "media", "marketing": "media", "media": "media", "content": "media",
    "franchise": "retail", "saas": "software", "software": "software",
}


def extract_budget(text: str) -> str | None:
    m = BUDGET_RE.search(text)
    if m:
        unit = (m.group(2) or "").lower()
        cur = "USD" if "$" in m.group(0) else "INR"
        return f"{cur} {m.group(1)}{(' ' + unit) if unit else ''}"
    if BUDGET_TIGHT_RE.search(text):
        return "tight/limited budget (no figure stated)"
    return None


def extract_timeline(text: str) -> str | None:
    m = TIMELINE_RE.search(text)
    if not m:
        return None
    return m.group(0).strip().rstrip(".").lower()


def extract_industry(text: str) -> str | None:
    low = text.lower()
    for kw, ind in INDUSTRY_DICT.items():
        if kw in low:
            return ind
    return None


def extract_goal(text: str) -> str | None:
    body = re.sub(r"^(hi|hello|namaste|hey)[^,\n]*[,\n]\s*", "", text.strip(), flags=re.I)
    body = re.sub(r"\s+", " ", body)
    first = body.split(". ")[0].strip()
    if not first or len(first) < 12:
        return None
    if len(first) > 140:
        first = first[:137] + "..."
    return first


DELIVERABLE_HINTS = {
    "ai_automation": ["AI assistant / agent", "document automation", "voice agent", "classification & triage"],
    "software_dev": ["web/mobile application", "portal or dashboard", "booking/e-commerce module"],
    "cloud": ["cloud migration", "CI/CD & IaC", "Kubernetes cluster", "cost/security audit"],
    "seo_marketing": ["technical SEO program", "paid campaigns", "content plan", "funnel/CRO work"],
}


def guess_deliverables(services: list[str], text: str) -> list[str]:
    low = text.lower()
    out: list[str] = []
    for s in services:
        for d in DELIVERABLE_HINTS[s]:
            key = d.split(" ")[0].split("/")[0].lower()
            if key[:5] in low or key in low:
                out.append(d)
        if not any(d for d in DELIVERABLE_HINTS[s] if d in out):
            out.append(DELIVERABLE_HINTS[s][0])
    return list(dict.fromkeys(out))[:6]


# ---------------------------------------------------------------------------
# The offline engine
# ---------------------------------------------------------------------------


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            rows.append(json.loads(line))
    return rows


class ComplexityModel:
    """Classical complexity bander: char n-gram TF-IDF + logistic regression,
    trained on the TRAIN split only (deterministic; no LLM involved).
    Rationale for the UI still comes from transparent keyword rules in
    pipeline.estimate_complexity — this model only decides the band."""

    def __init__(self, rows: list[dict]) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression

        texts = [r["text"] for r in rows]
        labels = [r["labels"]["complexity"] for r in rows]
        self.vec = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True
        )
        X = self.vec.fit_transform(texts)
        self.clf = LogisticRegression(
            C=10.0, max_iter=3000, class_weight="balanced", solver="lbfgs"
        )
        self.clf.fit(X, labels)

    def predict(self, text: str) -> str:
        proba = self.clf.predict_proba(self.vec.transform([text]))[0]
        return str(self.clf.classes_[int(proba.argmax())])


class OfflineEngine:
    """Deterministic engine + exact-match cache lookup for Offline Mode."""

    def __init__(self, train_path: Path = TRAIN_PATH, cache_path: Path = CACHE_PATH) -> None:
        self.train = _load_jsonl(train_path)
        self._cache = self._load_cache(cache_path)
        self._clf = None  # lazy
        self._threshold = 0.35
        self._cx_model: ComplexityModel | None = None  # lazy

    # -- cache ---------------------------------------------------------------

    @staticmethod
    def _load_cache(path: Path) -> dict:
        if not path.exists():
            return {"examples": []}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data.setdefault("examples", [])
            return data
        except (json.JSONDecodeError, OSError):
            return {"examples": []}

    def complexity_model(self) -> ComplexityModel:
        if self._cx_model is None:
            self._cx_model = ComplexityModel(self.train)
        return self._cx_model

    def cache_lookup(self, text: str) -> dict | None:
        """Exact (whitespace-normalized) match against cached demo outputs."""
        key = " ".join(text.split())
        for ex in self._cache.get("examples", []):
            if " ".join(ex.get("input", "").split()) == key:
                return ex.get("output")
        return None

    def cache_meta(self) -> dict:
        return self._cache.get("meta", {})

    # -- classification --------------------------------------------------------

    def _ensure_clf(self):
        if self._clf is not None:
            return
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.multiclass import OneVsRestClassifier

        train_texts = [r["text"] for r in self.train if r["labels"]["services"] != ["out_of_scope"]]
        train_labels = [
            [1 if s in r["labels"]["services"] else 0 for s in SERVICE_IDS]
            for r in self.train
            if r["labels"]["services"] != ["out_of_scope"]
        ]
        vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1)
        X = vec.fit_transform(train_texts)
        import numpy as np

        Y = np.array(train_labels)
        clf = OneVsRestClassifier(
            LogisticRegression(C=8.0, max_iter=2000, solver="lbfgs"), n_jobs=1
        )
        clf.fit(X, Y)
        # threshold picked on TRAIN only (in-sample micro-F1 sweep)
        probs = clf.predict_proba(X)
        best_t, best_f1 = 0.35, -1.0
        for t in (0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5):
            pred = (probs >= t).astype(int)
            tp = float(((pred == 1) & (Y == 1)).sum())
            fp = float(((pred == 1) & (Y == 0)).sum())
            fn = float(((pred == 0) & (Y == 1)).sum())
            f1 = 2 * tp / (2 * tp + fp + fn) if tp else 0.0
            if f1 > best_f1:
                best_t, best_f1 = t, f1
        self._threshold = best_t
        self._clf = (vec, clf)

    def predict_services(self, text: str) -> tuple[list[str], dict[str, float]]:
        self._ensure_clf()
        vec, clf = self._clf
        proba = clf.predict_proba(vec.transform([text]))[0]
        conf = {SERVICE_IDS[i]: round(float(proba[i]), 3) for i in range(len(SERVICE_IDS))}
        picks = [SERVICE_IDS[i] for i in range(len(SERVICE_IDS)) if proba[i] >= self._threshold]
        if not picks:  # degenerate: take top-1 if it clears a lower floor
        # (keeps the engine useful on odd phrasing; flagged via confidence)
            i_max = int(proba.argmax())
            if proba[i_max] >= 0.22:
                picks = [SERVICE_IDS[i_max]]
        return picks, conf

    # -- step 1+2: classify & extract -----------------------------------------

    def classify_extract(self, text: str, san: SanitizationResult) -> ClassifyExtract:
        for pattern, intent_key in OOS_PATTERNS:
            if re.search(pattern, text, re.I):
                return ClassifyExtract(
                    intent="out_of_scope",
                    out_of_scope=True,
                    out_of_scope_reason=f"Matched out-of-scope pattern: {intent_key}",
                    suggested_response=OOS_RESPONSES.get(intent_key, "Politely redirect to the appropriate channel."),
                    services=[],
                    goal=None,
                    deliverables=[],
                    industry=extract_industry(text),
                    budget_signal=extract_budget(text),
                    timeline_signal=extract_timeline(text),
                    tech_constraints=[],
                )
        services, conf = self.predict_services(text)
        goal = extract_goal(text)
        vague = goal is None and not services
        return ClassifyExtract(
            intent="exploratory" if vague or (goal and len(goal) < 25 and not services) else "new_project",
            out_of_scope=False,
            services=services,
            goal=goal,
            deliverables=guess_deliverables(services, text),
            industry=extract_industry(text),
            budget_signal=extract_budget(text),
            timeline_signal=extract_timeline(text),
            tech_constraints=_tech_constraints(text),
        )

    # -- step 5: risks / questions / next steps --------------------------------

    def advise(self, ce: ClassifyExtract, san: SanitizationResult, complexity: str) -> Advise:
        risks: list[RiskFlag] = []
        questions: list[ClarifyingQuestion] = []
        steps: list[NextStep] = []

        if san.injection_suspected:
            risks.append(RiskFlag(
                risk="Inquiry contains prompt-injection-style instructions; output was kept on-task and no instructions were followed.",
                severity="high",
                mitigation="Sanitizer flagged it; brief generated from sanitized data only; do not copy inquiry text into any downstream tool verbatim.",
            ))
        if ce.out_of_scope:
            return Advise(
                risks=[RiskFlag(risk="None — not a service engagement.", severity="low", mitigation="n/a")],
                clarifying_questions=[],
                next_steps=[
                    NextStep(step="Send the polite redirect response (suggested_response above).", owner="BD", when="immediately"),
                    NextStep(step="If the sender looks like a future client, add to newsletter list with consent.", owner="BD", when="same day"),
                ],
            )

        if not ce.budget_signal:
            questions.append(ClarifyingQuestion(
                question="What budget range has been approved or is being planned for this engagement?",
                priority="must_ask", why="Budget presence is the single biggest driver of realistic scoping.",
            ))
        else:
            risks.append(RiskFlag(
                risk="Stated budget may not align with the scope once requirements are detailed.",
                severity="medium", mitigation="Validate budget against the complexity band in the discovery call before blueprinting.",
            ))
        if not ce.timeline_signal:
            questions.append(ClarifyingQuestion(
                question="What is your target go-live date or hard deadline?",
                priority="must_ask", why="Timeline feasibility depends on complexity band and team availability.",
            ))
        if not ce.goal or len((ce.goal or "")) < 30:
            questions.append(ClarifyingQuestion(
                question="In one sentence, what should this solution do for your business once live?",
                priority="must_ask", why="Current description is too vague to scope or estimate.",
            ))
        urgent = ce.timeline_signal and any(
            w in ce.timeline_signal for w in ("urgent", "asap", "week", "2 month")
        )
        if urgent and complexity in ("M", "L"):
            risks.append(RiskFlag(
                risk="Timeline appears aggressive for the stated scope.",
                severity="high", mitigation="Propose phased delivery (MVP first) or negotiate the deadline in blueprinting.",
            ))
        if len(ce.services) >= 2:
            risks.append(RiskFlag(
                risk="Multi-service engagement: sequencing and ownership must be explicit to avoid scope drift.",
                severity="medium", mitigation="Single blueprint phase covering both lines; one named owner per track.",
            ))
        low = ce.timeline_signal or ""
        if "monolith" in low or "legacy" in (ce.goal or "").lower() or "legacy" in (ce.goal or ""):
            risks.append(RiskFlag(
                risk="Legacy/monolith context hides unknowns that surface during discovery.",
                severity="medium", mitigation="Start with the Discovery & audit step before committing any estimate.",
            ))
        comp_kw = (ce.goal or "") + " " + " ".join(ce.deliverables)
        if any(k in comp_kw.lower() for k in ("health", "patient", "payment", "card", "kyc", "data")):
            risks.append(RiskFlag(
                risk="Possible regulatory/compliance touchpoints (health data, payments).",
                severity="medium", mitigation="Pull the Quality & integrity check forward; identify applicable rules in discovery.",
            ))
        if san.language == "hinglish":
            risks.append(RiskFlag(
                risk="Client communicates in Hinglish; miscommunication risk in requirements.",
                severity="low", mitigation="Respond bilingually; confirm all scope points in writing in English.",
            ))

        for svc in ce.services:
            q = {
                "ai_automation": ClarifyingQuestion(
                    question="What content/documents should the AI ground its answers in, and when should it hand off to a human?",
                    priority="must_ask", why="Grounding source and handoff rules define both quality and safety.",
                ),
                "software_dev": ClarifyingQuestion(
                    question="Which platforms (web / iOS / Android) and third-party integrations are must-haves for version one?",
                    priority="must_ask", why="Platform + integration scope is the main effort driver.",
                ),
                "cloud": ClarifyingQuestion(
                    question="What workloads run where today, and what downtime window is acceptable during migration?",
                    priority="must_ask", why="Migration approach depends on current state and tolerance for downtime.",
                ),
                "seo_marketing": ClarifyingQuestion(
                    question="What is the monthly ad budget, and which event counts as a 'lead' for you?",
                    priority="must_ask", why="Channel mix and CPL math depend on both numbers.",
                ),
            }.get(svc)
            if q and q not in questions:
                questions.append(q)
        questions.append(ClarifyingQuestion(
            question="Who is the decision maker and who else must approve the engagement?",
            priority="should_ask", why="Avoids late-stage re-approvals; small teams often have hidden stakeholders.",
        ))
        if len(questions) < 3:
            questions.append(ClarifyingQuestion(
                question="Are there existing systems, vendors, or contracts this must work with?",
                priority="should_ask", why="Integration constraints change the effort band.",
            ))

        steps = [
            NextStep(step="Send the structured acknowledgment + this brief (target: within 5 minutes of inquiry).", owner="BD", when="immediately"),
            NextStep(step="Book the discovery call; use the clarifying questions above as the agenda.", owner="BD", when="same day"),
            NextStep(step="Prepare Discovery & audit checklist for the matched service line(s).", owner="Solutions architect", when="before call"),
            NextStep(step="Draft proposal skeleton from this brief after the call.", owner="Founder / BD", when="within 48h"),
        ]
        return Advise(risks=risks[:4], clarifying_questions=questions[:5], next_steps=steps)


def _tech_constraints(text: str) -> list[str]:
    low = text.lower()
    out = []
    if "aws" in low:
        out.append("AWS")
    if "azure" in low:
        out.append("Azure")
    if "wordpress" in low:
        out.append("existing WordPress")
    if "php" in low:
        out.append("existing PHP system")
    if "kubernetes" in low or "k8s" in low:
        out.append("Kubernetes")
    if "hindi" in low and ("english" in low or "bilingual" in low):
        out.append("bilingual Hindi+English")
    if "whatsapp" in low:
        out.append("WhatsApp integration")
    if "ios" in low or "android" in low:
        out.append("mobile platforms")
    return out[:4]


_engine: OfflineEngine | None = None


def get_engine() -> OfflineEngine:
    global _engine
    if _engine is None:
        _engine = OfflineEngine()
    return _engine
