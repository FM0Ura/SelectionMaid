"""Unit tests for MetadataEnricher language detection, doc_type inference, title extraction,
and the full enrich() method.

Test structure:
  - TestDetectLanguage: language detection with langdetect, confidence threshold, exception handling.
  - TestInferDocType: keyword-based doc_type heuristics for legal, presentation, form, report, other.
  - TestExtractTitle: first H1 extraction, edge cases.
  - TestEnrich: full enrich() integration, all 9 DocumentMetadata fields.
  - TestEdgeCases: empty content, duplicate H1, UUID uniqueness, timezone awareness.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from langdetect import LangDetectException

from selection_maid.adapters.enricher.default import MetadataEnricher
from selection_maid.domain.models import DocumentChunk, DocumentMetadata, RawDocument


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_raw_document(
    content: str = "# Title\n\nContent here.",
    filename: str = "test.pdf",
    page_count: int = 1,
    fmt: str = "pdf",
) -> RawDocument:
    """Construct a minimal RawDocument for testing."""
    return RawDocument(
        content=content,
        filename=filename,
        page_count=page_count,
        format=fmt,
    )


def _make_chunk(index: int = 0, total: int = 1) -> DocumentChunk:
    """Construct a minimal DocumentChunk for testing."""
    return DocumentChunk(
        chunk_id=str(uuid.uuid4()),
        content="Chunk content.",
        page_start=0,
        page_end=0,
        section_title="Title",
        chunk_index=index,
        total_chunks=total,
        word_count=2,
    )


# ---------------------------------------------------------------------------
# TestDetectLanguage
# ---------------------------------------------------------------------------

class TestDetectLanguage:
    """Language detection uses langdetect with 0.8 confidence threshold (D-60, D-61, D-62)."""

    def test_detects_english(self) -> None:
        """Clearly English text returns 'en'."""
        enricher = MetadataEnricher()
        # Several English sentences about technology
        content = (
            "Machine learning is a subset of artificial intelligence that enables systems "
            "to learn from data and improve their performance over time without being explicitly "
            "programmed. Deep learning models have revolutionized natural language processing, "
            "computer vision, and many other fields. Modern software engineering practices "
            "emphasize code quality, automated testing, and continuous integration."
        )
        result = enricher._detect_language(content)
        assert result == "en"

    def test_detects_portuguese(self) -> None:
        """Clearly Portuguese text returns 'pt'."""
        enricher = MetadataEnricher()
        content = (
            "O aprendizado de máquina é uma área da inteligência artificial que permite aos "
            "sistemas aprender a partir de dados e melhorar seu desempenho ao longo do tempo "
            "sem serem explicitamente programados. Os modelos de aprendizado profundo "
            "revolucionaram o processamento de linguagem natural, a visão computacional e "
            "muitas outras áreas. As práticas modernas de engenharia de software enfatizam "
            "a qualidade do código, os testes automatizados e a integração contínua."
        )
        result = enricher._detect_language(content)
        assert result == "pt"

    def test_detects_spanish(self) -> None:
        """Clearly Spanish text returns 'es'."""
        enricher = MetadataEnricher()
        content = (
            "El aprendizaje automático es una rama de la inteligencia artificial que permite "
            "a los sistemas aprender de los datos y mejorar su rendimiento con el tiempo sin "
            "ser programados explícitamente. Los modelos de aprendizaje profundo han "
            "revolucionado el procesamiento del lenguaje natural, la visión por computadora "
            "y muchos otros campos. Las prácticas modernas de ingeniería de software hacen "
            "hincapié en la calidad del código, las pruebas automatizadas y la integración continua."
        )
        result = enricher._detect_language(content)
        assert result == "es"

    def test_returns_und_for_very_short_text(self) -> None:
        """When detect_langs returns a low-confidence result (below 0.8 threshold), 'und' is returned."""
        enricher = MetadataEnricher()
        # Simulate detect_langs returning a low-confidence language guess (e.g. 0.5 for "en")
        # by mocking the return value — the threshold check in _detect_language should reject it.
        from unittest.mock import MagicMock
        mock_lang = MagicMock()
        mock_lang.prob = 0.5  # below LANGUAGE_CONFIDENCE_THRESHOLD (0.8)
        mock_lang.lang = "en"
        with patch(
            "selection_maid.adapters.enricher.default.detect_langs",
            return_value=[mock_lang],
        ):
            result = enricher._detect_language("hi")
        assert result == "und"

    def test_returns_und_on_exception(self) -> None:
        """When langdetect.detect_langs raises LangDetectException, 'und' is returned (D-62)."""
        enricher = MetadataEnricher()
        with patch(
            "selection_maid.adapters.enricher.default.detect_langs",
            side_effect=LangDetectException(0, "mocked failure"),
        ):
            result = enricher._detect_language("some content that triggers an exception")
        assert result == "und"


# ---------------------------------------------------------------------------
# TestInferDocType
# ---------------------------------------------------------------------------

class TestInferDocType:
    """Doc type inference uses keyword heuristics on headings and structural analysis (D-63, D-64, D-65)."""

    def test_legal_from_heading_keyword(self) -> None:
        """Heading containing 'contrato' keyword → 'legal'."""
        enricher = MetadataEnricher()
        content = "# Contrato de Prestação de Serviços\n\nText describing the service agreement."
        result = enricher._infer_doc_type(content)
        assert result == "legal"

    def test_legal_from_clause_keyword(self) -> None:
        """Heading containing 'cláusula' keyword → 'legal'."""
        enricher = MetadataEnricher()
        content = "# Cláusula 1\n\nContent describing the terms and conditions."
        result = enricher._infer_doc_type(content)
        assert result == "legal"

    def test_presentation_from_slide_keyword(self) -> None:
        """Heading containing 'slide' keyword → 'presentation'."""
        enricher = MetadataEnricher()
        content = "# Slide 1\n\nContent of the first slide."
        result = enricher._infer_doc_type(content)
        assert result == "presentation"

    def test_presentation_from_agenda_keyword(self) -> None:
        """Heading containing 'agenda' keyword → 'presentation'."""
        enricher = MetadataEnricher()
        content = "# Agenda\n\nItems to be discussed in this meeting."
        result = enricher._infer_doc_type(content)
        assert result == "presentation"

    def test_form_detection(self) -> None:
        """Content with fill-in blanks and checkboxes → 'form'."""
        enricher = MetadataEnricher()
        content = "Nome: _____\n[ ] Option 1\n[ ] Option 2"
        result = enricher._infer_doc_type(content)
        assert result == "form"

    def test_report_detection(self) -> None:
        """Content with multiple tables and numbered sections → 'report'."""
        enricher = MetadataEnricher()
        content = (
            "# Executive Summary\n\n"
            "1. Introduction\n\n"
            "2. Findings\n\n"
            "| Column A | Column B |\n"
            "|----------|----------|\n"
            "| Data 1   | Data 2   |\n"
            "| Data 3   | Data 4   |\n"
        )
        result = enricher._infer_doc_type(content)
        assert result == "report"

    def test_defaults_to_other(self) -> None:
        """Content with no matching keywords falls back to 'other' (D-65)."""
        enricher = MetadataEnricher()
        content = "# Random Topic\n\nThis is some generic text without any specific keywords."
        result = enricher._infer_doc_type(content)
        assert result == "other"


# ---------------------------------------------------------------------------
# TestExtractTitle
# ---------------------------------------------------------------------------

class TestExtractTitle:
    """Title is extracted from the first H1 heading (D-66)."""

    def test_extracts_first_h1(self) -> None:
        """First H1 heading text is returned as the title."""
        enricher = MetadataEnricher()
        result = enricher._extract_title("# My Title\n\nContent")
        assert result == "My Title"

    def test_returns_empty_string_when_no_h1(self) -> None:
        """Document with H2 but no H1 returns empty string."""
        enricher = MetadataEnricher()
        result = enricher._extract_title("## Subtitle\n\nContent")
        assert result == ""

    def test_extracts_title_with_special_chars(self) -> None:
        """H1 with accented characters is extracted correctly."""
        enricher = MetadataEnricher()
        result = enricher._extract_title("# Título com Acentos\n\nContent")
        assert result == "Título com Acentos"

    def test_returns_empty_string_for_empty_content(self) -> None:
        """Empty content string returns empty string."""
        enricher = MetadataEnricher()
        result = enricher._extract_title("")
        assert result == ""


# ---------------------------------------------------------------------------
# TestEnrich
# ---------------------------------------------------------------------------

class TestEnrich:
    """Full enrich() integration tests — verifies all 9 DocumentMetadata fields (META-01)."""

    def test_enrich_returns_document_metadata(self) -> None:
        """enrich() returns a DocumentMetadata instance."""
        enricher = MetadataEnricher()
        raw = _make_raw_document()
        chunks = [_make_chunk(0, 1)]
        result = enricher.enrich(raw, chunks)
        assert isinstance(result, DocumentMetadata)

    def test_enrich_all_nine_fields_present(self) -> None:
        """All 9 DocumentMetadata fields are non-None."""
        enricher = MetadataEnricher()
        raw = _make_raw_document()
        chunks = [_make_chunk(0, 1)]
        result = enricher.enrich(raw, chunks)
        assert result.doc_id is not None
        assert result.source_filename is not None
        assert result.title is not None
        assert result.author is not None
        assert result.language is not None
        assert result.doc_type is not None
        assert result.page_count is not None
        assert result.chunk_count is not None
        assert result.ingested_at is not None

    def test_doc_id_is_valid_uuid4(self) -> None:
        """doc_id is a valid UUID v4 string (D-69)."""
        enricher = MetadataEnricher()
        raw = _make_raw_document()
        chunks = [_make_chunk()]
        result = enricher.enrich(raw, chunks)
        parsed = uuid.UUID(result.doc_id)
        assert parsed.version == 4

    def test_source_filename_matches_raw(self) -> None:
        """source_filename matches raw.filename (D-70)."""
        enricher = MetadataEnricher()
        raw = _make_raw_document(filename="my_document.pdf")
        chunks = [_make_chunk()]
        result = enricher.enrich(raw, chunks)
        assert result.source_filename == "my_document.pdf"

    def test_ingested_at_is_recent(self) -> None:
        """ingested_at is within 5 seconds of the current UTC time."""
        enricher = MetadataEnricher()
        raw = _make_raw_document()
        chunks = [_make_chunk()]
        before = datetime.now(timezone.utc)
        result = enricher.enrich(raw, chunks)
        after = datetime.now(timezone.utc)
        assert before <= result.ingested_at <= after or (
            (result.ingested_at - before).total_seconds() < 5
            and (after - result.ingested_at).total_seconds() < 5
        )

    def test_author_is_empty_string(self) -> None:
        """author is always '' (D-67)."""
        enricher = MetadataEnricher()
        raw = _make_raw_document()
        chunks = [_make_chunk()]
        result = enricher.enrich(raw, chunks)
        assert result.author == ""

    def test_chunk_count_matches_chunks_len(self) -> None:
        """chunk_count equals the number of chunks passed in."""
        enricher = MetadataEnricher()
        raw = _make_raw_document()
        chunks = [_make_chunk(i, 3) for i in range(3)]
        result = enricher.enrich(raw, chunks)
        assert result.chunk_count == 3

    def test_page_count_matches_raw(self) -> None:
        """page_count matches raw.page_count."""
        enricher = MetadataEnricher()
        raw = _make_raw_document(page_count=7)
        chunks = [_make_chunk()]
        result = enricher.enrich(raw, chunks)
        assert result.page_count == 7


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases for empty content, multiple H1s, UUID uniqueness, and timezone."""

    def test_empty_content_returns_und_language(self) -> None:
        """Empty content → language='und' (no detectable language)."""
        enricher = MetadataEnricher()
        raw = _make_raw_document(content="")
        chunks: list[DocumentChunk] = []
        result = enricher.enrich(raw, chunks)
        assert result.language == "und"

    def test_empty_content_title_is_empty(self) -> None:
        """Empty content → title=''."""
        enricher = MetadataEnricher()
        raw = _make_raw_document(content="")
        chunks: list[DocumentChunk] = []
        result = enricher.enrich(raw, chunks)
        assert result.title == ""

    def test_empty_content_doc_type_is_other(self) -> None:
        """Empty content → doc_type='other' (fallback, D-65)."""
        enricher = MetadataEnricher()
        raw = _make_raw_document(content="")
        chunks: list[DocumentChunk] = []
        result = enricher.enrich(raw, chunks)
        assert result.doc_type == "other"

    def test_two_h1_uses_first(self) -> None:
        """When document has two H1 headings, title is extracted from the first."""
        enricher = MetadataEnricher()
        content = "# First Title\n\n# Second Title\n\nContent"
        result = enricher._extract_title(content)
        assert result == "First Title"

    def test_doc_id_unique_per_call(self) -> None:
        """Each call to enrich() produces a different doc_id."""
        enricher = MetadataEnricher()
        raw = _make_raw_document()
        chunks = [_make_chunk()]
        result1 = enricher.enrich(raw, chunks)
        result2 = enricher.enrich(raw, chunks)
        assert result1.doc_id != result2.doc_id

    def test_ingested_at_is_timezone_aware(self) -> None:
        """ingested_at.tzinfo is not None (UTC datetime, D-68)."""
        enricher = MetadataEnricher()
        raw = _make_raw_document()
        chunks = [_make_chunk()]
        result = enricher.enrich(raw, chunks)
        assert result.ingested_at.tzinfo is not None
