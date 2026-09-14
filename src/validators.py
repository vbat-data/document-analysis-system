"""Business rules for document validation."""
from src.schemas import DocumentType, ExtractedEntity, ValidationResult

# Required entity types per document type
REQUIRED_FIELDS: dict[DocumentType, list[str]] = {
    DocumentType.CONTRACT: ["ORG", "DATE"],
    DocumentType.INVOICE: ["ORG", "DATE", "MONEY"],
    DocumentType.ACT: ["ORG", "DATE"],
    DocumentType.UNKNOWN: [],
}


def validate_entities(
    entities: list[ExtractedEntity],
    doc_type: DocumentType,
) -> ValidationResult:
    """Check that a document contains all required entity types."""
    required = REQUIRED_FIELDS.get(doc_type, [])
    found = {e.entity_type for e in entities}

    missing = [field for field in required if field not in found]
    warnings: list[str] = []

    # Low-confidence warning
    for e in entities:
        if e.confidence < 0.7:
            warnings.append(f"Low confidence for '{e.entity_type}': {e.confidence}")
            break

    return ValidationResult(
        is_valid=not missing,
        missing_fields=missing,
        warnings=warnings,
    )