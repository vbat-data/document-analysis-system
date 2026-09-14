"""Tests for business validation rules."""
from src.schemas import DocumentType, ExtractedEntity
from src.validators import validate_entities


def _entity(entity_type: str, value: str = "x", confidence: float = 0.9) -> ExtractedEntity:
    """Helper to build an ExtractedEntity quickly."""
    return ExtractedEntity(entity_type=entity_type, value=value, confidence=confidence)


def test_valid_when_all_fields_present():
    """Contract with all required entities is valid."""
    entities = [_entity("ORG"), _entity("DATE")]
    result = validate_entities(entities, DocumentType.CONTRACT)

    assert result.is_valid is True
    assert result.missing_fields == []


def test_invalid_when_field_missing():
    """Contract without DATE is invalid."""
    entities = [_entity("ORG")]
    result = validate_entities(entities, DocumentType.CONTRACT)

    assert result.is_valid is False
    assert "DATE" in result.missing_fields


def test_low_confidence_produces_warning():
    """Entity with low confidence produces a warning."""
    entities = [_entity("ORG", confidence=0.4), _entity("DATE")]
    result = validate_entities(entities, DocumentType.CONTRACT)

    assert result.is_valid is True  # все поля есть
    assert len(result.warnings) == 1
    assert "ORG" in result.warnings[0]


def test_unknown_document_type_has_no_requirements():
    """Unknown documents require nothing."""
    result = validate_entities([], DocumentType.UNKNOWN)
    assert result.is_valid is True


def test_invoice_requires_money():
    """Invoice requires ORG, DATE, MONEY."""
    entities = [_entity("ORG"), _entity("DATE")]
    result = validate_entities(entities, DocumentType.INVOICE)

    assert result.is_valid is False
    assert "MONEY" in result.missing_fields