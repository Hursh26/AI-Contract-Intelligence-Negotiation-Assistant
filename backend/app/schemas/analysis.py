"""Response shapes for the frontend's analysis views.

The ML service returns clauses as `{id, text, type, entities, risk}`; the UI
wants a presentation-friendly shape (risk labels/scores out of 100, a risk
summary, grouped entities). `app/utils/analysis_view.py` does the mapping.
`page` fields are always None for now — ML doesn't report page numbers.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ClauseView(BaseModel):
    category: str
    text: str
    risk_label: str  # HIGH | MEDIUM | LOW
    risk_score: int  # 0-100
    reasons: list[str] = []
    page: int | None = None


class RiskSummary(BaseModel):
    overall_score: int  # 0-100
    level: str  # HIGH | MEDIUM | LOW
    high: int
    medium: int
    low: int


class AnalysisOut(BaseModel):
    id: uuid.UUID
    filename: str
    uploaded_at: datetime
    num_pages: int | None = None
    clauses: list[ClauseView]
    risk_summary: RiskSummary
    entities: dict[str, Any]


class HistoryItem(BaseModel):
    id: uuid.UUID
    filename: str
    uploaded_at: datetime
    risk_summary: RiskSummary


class AskRequest(BaseModel):
    question: str = Field(max_length=1000)


class EvidenceOut(BaseModel):
    text: str
    page: int | None = None
    similarity: int  # 0-100


class AskOut(BaseModel):
    answer: str
    evidence: list[EvidenceOut]
