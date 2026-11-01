"""Contract endpoints: upload, retrieval, text extraction, and storing NLP/ML output.

  POST  /contracts/upload              -> "Create upload API" + "Validate uploaded file"
  GET   /contracts/{id}                -> read back a stored contract
  POST  /contracts/{id}/extract        -> "Store extracted information" (raw text side):
                                           pulls text straight out of the stored file
                                           ourselves (PDF/DOCX/TXT) so this doesn't have
                                           to wait on NLP/ML's pipeline. No clause
                                           identification happens here.
  POST  /contracts/{id}/analyze        -> extracts text if needed, sends it to the ML
                                           service (/analyze), and stores the clauses
  PATCH /contracts/{id}/extraction     -> "Store extracted information" (clauses side):
                                           called by the NLP/ML pipeline once it has
                                           identified clauses (and/or wants to override
                                           the extracted text with their own version)
"""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.models.contract import Contract
from app.schemas.analysis import AnalysisOut, AskOut, AskRequest, EvidenceOut, HistoryItem
from app.schemas.contract import ContractExtractionUpdate, ContractOut
from app.utils.analysis_view import build_analysis, build_history_item, is_analyzed
from app.utils.file_validation import FileValidationError, sanitize_filename, validate_upload
from app.utils.ml_client import MLBusyError, MLServiceError, analyze_and_index, ask_about_contract
from app.utils.storage import save_upload
from app.utils.text_extraction import TextExtractionError, extract_text

logger = logging.getLogger(__name__)

router = APIRouter()

# Client-facing text for ML failures; the real error (incl. internal URL) is logged only.
_ML_ERROR_DETAIL = "The analysis service is unavailable or returned an error. Please try again."


