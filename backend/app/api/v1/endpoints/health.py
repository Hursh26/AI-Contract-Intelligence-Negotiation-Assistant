"""Liveness check — used by CI/infra to confirm the API is up and to smoke-test the scaffold."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", include_in_schema=False)
def health_check() -> dict[str, str]:
    return {"status": "ok"}
