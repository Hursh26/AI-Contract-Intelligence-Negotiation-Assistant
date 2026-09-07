"""SQLAlchemy declarative base.

All ORM models (app/models/*) inherit from this Base. Import it here (rather
than each model defining its own) so Alembic/metadata stays in one place.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
