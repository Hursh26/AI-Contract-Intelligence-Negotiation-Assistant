"""User ORM model.

Minimal shape for now — fields will grow once the auth task is scoped
(roles, verification status, etc.).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Uuid

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    # sqlalchemy.Uuid (not the postgresql-dialect-specific UUID type) so this
    # renders as native UUID on Postgres in production but still works on
    # SQLite, which the test suite uses to run with zero external infra.
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
