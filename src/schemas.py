"""Pydantic schemas for API requests and responses."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Supported document types."""

    CONTRACT = "contract"
    INVOICE = "invoice"
    ACT = "act"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Document processing statuses."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractedEntity(BaseModel):
    """A single extracted entity from a document."""

    entity_type: str = Field(..., description="Type of entity, e.g. 'DATE'")
    value: str = Field(..., description="Extracted text value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence")


class ValidationResult(BaseModel):
    """Validation results for a document."""

    is_valid: bool
    missing_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DocumentAnalysisResponse(BaseModel):
    """Response for document analysis."""

    document_id: str
    filename: str
    status: ProcessingStatus
    document_type: DocumentType
    entities: list[ExtractedEntity] = Field(default_factory=list)
    validation: ValidationResult
    processing_time_sec: float


class DocumentListItem(BaseModel):
    """Short info about a processed document."""

    document_id: str
    filename: str
    document_type: DocumentType
    status: ProcessingStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    models_loaded: bool