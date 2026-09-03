"""Tests for the contract upload / retrieval / extraction-storage endpoints."""

import io

import pytest
from fastapi.testclient import TestClient

PDF_BYTES = b"%PDF-1.4\n%mock pdf content for tests\n"
DOCX_BYTES = b"PK\x03\x04" + b"mock docx (zip) content for tests"


def test_upload_pdf_succeeds(client: TestClient) -> None:
    response = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("sample.pdf", io.BytesIO(PDF_BYTES), "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "sample.pdf"
    assert body["status"] == "uploaded"
    assert body["extracted_text"] is None


def test_upload_docx_succeeds(client: TestClient) -> None:
    response = client.post(
        "/api/v1/contracts/upload",
        files={
            "file": (
                "agreement.docx",
                io.BytesIO(DOCX_BYTES),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert response.status_code == 201
    assert response.json()["filename"] == "agreement.docx"


def test_upload_rejects_unsupported_extension(client: TestClient) -> None:
    response = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("virus.exe", io.BytesIO(b"whatever"), "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_rejects_empty_file(client: TestClient) -> None:
    response = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_rejects_mismatched_signature(client: TestClient) -> None:
    """A .pdf extension whose content isn't actually a PDF should be rejected."""
    response = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("fake.pdf", io.BytesIO(b"not really a pdf"), "application/pdf")},
    )
    assert response.status_code == 400
    assert "does not match" in response.json()["detail"]


def test_upload_rejects_oversized_file(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0)  # anything is "too big" now
    response = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("sample.pdf", io.BytesIO(PDF_BYTES), "application/pdf")},
    )
    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"]


def test_upload_sanitizes_path_traversal_filename(client: TestClient) -> None:
    """Both '/' and '\\' path components in a filename must be stripped, not just the host OS's separator."""
    response = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("..\\..\\etc\\evil.pdf", io.BytesIO(PDF_BYTES), "application/pdf")},
    )
    assert response.status_code == 201
    assert response.json()["filename"] == "evil.pdf"


def test_get_contract_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/contracts/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_store_extraction_updates_contract(client: TestClient) -> None:
    upload = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("sample.pdf", io.BytesIO(PDF_BYTES), "application/pdf")},
    )
    contract_id = upload.json()["id"]

    response = client.patch(
        f"/api/v1/contracts/{contract_id}/extraction",
        json={
            "extracted_text": "This agreement is entered into...",
            "clauses": [{"type": "termination", "text": "Either party may terminate..."}],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["extracted_text"].startswith("This agreement")
    assert body["clauses"][0]["type"] == "termination"

    # Confirm it's actually persisted, not just echoed back in the response.
    fetched = client.get(f"/api/v1/contracts/{contract_id}")
    assert fetched.json()["clauses"][0]["type"] == "termination"


def test_store_extraction_not_found(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/contracts/00000000-0000-0000-0000-000000000000/extraction",
        json={"extracted_text": "text", "clauses": None},
    )
    assert response.status_code == 404
