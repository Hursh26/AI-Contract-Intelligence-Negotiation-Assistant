"""Contract ORM model.

Covers the "store uploaded/extracted contract info" side of the backend
tasks. `status` tracks it through the pipeline; `extracted_text` /
`clauses` are populated via PATCH /contracts/{id}/extraction once the
NLP/ML team's extraction + clause-identification tasks produce output —
this model just persists what they hand back, it doesn't do NLP itself.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base


class Contract(Base):
    __tablename__ = "contracts"

    # sqlalchemy.Uuid (portable) rather than postgresql.UUID — see user.py.
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Nullable until the JWT auth task lands and every request carries an
    # authenticated user to attach. DB-schema flag: this tightens to
    # nullable=False once that's wired up — call this out in that PR.
    owner_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=True)

    filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    content_type = Column(String, nullable=True)

    # uploaded -> processing -> processed | failed
    status = Column(String, nullable=False, default="uploaded")

    extracted_text = Column(Text, nullable=True)
    # JSONB on Postgres (indexable, native json type); falls back to plain
    # JSON (TEXT-backed) on any other dialect, e.g. SQLite in tests — same
    # column works on both without special-casing.
    clauses = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
