"""MetadataEnricher — concrete MetadataEnricherPort implementation.

Receives a RawDocument and list[DocumentChunk] and returns a DocumentMetadata
object with all 9 META-01/02/03 fields populated:
  doc_id, source_filename, title, author, language, doc_type,
  page_count, chunk_count, ingested_at.

Language detection:
  Uses langdetect.detect_langs() on the full RawDocument.content (D-60, D-61).
  Only accepts the result if the top-candidate score >= LANGUAGE_CONFIDENCE_THRESHOLD.
  Any exception from langdetect is silently swallowed and "und" is returned (D-62).

doc_type inference (D-63, D-64, D-65):
  Keyword-based heuristic using multilingual PT/EN/ES keywords.
  Priority: legal > presentation > form > report > other.
  Closed vocabulary: article, report, presentation, form, legal, other.
  "article" is in the vocabulary but no heuristic produces it — no-match → "other".

Decision references:
  D-60: Use langdetect on full RawDocument.content.
  D-61: detect_langs() with score >= 0.8; else "und".
  D-62: Any langdetect exception → "und".
  D-63: Closed doc_type vocabulary.
  D-64: Multilingual keywords; form uses full-content scan.
  D-65: Default "other".
  D-66: title = first H1 line; "" if none.
  D-67: author always "".
  D-68: doc_id, source_filename, ingested_at, doc_type all required.
  D-69: doc_id = str(uuid.uuid4()).
  D-70: source_filename = raw.filename.
  D-71: File at src/selection_maid/adapters/enricher/default.py.
  D-72: Factory build_metadata_enricher(config: EnricherConfig) -> MetadataEnricher.
  D-73: EnricherConfig is empty in v1.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Final

import langdetect
from langdetect import detect_langs

from selection_maid.config import EnricherConfig
from selection_maid.domain.models import DocumentChunk, DocumentMetadata, RawDocument

# Minimum langdetect confidence score to accept the top-candidate language (D-61).
LANGUAGE_CONFIDENCE_THRESHOLD: Final[float] = 0.8

# Multilingual keywords per doc_type category (D-64).
# Keywords are matched case-insensitively against heading lines (lines starting
# with "#"), except for form indicators which are matched against the full content.
DOC_TYPE_KEYWORDS: Final[dict[str, list[str]]] = {
    "legal": [
        "cláusula",
        "contrato",
        "artigo",
        "parágrafo",
        "clause",
        "contract",
        "article",
        "whereas",
    ],
    "presentation": [
        "slide",
        "apresentação",
        "presentation",
        "agenda",
        "outline",
        "presentación",
    ],
}

# Form indicators matched against the full content string (D-64).
_FORM_INDICATORS: Final[list[str]] = [
    "_____",
    "[ ]",
    "Name:",
    "Nome:",
    "Nombre:",
]


class MetadataEnricher:
    """Concrete MetadataEnricherPort implementation.

    Satisfies MetadataEnricherPort Protocol via structural typing — no
    inheritance required (D-14).

    langdetect state is initialised lazily on the first call to
    _detect_language(). No mutable instance state is held; this class is
    safe to reuse across requests.
    """

    # ------------------------------------------------------------------
    # Public MetadataEnricherPort interface
    # ------------------------------------------------------------------

    def enrich(
        self, raw: RawDocument, chunks: list[DocumentChunk]
    ) -> DocumentMetadata:
        """Produce DocumentMetadata from a RawDocument and its chunks.

        All 9 META-01 fields are populated:
          - doc_id: UUID v4 (D-69)
          - source_filename: from raw.filename (D-70)
          - title: first H1 heading or "" (D-66)
          - author: always "" (D-67)
          - language: ISO 639-1 code or "und" (D-60, D-61, D-62)
          - doc_type: inferred from content heuristics (D-63, D-64, D-65)
          - page_count: from raw.page_count
          - chunk_count: len(chunks)
          - ingested_at: UTC timestamp at call time

        Args:
            raw: The filtered RawDocument produced by the filter adapter.
            chunks: List of DocumentChunk objects produced by the chunker.

        Returns:
            Immutable DocumentMetadata with all fields populated.
        """
        return DocumentMetadata(
            doc_id=str(uuid.uuid4()),
            source_filename=raw.filename,
            title=self._extract_title(raw.content),
            author="",
            language=self._detect_language(raw.content),
            doc_type=self._infer_doc_type(raw.content),
            page_count=raw.page_count,
            chunk_count=len(chunks),
            ingested_at=datetime.now(timezone.utc),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_language(self, content: str) -> str:
        """Detect the ISO 639-1 language code for the given text (D-60, D-61, D-62).

        Uses langdetect.detect_langs() which returns a list of Language objects
        sorted by probability in descending order. Accepts the top candidate
        only if its score >= LANGUAGE_CONFIDENCE_THRESHOLD. Returns "und"
        (ISO 639-3 for undetermined) in all other cases.

        Any exception raised internally by langdetect (e.g. LangDetectException
        for text too short, encoding errors, or internal failures) is caught and
        "und" is returned — exceptions never propagate outside this method (D-62).

        Args:
            content: The Markdown text to analyse.

        Returns:
            ISO 639-1 language code (e.g. "en", "pt", "es") if confident,
            or "und" if detection is uncertain or fails.
        """
        try:
            candidates = detect_langs(content)
            if candidates and candidates[0].prob >= LANGUAGE_CONFIDENCE_THRESHOLD:
                return str(candidates[0].lang)
            return "und"
        except Exception:  # noqa: BLE001 — any langdetect failure → "und" (D-62)
            return "und"

    def _infer_doc_type(self, content: str) -> str:
        """Infer doc_type from content using keyword and structural heuristics.

        Strategy (D-63, D-64, D-65):
          1. Extract heading lines (lines starting with "#").
          2. Check heading text (lowercased) against DOC_TYPE_KEYWORDS for:
             - legal: highest priority keyword set
             - presentation: second keyword set
          3. Check full content for form indicators (fill-in-the-blank patterns).
          4. Report heuristic: document has multiple tables (lines with "|") AND
             numbered sections (lines matching ^\\d+\\.) AND has content.
          5. Fallback: "other".

        Priority: legal → presentation → form → report → other.

        "article" is in the closed vocabulary (D-63) but is not produced by
        any heuristic — documents with no strong signal receive "other".

        Args:
            content: The Markdown text to analyse.

        Returns:
            One of: "article", "report", "presentation", "form", "legal", "other".
        """
        lines = content.splitlines()
        heading_text = " ".join(
            line.lstrip("#").strip().lower()
            for line in lines
            if line.startswith("#")
        )

        # --- legal (highest priority) ---
        for keyword in DOC_TYPE_KEYWORDS["legal"]:
            if keyword.lower() in heading_text:
                return "legal"

        # --- presentation ---
        for keyword in DOC_TYPE_KEYWORDS["presentation"]:
            if keyword.lower() in heading_text:
                return "presentation"

        # --- form: scan full content for fill-in-the-blank indicators ---
        for indicator in _FORM_INDICATORS:
            if indicator in content:
                return "form"

        # --- report: structural heuristic ---
        # Requires: at least 2 table rows (lines containing "|") AND
        # at least 2 numbered section lines (lines matching ^\d+\.)
        table_lines = sum(1 for line in lines if "|" in line)
        numbered_sections = sum(
            1 for line in lines if re.match(r"^\d+\.", line.strip())
        )
        if table_lines >= 2 and numbered_sections >= 2:
            return "report"

        return "other"

    def _extract_title(self, content: str) -> str:
        """Extract the document title from the first H1 heading (D-66).

        Uses re.search with re.MULTILINE to find the first line matching
        the pattern ``^# (.+)``. Returns the matched text stripped of
        surrounding whitespace. Returns "" if no H1 heading is present.

        Args:
            content: The Markdown text to search.

        Returns:
            Title string from the first H1, or "" if none found.
        """
        match = re.search(r"^# (.+)", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return ""


def build_metadata_enricher(config: EnricherConfig) -> MetadataEnricher:
    """Factory function for MetadataEnricher (D-23, D-72).

    Follows the same factory pattern as ``build_heuristic_filter()`` and
    ``build_markdown_chunker()``. Callers (service wiring, tests) use this
    factory rather than constructing MetadataEnricher directly.

    Args:
        config: EnricherConfig instance (empty in v1 — all parameters are
            module-level constants). Use ``get_config().enricher`` to obtain
            from the centralized config.

    Returns:
        A fully configured MetadataEnricher instance.
    """
    _ = config  # EnricherConfig is empty in v1; parameter reserved for v2.
    return MetadataEnricher()
