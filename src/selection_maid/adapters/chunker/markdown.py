"""MarkdownChunker — concrete ChunkerPort implementation.

Splits Markdown content into DocumentChunk objects using two strategies:

  1. Heading-based split (primary): splits at H1 (``#``) and H2 (``##``)
     boundaries (D-45). Oversized sections are further subdivided at paragraph
     boundaries (D-47). This strategy is used when the document contains at
     least one H1 or H2 heading.

  2. Fixed-size fallback: token-budget chunking via tiktoken (D-49, D-50).
     Activated when no H1/H2 headings are present. Respects paragraph
     boundaries — never cuts mid-paragraph (D-52).

Tokenizer encoding is hardcoded to ``cl100k_base`` (GPT-4 /
text-embedding-ada-002) and initialised once in the constructor (D-50).
``max_tokens`` is configurable via constructor injection (D-57).

Decision references:
  D-16: Exception wrapping — unexpected errors raised as ChunkingError.
  D-45: H1/H2 heading boundaries as primary split points.
  D-46: Pre-heading content preserved as a chunk with section_title="".
  D-47: Oversized sections subdivided at paragraph boundaries.
  D-48: Section-subdivision limit == max_tokens (configurable).
  D-49: Fixed-size fallback when no H1/H2 present.
  D-50: cl100k_base encoding, initialised once in __init__.
  D-51: max_tokens default 512.
  D-52: Fallback respects paragraph boundaries.
  D-53: page_start and page_end always 0 (no page info in Markdown string).
  D-54: chunk_id is UUID v4 via uuid.uuid4().
  D-55: word_count via len(content.split()).
  D-56: section_title is the heading text without leading ``#`` characters.
  D-57: Constructor injection: MarkdownChunker(max_tokens).
  D-59: File at src/selection_maid/adapters/chunker/markdown.py.
"""

from __future__ import annotations

import re
import uuid

import tiktoken

from selection_maid.config import ChunkerConfig
from selection_maid.domain.models import DocumentChunk
from selection_maid.errors import ChunkingError, SelectionMaidError

#: Tokenizer encoding hardcoded to cl100k_base (D-50) — not configurable in v1.
_ENCODING_NAME: str = "cl100k_base"

#: Regex matching H1 and H2 headings only (D-45).
#: Group 1 captures the heading text without leading '#' characters.
_H1_H2_PATTERN: re.Pattern[str] = re.compile(r"^#{1,2}\s+(.+)", re.MULTILINE)


def _make_chunk(
    content: str,
    section_title: str,
    chunk_index: int,
    total_chunks: int,
    chunk_id: str,
) -> DocumentChunk:
    """Create a DocumentChunk with all CHUNK-03 fields populated.

    Args:
        content: The text content for this chunk.
        section_title: Heading title without '#' prefix (D-56). Empty string
            for pre-heading content and fixed-size fallback chunks.
        chunk_index: Zero-based position of this chunk in the final list.
        total_chunks: Total number of chunks produced by this call.
        chunk_id: Pre-generated UUID v4 string for this chunk (D-54).

    Returns:
        Immutable DocumentChunk with all required fields.
    """
    return DocumentChunk(
        chunk_id=chunk_id,
        content=content,
        page_start=0,  # D-53: no page info available from Markdown string
        page_end=0,  # D-53
        section_title=section_title,
        chunk_index=chunk_index,
        total_chunks=total_chunks,
        word_count=len(content.split()),  # D-55
    )


def _subdivide_by_paragraph(
    section_content: str,
    section_title: str,
    max_words: int,
) -> list[tuple[str, str]]:
    """Subdivide a section's content into paragraph-bounded sub-chunks.

    Accumulates paragraphs (separated by double newlines) until the word
    count would exceed ``max_words``. When the budget is exceeded, the
    current accumulation is flushed as a sub-chunk and a new one starts.
    Never cuts inside a paragraph (D-47).

    Args:
        section_content: The full text content of one heading section.
        section_title: The heading title preserved for all sub-chunks (D-56).
        max_words: Word budget per sub-chunk (D-48). Measured via len(split()).

    Returns:
        List of (content, section_title) pairs — one per sub-chunk.
        The section_title is identical for all returned pairs.
    """
    # Split on double-newline paragraph boundaries
    paragraphs = re.split(r"\n\n+", section_content)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if not paragraphs:
        return []

    result: list[tuple[str, str]] = []
    current_paragraphs: list[str] = []
    current_words = 0

    for paragraph in paragraphs:
        para_words = len(paragraph.split())

        if current_paragraphs and current_words + para_words > max_words:
            # Flush current accumulation as a sub-chunk
            result.append(("\n\n".join(current_paragraphs), section_title))
            current_paragraphs = [paragraph]
            current_words = para_words
        else:
            current_paragraphs.append(paragraph)
            current_words += para_words

    # Flush the final accumulation
    if current_paragraphs:
        result.append(("\n\n".join(current_paragraphs), section_title))

    return result


