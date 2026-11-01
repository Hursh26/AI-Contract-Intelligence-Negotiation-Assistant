"""Tests for POST /contracts/{id}/analyze (ML service is mocked)."""

import io
import uuid

import httpx
import pytest
from fastapi.testclient import TestClient

import app.utils.ml_client as ml_client

ML_RESULT = {
    "extracted_text": "Term. Either party may terminate.",
    "clause_count": 1,
    "clauses": [{"id": "1", "text": "Either party may terminate.", "type": "termination"}],
}


def _upload_txt(client: TestClient, content: bytes = b"Either party may terminate.") -> str:
    r = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("c.txt", io.BytesIO(content), "text/plain")},
    )
    return r.json()["id"]


def test_analyze_stores_clauses(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    seen = {}

    def fake(contract_id: uuid.UUID, text: str) -> dict:
        seen["text"] = text
        return ML_RESULT

    monkeypatch.setattr("app.api.v1.endpoints.contracts.analyze_and_index", fake)
    cid = _upload_txt(client)
    r = client.post(f"/api/v1/contracts/{cid}/analyze")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "processed"
    assert body["clauses"] == ML_RESULT["clauses"]
    assert seen["text"] == "Either party may terminate."
    assert client.get(f"/api/v1/contracts/{cid}").json()["clauses"] == ML_RESULT["clauses"]


def test_analyze_unknown_contract_404(client: TestClient) -> None:
    assert client.post(f"/api/v1/contracts/{uuid.uuid4()}/analyze").status_code == 404


def test_analyze_ml_down_returns_502(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*a, **k):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(ml_client.httpx, "post", boom)
    cid = _upload_txt(client)
    r = client.post(f"/api/v1/contracts/{cid}/analyze")
    assert r.status_code == 502
    assert client.get(f"/api/v1/contracts/{cid}").json()["status"] == "uploaded"


def test_analyze_ml_bad_response_returns_502(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        ml_client.httpx, "post", lambda *a, **k: httpx.Response(200, json={"oops": 1})
    )
    cid = _upload_txt(client)
    assert client.post(f"/api/v1/contracts/{cid}/analyze").status_code == 502


def test_analyze_unparseable_file_422(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.v1.endpoints.contracts.analyze_and_index", lambda i, t: ML_RESULT)
    r = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("bad.pdf", io.BytesIO(b"%PDF-1.4\nnot real"), "application/pdf")},
    )
    cid = r.json()["id"]
    assert client.post(f"/api/v1/contracts/{cid}/analyze").status_code == 422


# --- frontend-facing views: history, analysis, ask -------------------------

RICH_ML_RESULT = {
    "extracted_text": "x",
    "clause_count": 3,
    "clauses": [
        {
            "id": "1",
            "text": "Tenant shall pay rent of $1,200 per month to Acme Realty LLC.",
            "type": "payment",
            "entities": [
                {"text": "$1,200", "label": "MONEY"},
                {"text": "Acme Realty LLC", "label": "ORG"},
            ],
            "risk": {"level": "low", "score": 0.2, "reasons": []},
        },
        {
            "id": "2",
            "text": "Either party may terminate with 30 days written notice.",
            "type": "termination",
            "entities": [{"text": "30 days", "label": "DATE"}],
            "risk": {"level": "medium", "score": 0.6, "reasons": ["terminate"]},
        },
        {
            "id": "3",
            "text": "Tenant shall indemnify Landlord.",
            "type": "indemnity",
            "entities": [],
            "risk": {"level": "high", "score": 0.85, "reasons": ["indemnify"]},
        },
    ],
}


