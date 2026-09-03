"""Pydantic schemas for Contract request/response bodies.

Kept minimal on purpose — the upload endpoint's actual request/response
shape gets finalized as part of the "Create upload API" task; this is just
enough to have a typed response for the DB model above.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ContractExtractionUpdate(BaseModel):
    """Body for PATCH /contracts/{id}/extraction — what NLP/ML hands back
    once they've extracted text and identified clauses for a contract."""

    extracted_text: str
    clauses: Any | None = None


class ContractOut(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    extracted_text: str | None = None
    clauses: Any | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
