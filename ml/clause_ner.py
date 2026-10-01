"""Clause typing, named-entity extraction and transparent risk heuristics."""

import re
from typing import Any

from .preprocessing import load_spacy


CLAUSE_PATTERNS: dict[str, tuple[str, ...]] = {
    "payment": ("rent", "payment", "invoice", "fee", "price", "compensation", "salary"),
    "deposit": ("security deposit", "deposit", "advance deposit"),
    "termination": ("termination", "terminate", "cancellation", "ending"),
    "notice": ("notice period", "written notice", "notice of"),
    "maintenance": ("maintenance", "repair", "repairs", "upkeep"),
    "indemnity": ("indemnify", "indemnification", "hold harmless"),
    "confidentiality": ("confidential", "non-disclosure", "trade secret"),
    "liability": ("liability", "liable", "damages", "limitation of liability"),
    "default": ("default", "breach", "remedy", "cure period"),
    "renewal": ("renewal", "automatically renew", "auto-renew"),
}

RISK_PATTERNS: dict[str, tuple[str, ...]] = {
    "high": (
        "unlimited liability",
        "liquidated damages",
        "penalty",
        "personal guarantee",
        "indemnify",
        "hold harmless",
        "forfeiture",
        "non-compete",
        "automatic renewal",
    ),
    "medium": (
        "terminate",
        "termination",
        "breach",
        "default",
        "liable",
        "late fee",
        "notice period",
    ),
}


def _contains_phrase(text: str, phrase: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text, re.IGNORECASE))


def detect_clause_type(text: str) -> str:
    scores = {name: sum(_contains_phrase(text, p) for p in phrases) for name, phrases in CLAUSE_PATTERNS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "other"


def extract_entities(text: str, model_name: str = "en_core_web_sm") -> list[dict[str, Any]]:
    doc = load_spacy(model_name)(text)
    return [
        {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
        for ent in doc.ents
    ]


def risk_assessment(text: str) -> dict[str, Any]:
    reasons: list[str] = []
    lower = text.lower()
    for level, phrases in RISK_PATTERNS.items():
        for phrase in phrases:
            if _contains_phrase(lower, phrase):
                reasons.append(phrase)
    if any(ch.isdigit() for ch in text):
        reasons.append("contains numeric obligation or threshold")

    if any(_contains_phrase(lower, p) for p in RISK_PATTERNS["high"]):
        level = "high"
        score = 0.85
    elif any(_contains_phrase(lower, p) for p in RISK_PATTERNS["medium"]):
        level = "medium"
        score = 0.60
    else:
        level = "low"
        score = 0.20

    return {"level": level, "score": score, "reasons": sorted(set(reasons))}


def analyze_clause(clause: dict[str, object], model_name: str = "en_core_web_sm") -> dict[str, Any]:
    text = str(clause["text"])
    return {
        "id": str(clause["id"]),
        "text": text,
        "type": detect_clause_type(text),
        "entities": extract_entities(text, model_name),
        "risk": risk_assessment(text),
    }
