"""Dev-time helper: create tables directly from the models.

Stop-gap for local development only — a real migration tool (Alembic)
should be introduced once schema changes need to be tracked/versioned
across environments. Not run automatically; invoke explicitly:

    python -m app.db.init_db
"""

import app.models  # noqa: F401  (registers all models on Base.metadata before create_all)
from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
