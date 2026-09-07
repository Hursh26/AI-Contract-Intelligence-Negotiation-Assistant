"""Import every ORM model here so `import app.models` registers all of them
on Base.metadata — required for Base.metadata.create_all() (see
app/db/init_db.py and tests/conftest.py) to see every table, including ones
only referenced via a ForeignKey string (e.g. Contract.owner_id -> users.id)
rather than imported directly.
"""

from app.models.contract import Contract
from app.models.user import User

__all__ = ["Contract", "User"]
