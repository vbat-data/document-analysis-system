"""Tests for document processing logic."""
from pathlib import Path

import pytest

from src.document_processor import (
    classify_document,
    generate_document_id,
    parse_document,
)
from src.schemas import DocumentType


def test_generate_document_id_is_unique():
    """100 IDs should all be distinct."""
    ids = {generate_document_id() for _ in range(100)}
    assert len(ids) == 100


def test_generate_document_id_has_prefix():
    """ID starts with 'doc_'."""
    doc_id = generate_document_id()
    assert doc_id.startswith("doc_")
    assert len(doc_id) == 14  # "doc_" + 10 hex chars


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Договор поставки №123", DocumentType.CONTRACT),
        ("Счёт на оплату товара", DocumentType.INVOICE),
        ("Акт выполненных работ", DocumentType.ACT),
        ("Произвольный текст без ключевых слов", DocumentType.UNKNOWN),
    ],
)
def test_classify_document(text: str, expected: DocumentType):
    """Document classification by keywords."""
    assert classify_document(text) == expected


def test_parse_document_with_unsupported_extension(tmp_path: Path):
    """Unsupported formats raise ValueError."""
    file_path = tmp_path / "note.txt"
    file_path.write_text("hello")

    with pytest.raises(ValueError, match="Unsupported file format"):
        parse_document(file_path)


def test_parse_docx(tmp_path: Path):
    """Parsing a real DOCX file works."""
    from docx import Document

    docx_path = tmp_path / "sample.docx"
    doc = Document()
    doc.add_paragraph("Договор №42 от 01.01.2024")
    doc.add_paragraph("Поставщик: ООО Ромашка")
    doc.save(docx_path)

    text = parse_document(docx_path)
    assert "Договор" in text
    assert "Ромашка" in text