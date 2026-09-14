"""API endpoints."""
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.config import settings
from src.database import DocumentRecord, get_db
from src.document_processor import analyze, generate_document_id, parse_document
from src.ml_models import get_ner_model
from src.schemas import (
    DocumentAnalysisResponse,
    DocumentListItem,
    HealthResponse,
    ProcessingStatus,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        models_loaded=get_ner_model().is_loaded,
    )


@router.post(
    "/documents/upload",
    response_model=DocumentAnalysisResponse,
    tags=["documents"],
)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentAnalysisResponse:
    """Upload and analyze a document."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Allowed: {sorted(settings.supported_formats)}",
        )

    content = file.file.read()  # <-- без await, теперь обычный read
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max: {settings.max_file_size_mb} MB",
        )

    document_id = generate_document_id()
    save_path = settings.upload_dir / f"{document_id}{ext}"
    save_path.write_bytes(content)

    try:
        text = parse_document(save_path)
        entities, doc_type, validation, elapsed = analyze(text, get_ner_model())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Processing error: {exc}") from exc

    record = DocumentRecord(
        document_id=document_id,
        filename=file.filename or "unknown",
        document_type=doc_type.value,
        entities=[e.model_dump() for e in entities],
        is_valid=validation.is_valid,
        processing_time=elapsed,
    )
    db.add(record)
    db.commit()

    return DocumentAnalysisResponse(
        document_id=document_id,
        filename=file.filename or "unknown",
        status=ProcessingStatus.COMPLETED,
        document_type=doc_type,
        entities=entities,
        validation=validation,
        processing_time_sec=elapsed,
    )


@router.get("/documents", response_model=list[DocumentListItem], tags=["documents"])
def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[DocumentListItem]:
    """List processed documents."""
    records = (
        db.query(DocumentRecord)
        .order_by(DocumentRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [DocumentListItem.model_validate(r) for r in records]


@router.get(
    "/documents/{document_id}",
    response_model=DocumentAnalysisResponse,
    tags=["documents"],
)
def get_document(document_id: str, db: Session = Depends(get_db)) -> DocumentAnalysisResponse:
    """Get a single document by ID."""
    record = (
        db.query(DocumentRecord)
        .filter(DocumentRecord.document_id == document_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentAnalysisResponse(
        document_id=record.document_id,
        filename=record.filename,
        status=ProcessingStatus.COMPLETED,
        document_type=record.document_type,
        entities=record.entities,
        validation={"is_valid": record.is_valid, "missing_fields": [], "warnings": []},
        processing_time_sec=record.processing_time,
    )