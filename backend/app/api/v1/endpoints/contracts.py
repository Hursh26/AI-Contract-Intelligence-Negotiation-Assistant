"""Contract endpoints: upload, retrieval, text extraction, and storing NLP/ML output.

  POST  /contracts/upload              -> "Create upload API" + "Validate uploaded file"
  GET   /contracts/{id}                -> read back a stored contract
  POST  /contracts/{id}/extract        -> "Store extracted information" (raw text side):
                                           pulls text straight out of the stored file
                                           ourselves (PDF/DOCX/TXT) so this doesn't have
                                           to wait on NLP/ML's pipeline. No clause
                                           identification happens here.
  PATCH /contracts/{id}/extraction     -> "Store extracted information" (clauses side):
                                           called by the NLP/ML pipeline once it has
                                           identified clauses (and/or wants to override
                                           the extracted text with their own version)
"""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.contract import Contract
from app.schemas.contract import ContractExtractionUpdate, ContractOut
from app.utils.file_validation import FileValidationError, sanitize_filename, validate_upload
from app.utils.storage import save_upload
from app.utils.text_extraction import TextExtractionError, extract_text

logger = logging.getLogger(__name__)

router = APIRouter()


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
    content = await file.read()
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
    db.commit()
    db.refresh(contract)
    logger.info("Contract uploaded: id=%s filename=%s", contract.id, safe_name)
    return contract


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
    contract.status = "processed"
    db.commit()
    db.refresh(contract)
    logger.info("Contract text extracted: id=%s chars=%d", contract.id, len(text))
    return contract


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
