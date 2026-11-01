"""Client for the NLP/ML service (`ml/api.py`: POST /analyze and POST /ask).

The ML service is a separate process owned by the NLP/ML team. This module
only sends it requests and returns its responses; clause identification and
question answering stay on their side.

Important quirk of that service: it keeps ONE in-memory search index, built
by the most recent `/analyze` call. `/ask` always answers against whatever
contract was analyzed last. `ask_about_contract` hides that by re-analyzing
the right contract first whenever the index might belong to a different one.

Limitation: that tracking lives in this process's memory. With more than one
backend worker/instance it can be stale, so set ML_REINDEX_EVERY_ASK=true
there. The real fix is ML accepting a contract id on /analyze and /ask.
"""

import threading
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import httpx

from app.core.config import settings


class MLBusyError(RuntimeError):
    """Another request has held the ML service too long (-> HTTP 503)."""


class MLServiceError(RuntimeError):
    """ML service unreachable, timed out, or returned an unusable response (-> HTTP 502)."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


# Which contract the ML service's index currently holds (None = unknown).
_lock = threading.Lock()
_indexed_contract_id: uuid.UUID | None = None


@contextmanager
def _ml_slot() -> Iterator[None]:
    """Exclusive use of the ML service's single index, with a bounded wait.

    Analyze+ask must not interleave (they share one index), but waiting
    forever behind a slow request would stall every user — so give up after
    ML_LOCK_TIMEOUT_SECONDS and let the client retry.
    """
    if not _lock.acquire(timeout=settings.ML_LOCK_TIMEOUT_SECONDS):
        raise MLBusyError("The analysis service is busy; please retry shortly.")
    try:
        yield
    finally:
        _lock.release()


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{settings.ML_SERVICE_URL.rstrip('/')}{path}"
    try:
        response = httpx.post(url, json=payload, timeout=settings.ML_SERVICE_TIMEOUT_SECONDS)
    except httpx.HTTPError as exc:
        raise MLServiceError(f"Could not reach ML service at {url}: {exc}") from exc

    if response.status_code != 200:
        raise MLServiceError(
            f"ML service returned {response.status_code}: {response.text[:200]}",
            status_code=response.status_code,
        )
    try:
        data = response.json()
    except ValueError as exc:
        raise MLServiceError(f"ML service returned invalid JSON from {url}") from exc
    if not isinstance(data, dict):
        raise MLServiceError(f"ML service returned an unexpected response from {url}")
    return data


def analyze_text(text: str) -> dict[str, Any]:
    """Send contract text to ML `/analyze`; return `{extracted_text, clauses, clause_count}`."""
    data = _post("/analyze", {"text": text})
    if "extracted_text" not in data or "clauses" not in data:
        raise MLServiceError("ML service /analyze response is missing 'extracted_text' or 'clauses'")
    return data


def analyze_and_index(contract_id: uuid.UUID, text: str) -> dict[str, Any]:
    """Analyze `text` and record that ML's index now holds `contract_id`.

    Done under the lock so a concurrent `ask_about_contract` can't re-index a
    different contract in between and leave our bookkeeping wrong.
    """
    global _indexed_contract_id
    with _ml_slot():
        _indexed_contract_id = None  # unknown until the analyze succeeds
        result = analyze_text(text)
        _indexed_contract_id = contract_id
    return result


def ask_about_contract(contract_id: uuid.UUID, text: str, question: str) -> dict[str, Any]:
    """Ask ML `/ask` about one specific contract; returns `{answer, sources: [...]}`.

    Re-analyzes `text` first if the ML index may hold a different contract.
    Also retries once if ML reports it has no index (e.g. it was restarted).
    """
    global _indexed_contract_id
    with _ml_slot():
        if settings.ML_REINDEX_EVERY_ASK or _indexed_contract_id != contract_id:
            _indexed_contract_id = None
            analyze_text(text)
            _indexed_contract_id = contract_id
        try:
            data = _post("/ask", {"question": question})
        except MLServiceError as exc:
            if exc.status_code != 422:
                raise
            # ML lost its index (restart) — rebuild and retry once.
            _indexed_contract_id = None
            analyze_text(text)
            _indexed_contract_id = contract_id
            data = _post("/ask", {"question": question})

    if "answer" not in data:
        raise MLServiceError("ML service /ask response is missing 'answer'")
    return data