@router.post("/upload", response_model=ContractOut, status_code=status.HTTP_201_CREATED)
async def upload_contract(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Contract:
    """Upload a contract file (PDF/DOCX/TXT).

    Validates size/extension/content-signature, stores it on disk under a
    generated name, and creates the Contract row that later steps (NLP/ML
    extraction, then PATCH .../extraction below) fill in.
    """
    # Read at most limit+1 bytes: enough for validate_upload to reject an
    # oversized file without buffering an arbitrarily large body in memory.
    content = await file.read(settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)
    safe_name = sanitize_filename(file.filename or "")

    try:
        validate_upload(filename=safe_name, content=content)
    except FileValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    stored_path = save_upload(content=content, sanitized_filename=safe_name)

    contract = Contract(
        filename=safe_name,
        storage_path=str(stored_path),
        content_type=file.content_type,
        status="uploaded",
    )
    db.add(contract)
    try:
        db.commit()
    except Exception:
        db.rollback()
        stored_path.unlink(missing_ok=True)  # don't leave an orphan file with no DB row
        raise
    db.refresh(contract)
    logger.info("Contract uploaded: id=%s filename=%s", contract.id, safe_name)
    return contract


@router.get("", response_model=list[HistoryItem])
def list_contracts(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[HistoryItem]:
    """History: analyzed contracts, newest first, with their risk summary.

    `limit`/`offset` page over *analyzed* contracts (un-analyzed uploads are skipped).
    """
    items: list[HistoryItem] = []
    skipped = 0
    rows = db.query(Contract).order_by(Contract.created_at.desc()).yield_per(50)
    for c in rows:
        if not is_analyzed(c):
            continue
        if skipped < offset:
            skipped += 1
            continue
        try:
            items.append(build_history_item(c))
        except Exception:  # noqa: BLE001 - one malformed row must not break history for everyone
            logger.warning("Skipping contract %s in history: unreadable clauses", c.id)
            continue
        if len(items) >= limit:
            break
    return items


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(contract_id: uuid.UUID, db: Session = Depends(get_db)) -> Contract:
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")
    return contract


@router.post("/{contract_id}/extract", response_model=ContractOut)
def extract_contract_text(contract_id: uuid.UUID, db: Session = Depends(get_db)) -> Contract:
    """Pull raw text out of the stored file and persist it.

    Basic text extraction only (PyMuPDF for PDF, python-docx for DOCX, plain
    decode for TXT) — no clause identification. That's NLP/ML's "Identify
    basic clauses" task, stored separately via PATCH .../extraction once
    their pipeline exists.
    """
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")

    try:
        text = extract_text(Path(contract.storage_path))
    except TextExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    contract.extracted_text = text
    contract.status = "extracted"  # text only; "processed" means clauses are stored too
    db.commit()
    db.refresh(contract)
    logger.info("Contract text extracted: id=%s chars=%d", contract.id, len(text))
    return contract


@router.post("/{contract_id}/analyze", response_model=ContractOut)
def analyze_contract(contract_id: uuid.UUID, db: Session = Depends(get_db)) -> Contract:
    """Run the full pipeline: file -> raw text -> ML clause analysis -> stored.

    Uses already-extracted text if present, otherwise extracts it first.
    422 if the file can't be parsed; 502 if the ML service is down or bad.
    """
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")

    text = contract.extracted_text
    if not text:
        try:
            text = extract_text(Path(contract.storage_path))
        except TextExtractionError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc

    try:
        result = analyze_and_index(contract.id, text)
    except MLBusyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except MLServiceError as exc:
        logger.error("ML analysis failed: id=%s error=%s", contract.id, exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=_ML_ERROR_DETAIL) from exc

    contract.extracted_text = result["extracted_text"]
    contract.clauses = result["clauses"]
    contract.status = "processed"
    db.commit()
    db.refresh(contract)
    logger.info("Contract analyzed: id=%s clauses=%d", contract.id, len(result["clauses"] or []))
    return contract


@router.get("/{contract_id}/analysis", response_model=AnalysisOut)
def get_analysis(contract_id: uuid.UUID, db: Session = Depends(get_db)) -> AnalysisOut:
    """Frontend view of a contract's ML results: clauses, risk summary, entities.

    409 if the contract hasn't been run through POST .../analyze yet.
    """
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")
    if not is_analyzed(contract):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contract has not been analyzed yet. POST .../analyze first.",
        )
    return build_analysis(contract)


@router.post("/{contract_id}/ask", response_model=AskOut)
def ask_contract(contract_id: uuid.UUID, payload: AskRequest, db: Session = Depends(get_db)) -> AskOut:
    """Ask a natural-language question about one contract (answered by the ML service's RAG)."""
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Question must not be empty.")

    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")
    if not contract.extracted_text or not is_analyzed(contract):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contract has not been analyzed yet. POST .../analyze first.",
        )

    try:
        data = ask_about_contract(contract.id, contract.extracted_text, question)
    except MLBusyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except MLServiceError as exc:
        logger.error("ML ask failed: id=%s error=%s", contract.id, exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=_ML_ERROR_DETAIL) from exc

    return AskOut(
        answer=str(data["answer"]),
        evidence=[
            EvidenceOut(text=str(s.get("text", "")), similarity=round(max(float(s.get("score", 0)), 0) * 100))
            for s in data.get("sources", [])
        ],
    )


# TODO: once JWT auth lands, this should require either an authenticated
# service/role (it's meant to be called by the NLP/ML pipeline, not end
# users directly) rather than being open like every other endpoint today.
@router.patch("/{contract_id}/extraction", response_model=ContractOut)
def store_extraction(
    contract_id: uuid.UUID,
    payload: ContractExtractionUpdate,
    db: Session = Depends(get_db),
) -> Contract:
    """Persist NLP/ML's extracted text + clauses for a contract and mark it processed."""
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")

    contract.extracted_text = payload.extracted_text
    contract.clauses = payload.clauses
    contract.status = "processed"
    db.commit()
    db.refresh(contract)
    logger.info("Contract extraction stored: id=%s", contract.id)
    return contract
