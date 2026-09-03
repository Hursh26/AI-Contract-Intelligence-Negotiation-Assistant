"""Aggregates all v1 endpoint routers into one APIRouter mounted by main.py."""

from fastapi import APIRouter

from app.api.v1.endpoints import contracts, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
