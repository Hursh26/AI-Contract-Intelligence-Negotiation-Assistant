"""Tests for POST /contracts/{id}/extract (raw text extraction, no clause identification)."""

import io

import pymupdf
from docx import Document
from fastapi.testclient import TestClient


def _make_pdf_bytes(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def _make_docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_extract_pdf_text(client: TestClient) -> None:
    pdf_bytes = _make_pdf_bytes("This Employment Agreement is entered into by the parties.")
    upload = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    contract_id = upload.json()["id"]

    response = client.post(f"/api/v1/contracts/{contract_id}/extract")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert "Employment Agreement" in body["extracted_text"]
    assert body["clauses"] is None  # extraction never touches clauses — that's NLP/ML's job


def test_extract_docx_text(client: TestClient) -> None:
    docx_bytes = _make_docx_bytes("This NDA is between the disclosing and receiving party.")
    upload = client.post(
        "/api/v1/contracts/upload",
        files={
            "file": (
                "nda.docx",
                io.BytesIO(docx_bytes),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    contract_id = upload.json()["id"]

    response = client.post(f"/api/v1/contracts/{contract_id}/extract")
    assert response.status_code == 200
    assert "NDA" in response.json()["extracted_text"]


def test_extract_txt_text(client: TestClient) -> None:
    upload = client.post(
        "/api/v1/contracts/upload",
        files={"file": ("notes.txt", io.BytesIO(b"Plain text contract body."), "text/plain")},
    )
    contract_id = upload.json()["id"]

    response = client.post(f"/api/v1/contracts/{contract_id}/extract")
    assert response.status_code == 200
    assert response.json()["extracted_text"] == "Plain text contract body."


def test_extract_not_found(client: TestClient) -> None:
    response = client.post("/api/v1/contracts/00000000-0000-0000-0000-000000000000/extract")
    assert response.status_code == 404


def test_extract_unparseable_pdf_returns_422(client: TestClient) -> None:
    # Passes upload's magic-byte check (starts with %PDF-) but isn't a real,
    # parseable PDF structure — extraction itself should fail cleanly (422),
    # not 500.
    upload = client.post(
        "/api/v1/contracts/upload",
        files={
            "file": (
                "broken.pdf",
                io.BytesIO(b"%PDF-1.4\nnot a real pdf body, just garbage bytes after the header"),
                "application/pdf",
            )
        },
    )
    contract_id = upload.json()["id"]

    response = client.post(f"/api/v1/contracts/{contract_id}/extract")
    assert response.status_code == 422
