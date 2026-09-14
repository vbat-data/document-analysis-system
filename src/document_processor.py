"""Document parsing and analysis pipeline."""
import re
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

DOCUMENT_KEYWORDS: dict[DocumentType, tuple[str, ...]] = {
    DocumentType.CONTRACT: ("договор", "контракт"),
    DocumentType.INVOICE: ("счёт", "счет", "invoice"),
    DocumentType.ACT: ("акт", "выполненных работ"),
}

# --- Regex patterns for structured entities ---------------------------------
DATE_PATTERN = re.compile(r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b")

MONEY_PATTERN = re.compile(
    r"\b((?:\d{1,3}(?:[\s\u00A0]\d{3})*|\d+)(?:[.,]\d{1,2})?\s*"
    r"(?:руб\.?|рубл(?:ей|я|ь)|₽|RUB|USD|EUR|\$|€))",
    re.IGNORECASE,
)


def parse_pdf(file_path: Path) -> str:
    import pdfplumber

    parts: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
    return "\n".join(parts)


def parse_docx(file_path: Path) -> str:
    from docx import Document

    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text)


def parse_xlsx(file_path: Path) -> str:
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
    ext = file_path.suffix.lower()
    parser = PARSERS.get(ext)
    if not parser:
        raise ValueError(f"Unsupported file format: {ext}")
    return parser(file_path)


def generate_document_id() -> str:
    return f"doc_{uuid.uuid4().hex[:10]}"


def classify_document(text: str) -> DocumentType:
    lowered = text.lower()
    for doc_type, keywords in DOCUMENT_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            return doc_type
    return DocumentType.UNKNOWN


def extract_regex_entities(text: str) -> list[ExtractedEntity]:
    """Extract DATE and MONEY via deterministic regex patterns.

    NER models typically don't detect numeric/monetary entities reliably,
    so we complement ML output with regex.
    """
    entities: list[ExtractedEntity] = []

    for match in DATE_PATTERN.finditer(text):
        entities.append(
            ExtractedEntity(
                entity_type="DATE",
                value=match.group(1),
                confidence=0.95,
            )
        )

    for match in MONEY_PATTERN.finditer(text):
        entities.append(
            ExtractedEntity(
                entity_type="MONEY",
                value=match.group(1).strip(),
                confidence=0.92,
            )
        )

    return entities


def analyze(
    text: str,
    ner_model: NERModel,
) -> tuple[list[ExtractedEntity], DocumentType, ValidationResult, float]:
    """Run full analysis: ML entities + regex entities, then validate."""
    start = time.perf_counter()

    doc_type = classify_document(text)

    # ML-based NER (organizations, people, locations)
    raw_entities = ner_model.extract(text)
    ml_entities = [ExtractedEntity(**e) for e in raw_entities]

    # Regex-based extraction (dates, money)
    regex_entities = extract_regex_entities(text)

    # Merge + deduplicate by (type, lowercase value)
    seen: set[tuple[str, str]] = set()
    all_entities: list[ExtractedEntity] = []
    for entity in ml_entities + regex_entities:
        key = (entity.entity_type, entity.value.lower())
        if key not in seen:
            seen.add(key)
            all_entities.append(entity)

    validation = validate_entities(all_entities, doc_type)

    elapsed = round(time.perf_counter() - start, 3)
    return all_entities, doc_type, validation, elapsed