"""Shared FastAPI dependencies for the API layer."""

from app.db.session import get_db

__all__ = ["get_db"]

# TODO: get_current_user (JWT-based) once the auth task is scoped.
