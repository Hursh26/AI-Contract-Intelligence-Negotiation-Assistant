"""Pull raw text out of a stored contract file (PDF / DOCX / TXT).

Deliberately minimal: this ONLY extracts raw text. It does not identify
clauses, summarize, or do anything NLP-flavored — that's the NLP/ML team's
"Identify basic clauses" task, done separately once their pipeline exists
(via PATCH /contracts/{id}/extraction). This exists so "Store extracted
information" has something real to store without waiting on that pipeline.
"""

from pathlib import Path

import pymupdf
from docx import Document


class TextExtractionError(ValueError):
    """Raised when text can't be pulled out of a stored file; the endpoint turns this into an HTTP 422."""


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".docx":
        return _extract_docx(path)
    if suffix == ".txt":
        return _extract_txt(path)

    raise TextExtractionError(f"No text extractor for file type '{suffix}'.")


def _extract_pdf(path: Path) -> str:
    try:
        with pymupdf.open(path) as doc:
            text = "\n".join(page.get_text() for page in doc).strip()
    except Exception as exc:  # noqa: BLE001 - normalize any parser failure into our own error type
        raise TextExtractionError(f"Could not parse '{path.name}' as a PDF: {exc}") from exc

    if not text:
        raise TextExtractionError(f"No extractable text found in '{path.name}'.")
    return text


def _extract_docx(path: Path) -> str:
    try:
        document = Document(str(path))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    except Exception as exc:  # noqa: BLE001
        raise TextExtractionError(f"Could not parse '{path.name}' as a DOCX: {exc}") from exc

    if not text:
        raise TextExtractionError(f"No extractable text found in '{path.name}'.")
    return text


def _extract_txt(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        raise TextExtractionError(f"'{path.name}' is empty.")
    return text
