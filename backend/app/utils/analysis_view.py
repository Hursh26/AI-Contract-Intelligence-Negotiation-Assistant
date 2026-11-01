"""Map stored ML output (`Contract.clauses`) to the shapes the frontend renders."""

import re
from typing import Any

from app.models.contract import Contract
from app.schemas.analysis import AnalysisOut, ClauseView, HistoryItem, RiskSummary

# "30 days", "one (1) month" — a number (digits, or a word followed by "(n)") then a unit.
_NOTICE_RE = re.compile(
    r"\b(?:\w+\s*\(\d+\)|\d+)\s*(?:business\s+|calendar\s+)?(?:day|week|month)s?\b",
    re.IGNORECASE,
)

# spaCy's PERSON/ORG tags are noisy on contracts (role words, headings, address
# fragments). Drop the obvious junk so "Parties" in the UI is mostly real names.
_ROLE_WORDS = {
    "landlord", "tenant", "lessor", "lessee", "party", "parties", "employer", "employee",
    "company", "client", "vendor", "owner", "licensor", "licensee", "agreement", "premises",
}


def _looks_like_party(name: str) -> bool:
    words = name.split()
    return (
        1 <= len(words) <= 4
        and not any(ch.isdigit() for ch in name)
        and not name.isupper()
        and name.lower() not in _ROLE_WORDS
        and not any(w.lower().strip(",.") in {"hereinafter", "referred"} for w in words)
    )


def _raw_clauses(contract: Contract) -> list[dict[str, Any]]:
    """Stored clauses may come from PATCH /extraction (free-form JSON), so keep
    only items shaped like ML clauses (dicts) and ignore the rest."""
    return [c for c in (contract.clauses or []) if isinstance(c, dict)]


def _clause_views(raw: list[dict[str, Any]]) -> list[ClauseView]:
    views = []
    for c in raw:
        risk = c.get("risk") if isinstance(c.get("risk"), dict) else {}
        try:
            views.append(
                ClauseView(
                    category=str(c.get("type", "other")).replace("_", " ").title(),
                    text=str(c.get("text", "")),
                    risk_label=str(risk.get("level", "low")).upper(),
                    risk_score=round(float(risk.get("score", 0)) * 100),
                    reasons=[str(r) for r in risk.get("reasons", [])],
                )
            )
        except (TypeError, ValueError):
            continue  # unusable risk data on this clause; skip it
    return views


def build_risk_summary(clauses: list[ClauseView]) -> RiskSummary:
    """Overall score = half the worst clause + half the average, so one severe
    clause isn't diluted away by many harmless ones."""
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for c in clauses:
        counts[c.risk_label if c.risk_label in counts else "LOW"] += 1
    if clauses:
        scores = [c.risk_score for c in clauses]
        overall = round(0.5 * max(scores) + 0.5 * sum(scores) / len(scores))
    else:
        overall = 0
    level = "HIGH" if overall >= 70 else "MEDIUM" if overall >= 40 else "LOW"
    return RiskSummary(
        overall_score=overall,
        level=level,
        high=counts["HIGH"],
        medium=counts["MEDIUM"],
        low=counts["LOW"],
    )


def _entities(raw: list[dict[str, Any]]) -> dict[str, Any]:
    def values(label_set: set[str], clause_type: str | None = None) -> list[str]:
        seen: list[str] = []
        for c in raw:
            if clause_type and c.get("type") != clause_type:
                continue
            for e in c.get("entities") or []:
                if not isinstance(e, dict) or not e.get("text"):
                    continue
                if e.get("label") in label_set and e["text"] not in seen:
                    seen.append(e["text"])
        return seen

    parties = [n for n in values({"ORG", "PERSON"}) if _looks_like_party(n)][:4]
    money = values({"MONEY"})
    rent = values({"MONEY"}, "payment")
    deposit = values({"MONEY"}, "deposit")
    notice: list[str] = []
    for c in raw:
        if "notice" in str(c.get("text", "")).lower():
            for m in _NOTICE_RE.findall(str(c["text"])):
                if m not in notice:
                    notice.append(m)

    return {
        "parties": {f"Party {i + 1}": {"name": name, "page": None} for i, name in enumerate(parties)},
        "rent": {"value": rent[0], "page": None} if rent else None,
        "deposit": {"value": deposit[0], "page": None} if deposit else None,
        "money_mentions": [{"value": v, "page": None} for v in money],
        "dates": [{"value": v, "page": None} for v in values({"DATE"})],
        "notice_periods": [{"value": v, "page": None} for v in notice],
    }


def is_analyzed(contract: Contract) -> bool:
    return isinstance(contract.clauses, list)


def build_analysis(contract: Contract) -> AnalysisOut:
    raw = _raw_clauses(contract)
    clauses = _clause_views(raw)
    return AnalysisOut(
        id=contract.id,
        filename=contract.filename,
        uploaded_at=contract.created_at,
        clauses=clauses,
        risk_summary=build_risk_summary(clauses),
        entities=_entities(raw),
    )


def build_history_item(contract: Contract) -> HistoryItem:
    return HistoryItem(
        id=contract.id,
        filename=contract.filename,
        uploaded_at=contract.created_at,
        risk_summary=build_risk_summary(_clause_views(_raw_clauses(contract))),
    )
