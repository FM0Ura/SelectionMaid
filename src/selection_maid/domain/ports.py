from __future__ import annotations

from typing import Protocol

from selection_maid.domain.models import (
    DocumentChunk,
    DocumentMetadata,
    RawDocument,
    RawInput,
)


class ExtractorPort(Protocol):
    """Port contract for document extraction adapters (per D-09).

    An adapter satisfies this Protocol by implementing the ``extract`` method
    with the exact signature below — no inheritance required (structural typing).
    isinstance() checks are not supported by design (D-14).
    """

    def extract(self, document: RawInput) -> RawDocument: ...


class FilterPort(Protocol):
    """Port contract for document filtering adapters (per D-10).

    The filter receives a raw extracted document and returns a cleaned copy.
    Input and output types are both ``RawDocument`` — filtering is a pure
    transformation that does not change the document schema.
    """

    def filter(self, document: RawDocument) -> RawDocument: ...


class ChunkerPort(Protocol):
    """Port contract for document chunking adapters (per D-11).

    Receives the Markdown string from the filtered ``RawDocument.content``.
    Returns a ``list[DocumentChunk]``; the service converts this to an
    immutable ``tuple`` when building ``ExtractionResult``.
    """

    def chunk(self, content: str) -> list[DocumentChunk]: ...


class MetadataEnricherPort(Protocol):
    """Port contract for metadata enrichment adapters (per D-12).

    Receives both the original raw document and the final chunks list so the
    enricher can derive metadata from both sources (e.g. page_count from
    ``raw``, total_chunks from ``chunks``).
    """

    def enrich(self, raw: RawDocument, chunks: list[DocumentChunk]) -> DocumentMetadata: ...
