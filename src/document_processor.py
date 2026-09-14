"""Document parsing and analysis pipeline."""
import time
import uuid
from pathlib import Path

from src.ml_models import NERModel
from src.schemas import (
    DocumentType,
    ExtractedEntity,
    ValidationResult,
)
from src.validators import validate_entities

# Keywords for simple rule-based document classification
DOCUMENT_KEYWORDS: dict[DocumentType, tuple[str, ...]] = {
    DocumentType.CONTRACT: ("договор", "контракт"),
    DocumentType.INVOICE: ("счёт", "счет", "invoice"),
    DocumentType.ACT: ("акт", "выполненных работ"),
}


def generate_document_id() -> str:
    """Generate a short unique document ID."""
    return f"doc_{uuid.uuid4().hex[:10]}"


def parse_pdf(file_path: Path) -> str:
    """Extract text from a PDF file."""
    import pdfplumber

    parts: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
    return "\n".join(parts)


def parse_docx(file_path: Path) -> str:
    """Extract text from a DOCX file."""
    from docx import Document

    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text)


def parse_xlsx(file_path: Path) -> str:
    """Extract text from an XLSX file."""
    import pandas as pd

    sheets = pd.read_excel(file_path, sheet_name=None)
    parts: list[str] = []
    for name, df in sheets.items():
        parts.append(f"=== {name} ===")
        parts.append(df.to_string(index=False))
    return "\n".join(parts)


PARSERS = {
    ".pdf": parse_pdf,
    ".docx": parse_docx,
    ".xlsx": parse_xlsx,
}


def parse_document(file_path: Path) -> str:
    """Route file to the correct parser based on extension."""
    ext = file_path.suffix.lower()
    parser = PARSERS.get(ext)
    if not parser:
        raise ValueError(f"Unsupported file format: {ext}")
    return parser(file_path)


def classify_document(text: str) -> DocumentType:
    """Classify document type using keyword matching."""
    lowered = text.lower()
    for doc_type, keywords in DOCUMENT_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return doc_type
    return DocumentType.UNKNOWN


def analyze(
    text: str,
    ner_model: NERModel,
) -> tuple[list[ExtractedEntity], DocumentType, ValidationResult, float]:
    """Run the full analysis pipeline on raw text."""
    start = time.perf_counter()

    doc_type = classify_document(text)
    raw_entities = ner_model.extract(text)
    entities = [ExtractedEntity(**e) for e in raw_entities]
    validation = validate_entities(entities, doc_type)

    elapsed = round(time.perf_counter() - start, 3)
    return entities, doc_type, validation, elapsed