def _analyzed(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setattr("app.api.v1.endpoints.contracts.analyze_and_index", lambda i, t: RICH_ML_RESULT)
    cid = _upload_txt(client)
    assert client.post(f"/api/v1/contracts/{cid}/analyze").status_code == 200
    return cid


def test_analysis_view_shape(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    cid = _analyzed(client, monkeypatch)
    r = client.get(f"/api/v1/contracts/{cid}/analysis")
    assert r.status_code == 200
    body = r.json()
    assert body["filename"] == "c.txt"
    assert [c["risk_label"] for c in body["clauses"]] == ["LOW", "MEDIUM", "HIGH"]
    assert body["clauses"][2]["risk_score"] == 85
    assert body["clauses"][0]["category"] == "Payment"
    s = body["risk_summary"]
    assert (s["high"], s["medium"], s["low"]) == (1, 1, 1)
    assert s["overall_score"] == round(0.5 * 85 + 0.5 * (20 + 60 + 85) / 3)
    assert s["level"] == "HIGH"
    assert body["entities"]["parties"]["Party 1"]["name"] == "Acme Realty LLC"
    assert body["entities"]["rent"]["value"] == "$1,200"
    assert body["entities"]["notice_periods"][0]["value"] == "30 days"


def test_analysis_view_requires_analysis(client: TestClient) -> None:
    cid = _upload_txt(client)
    assert client.get(f"/api/v1/contracts/{cid}/analysis").status_code == 409
    assert client.get(f"/api/v1/contracts/{uuid.uuid4()}/analysis").status_code == 404


def test_history_lists_only_analyzed(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _upload_txt(client)  # not analyzed -> excluded
    cid = _analyzed(client, monkeypatch)
    r = client.get("/api/v1/contracts")
    assert r.status_code == 200
    items = r.json()
    assert [i["id"] for i in items] == [cid]
    assert items[0]["risk_summary"]["high"] == 1


def test_ask_maps_sources_to_evidence(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    cid = _analyzed(client, monkeypatch)
    monkeypatch.setattr(
        "app.api.v1.endpoints.contracts.ask_about_contract",
        lambda contract_id, text, q: {
            "answer": "30 days",
            "sources": [{"id": "2", "text": "Either party may terminate.", "score": 0.8765}],
        },
    )
    r = client.post(f"/api/v1/contracts/{cid}/ask", json={"question": "Notice period?"})
    assert r.status_code == 200
    assert r.json() == {
        "answer": "30 days",
        "evidence": [{"text": "Either party may terminate.", "page": None, "similarity": 88}],
    }


def test_ask_errors(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    assert (
        client.post(f"/api/v1/contracts/{uuid.uuid4()}/ask", json={"question": "hi"}).status_code
        == 404
    )
    cid = _upload_txt(client)
    assert client.post(f"/api/v1/contracts/{cid}/ask", json={"question": "hi"}).status_code == 409
    cid2 = _analyzed(client, monkeypatch)
    assert client.post(f"/api/v1/contracts/{cid2}/ask", json={"question": "  "}).status_code == 422

    def boom(*a, **k):
        raise ml_client.MLServiceError("down")

    monkeypatch.setattr("app.api.v1.endpoints.contracts.ask_about_contract", boom)
    assert client.post(f"/api/v1/contracts/{cid2}/ask", json={"question": "hi"}).status_code == 502


def test_ask_reindexes_when_ml_holds_other_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_post(path: str, payload: dict) -> dict:
        calls.append(path)
        return {"extracted_text": "t", "clauses": []} if path == "/analyze" else {"answer": "a"}

    monkeypatch.setattr(ml_client, "_post", fake_post)
    a, b = uuid.uuid4(), uuid.uuid4()
    ml_client.analyze_and_index(a, "text")
    calls.clear()
    ml_client.ask_about_contract(a, "text", "q")
    assert calls == ["/ask"]  # already indexed -> no re-analyze
    calls.clear()
    ml_client.ask_about_contract(b, "text", "q")
    assert calls == ["/analyze", "/ask"]  # different contract -> rebuild index first


def test_ask_retries_after_ml_restart(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_post(path: str, payload: dict) -> dict:
        calls.append(path)
        if path == "/ask" and calls.count("/ask") == 1:
            raise ml_client.MLServiceError("no index", status_code=422)
        return {"extracted_text": "t", "clauses": []} if path == "/analyze" else {"answer": "a"}

    monkeypatch.setattr(ml_client, "_post", fake_post)
    cid = uuid.uuid4()
    ml_client.analyze_and_index(cid, "text")
    calls.clear()
    assert ml_client.ask_about_contract(cid, "text", "q")["answer"] == "a"
    assert calls == ["/ask", "/analyze", "/ask"]


def test_entity_mapping_filters_noise_and_reads_spelled_notice() -> None:
    from app.utils.analysis_view import _entities

    raw = [
        {
            "type": "termination",
            "text": "Either Party may terminate by one (1) month's written notice.",
            "entities": [
                {"text": "Landlord", "label": "PERSON"},
                {"text": "ENTIRE AGREEMENT", "label": "ORG"},
                {"text": "Maharashtra – 400050 Hereinafter", "label": "ORG"},
                {"text": "Vikram Desai", "label": "PERSON"},
            ],
        }
    ]
    ents = _entities(raw)
    assert [p["name"] for p in ents["parties"].values()] == ["Vikram Desai"]
    assert ents["notice_periods"][0]["value"] == "one (1) month"


def test_malformed_stored_clauses_do_not_break_history_or_analysis(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    good = _analyzed(client, monkeypatch)
    bad = _upload_txt(client)
    # PATCH accepts free-form JSON, so a non-ML shape can end up stored.
    client.patch(
        f"/api/v1/contracts/{bad}/extraction",
        json={"extracted_text": "x", "clauses": ["just a string", 7, {"risk": "oops"}, {"text": "ok"}]},
    )
    r = client.get("/api/v1/contracts")
    assert r.status_code == 200
    assert {i["id"] for i in r.json()} == {good, bad}
    assert client.get(f"/api/v1/contracts/{bad}/analysis").status_code == 200


def test_oversized_upload_rejected_without_full_read(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)
    big = b"a" * (1024 * 1024 + 10)
    r = client.post("/api/v1/contracts/upload", files={"file": ("big.txt", io.BytesIO(big), "text/plain")})
    assert r.status_code == 400
    assert "exceeds" in r.json()["detail"]


# --- hardening: fixes from the backend audit ---------------------------------

import json
from pathlib import Path

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "ml_analyze_sample.json").read_text())


def test_real_ml_response_shape_flows_through_endpoints(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pins the ACTUAL ML /analyze output (captured from the running service) so a
    change in the ML team's response format breaks CI instead of production."""
    monkeypatch.setattr(ml_client, "_post", lambda path, payload: FIXTURE)
    cid = _upload_txt(client)
    assert client.post(f"/api/v1/contracts/{cid}/analyze").status_code == 200
    body = client.get(f"/api/v1/contracts/{cid}/analysis").json()
    assert len(body["clauses"]) == FIXTURE["clause_count"]
    assert {c["risk_label"] for c in body["clauses"]} <= {"LOW", "MEDIUM", "HIGH"}
    assert all(0 <= c["risk_score"] <= 100 for c in body["clauses"])
    # Shape only: entity QUALITY is ML's domain (e.g. spaCy misses "Rs. 35,000" as MONEY).
    assert set(body["entities"]) == {"parties", "rent", "deposit", "money_mentions", "dates", "notice_periods"}


def test_extract_only_status_is_extracted_not_processed(client: TestClient) -> None:
    cid = _upload_txt(client)
    body = client.post(f"/api/v1/contracts/{cid}/extract").json()
    assert body["status"] == "extracted"
    assert client.get("/api/v1/contracts").json() == []  # not analyzed -> not in history


def test_patch_extraction_rejects_non_list_clauses(client: TestClient) -> None:
    cid = _upload_txt(client)
    r = client.patch(
        f"/api/v1/contracts/{cid}/extraction", json={"extracted_text": "x", "clauses": {"a": 1}}
    )
    assert r.status_code == 422


def test_ask_rejects_oversized_question(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    cid = _analyzed(client, monkeypatch)
    r = client.post(f"/api/v1/contracts/{cid}/ask", json={"question": "q" * 1001})
    assert r.status_code == 422


def test_ml_errors_do_not_leak_internal_url(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*a, **k):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(ml_client.httpx, "post", boom)
    cid = _upload_txt(client)
    r = client.post(f"/api/v1/contracts/{cid}/analyze")
    assert r.status_code == 502
    assert "localhost" not in r.json()["detail"]


def test_history_pagination(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    ids = [_analyzed(client, monkeypatch) for _ in range(3)]
    full = [i["id"] for i in client.get("/api/v1/contracts").json()]
    assert sorted(full) == sorted(ids)
    assert [i["id"] for i in client.get("/api/v1/contracts?limit=2").json()] == full[:2]
    assert [i["id"] for i in client.get("/api/v1/contracts?limit=2&offset=2").json()] == full[2:]
    assert client.get("/api/v1/contracts?limit=0").status_code == 422


def test_upload_failure_leaves_no_orphan_file(
    client: TestClient, db_session, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fail_commit() -> None:
        raise RuntimeError("db down")

    monkeypatch.setattr(db_session, "commit", fail_commit)
    with pytest.raises(RuntimeError):
        client.post(
            "/api/v1/contracts/upload",
            files={"file": ("c.txt", io.BytesIO(b"hello"), "text/plain")},
        )
    storage = tmp_path / "storage"
    assert not storage.exists() or list(storage.iterdir()) == []


def test_ml_busy_returns_503(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    cid = _analyzed(client, monkeypatch)
    monkeypatch.setattr(settings, "ML_LOCK_TIMEOUT_SECONDS", 0.05)
    assert ml_client._lock.acquire(timeout=1)  # simulate a slow in-flight ML request
    try:
        r = client.post(f"/api/v1/contracts/{cid}/ask", json={"question": "hi"})
        assert r.status_code == 503
    finally:
        ml_client._lock.release()


def test_reindex_every_ask_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    calls: list[str] = []

    def fake_post(path: str, payload: dict) -> dict:
        calls.append(path)
        return {"extracted_text": "t", "clauses": []} if path == "/analyze" else {"answer": "a"}

    monkeypatch.setattr(ml_client, "_post", fake_post)
    cid = uuid.uuid4()
    ml_client.analyze_and_index(cid, "text")
    calls.clear()
    monkeypatch.setattr(settings, "ML_REINDEX_EVERY_ASK", True)
    ml_client.ask_about_contract(cid, "text", "q")
    assert calls == ["/analyze", "/ask"]  # re-indexed even though cid was already indexed