class MarkdownChunker:
    """Concrete ChunkerPort implementation for Markdown content.

    Satisfies ChunkerPort Protocol via structural typing — no inheritance (D-14).

    Two chunking strategies are applied depending on document structure:
    - Heading-based split (primary, D-45)
    - Fixed-size token fallback (D-49, D-50)

    Attributes:
        _max_tokens: Token budget per chunk (D-51).
        _encoder: tiktoken encoder instance, initialised once (D-50).
    """

    def __init__(self, max_tokens: int = 512) -> None:
        """Initialise the chunker with configurable token budget (D-57).

        The tiktoken encoder is created once here and reused across all
        ``chunk()`` calls — encoder construction is expensive (D-50).

        Args:
            max_tokens: Maximum token budget per chunk. Used for both the
                fixed-size fallback (D-51) and the heading-section
                subdivision limit (D-48). Defaults to 512.
        """
        self._max_tokens = max_tokens
        self._encoder: tiktoken.Encoding = tiktoken.get_encoding(_ENCODING_NAME)

    # ------------------------------------------------------------------
    # Public ChunkerPort interface
    # ------------------------------------------------------------------

    def chunk(self, content: str) -> list[DocumentChunk]:
        """Split Markdown content into DocumentChunk objects.

        Selects the chunking strategy based on document structure:
        - If H1/H2 headings are present, uses heading-based split (D-45).
        - Otherwise, falls back to fixed-size token chunking (D-49).

        Args:
            content: Filtered Markdown string (RawDocument.content).

        Returns:
            List of DocumentChunk objects with all CHUNK-03 fields populated.

        Raises:
            ChunkingError: Unexpected error during chunking (D-16).
                SelectionMaidError subclasses propagate unchanged.
        """
        try:
            stripped = content.strip()
            if not stripped:
                return []

            if _H1_H2_PATTERN.search(stripped):
                raw_pairs = self._heading_split(stripped)
            else:
                raw_pairs = self._fixed_size_split(stripped)

            # Second pass: assign chunk_index and total_chunks (D-57)
            total = len(raw_pairs)
            if total == 0:
                return []

            chunks: list[DocumentChunk] = []
            for index, (text, title) in enumerate(raw_pairs):
                chunks.append(
                    _make_chunk(
                        content=text,
                        section_title=title,
                        chunk_index=index,
                        total_chunks=total,
                        chunk_id=str(uuid.uuid4()),  # D-54
                    )
                )
            return chunks

        except SelectionMaidError:
            raise
        except Exception as exc:
            raise ChunkingError(
                f"Chunking failed: {exc}",
                cause=exc,
            ) from exc

    # ------------------------------------------------------------------
    # Private strategy implementations
    # ------------------------------------------------------------------

    def _heading_split(self, content: str) -> list[tuple[str, str]]:
        """Primary heading-based split strategy (D-45, D-46, D-47, D-56).

        Iterates line-by-line. When an H1 or H2 heading is encountered,
        the accumulated content is flushed as a section. Pre-heading text
        is captured with section_title="" (D-46). Sections that exceed
        ``_max_tokens`` words are further subdivided by paragraph (D-47).

        Args:
            content: Non-empty stripped Markdown string with at least one H1/H2.

        Returns:
            List of (content, section_title) pairs before index assignment.
        """
        lines = content.splitlines()

        # Accumulated raw sections before paragraph subdivision
        # Each element: (list_of_lines, section_title)
        sections: list[tuple[list[str], str]] = []
        current_lines: list[str] = []
        current_title: str = ""

        for line in lines:
            match = re.match(r"^#{1,2}\s+(.+)", line)
            if match:
                # Flush the accumulated content as a section
                if current_lines:
                    sections.append((current_lines, current_title))
                # Start a new section with this heading
                current_lines = [line]
                current_title = match.group(1).strip()
            else:
                current_lines.append(line)

        # Flush the final section
        if current_lines:
            sections.append((current_lines, current_title))

        # Subdivide oversized sections (D-47, D-48) and collect final pairs
        raw_pairs: list[tuple[str, str]] = []
        for section_lines, title in sections:
            section_text = "\n".join(section_lines).strip()
            if not section_text:
                continue

            section_words = len(section_text.split())
            if section_words > self._max_tokens:
                sub_pairs = _subdivide_by_paragraph(
                    section_text, title, self._max_tokens
                )
                raw_pairs.extend(sub_pairs)
            else:
                raw_pairs.append((section_text, title))

        return raw_pairs

    def _fixed_size_split(self, content: str) -> list[tuple[str, str]]:
        """Fixed-size fallback strategy using tiktoken (D-49, D-50, D-52).

        Accumulates paragraphs until the token budget (``_max_tokens``) is
        reached. Never cuts inside a paragraph (D-52). All chunks receive
        section_title="" (D-56).

        Args:
            content: Non-empty stripped Markdown string with no H1/H2 headings.

        Returns:
            List of (content, section_title) pairs before index assignment.
        """
        paragraphs = re.split(r"\n\n+", content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        if not paragraphs:
            return []

        raw_pairs: list[tuple[str, str]] = []
        current_paragraphs: list[str] = []
        current_tokens = 0

        for paragraph in paragraphs:
            para_tokens = len(self._encoder.encode(paragraph))

            if current_paragraphs and current_tokens + para_tokens > self._max_tokens:
                raw_pairs.append(("\n\n".join(current_paragraphs), ""))
                current_paragraphs = [paragraph]
                current_tokens = para_tokens
            else:
                current_paragraphs.append(paragraph)
                current_tokens += para_tokens

        if current_paragraphs:
            raw_pairs.append(("\n\n".join(current_paragraphs), ""))

        return raw_pairs


def build_markdown_chunker(config: ChunkerConfig) -> MarkdownChunker:
    """Factory function for MarkdownChunker (D-23, D-57).

    Follows the same factory pattern as ``build_heuristic_filter()`` and
    ``build_docling_adapter()``. Callers (service wiring, tests) use this
    factory rather than constructing MarkdownChunker directly.

    Args:
        config: ChunkerConfig instance with resolved configuration values.
            Use ``get_config().chunker`` to obtain from the centralized config.

    Returns:
        A fully configured MarkdownChunker instance.
    """
    return MarkdownChunker(max_tokens=config.max_tokens)
