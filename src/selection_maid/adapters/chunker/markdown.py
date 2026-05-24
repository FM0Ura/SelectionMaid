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

import tiktoken

from selection_maid.config import ChunkerConfig
from selection_maid.domain.models import DocumentChunk
from selection_maid.errors import ChunkingError, SelectionMaidError

#: Tokenizer encoding hardcoded to cl100k_base (D-50) — not configurable in v1.
_ENCODING_NAME: str = "cl100k_base"


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
            NotImplementedError: Implementation pending (Plan 04-02).
            ChunkingError: Unexpected error during chunking (D-16).
                SelectionMaidError subclasses propagate unchanged.
        """
        try:
            raise NotImplementedError(
                "MarkdownChunker.chunk() is not yet implemented. "
                "Implementation is scheduled for Phase 4 Plan 02."
            )
        except SelectionMaidError:
            raise
        except Exception as exc:
            raise ChunkingError(
                f"Chunking failed: {exc}",
                cause=exc,
            ) from exc


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
