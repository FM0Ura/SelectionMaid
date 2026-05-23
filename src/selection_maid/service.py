"""Application service for SelectionMaid.

ExtractionService is the application core. It owns the pipeline logic,
delegates all actual work to injected port adapters, and wraps adapter
exceptions at each boundary to ensure callers only ever see
SelectionMaidError subclasses (decision D-16).

Pipeline: extract → filter → chunk → enrich → ExtractionResult
"""
from __future__ import annotations

from selection_maid.domain.models import (
    DocumentChunk,
    DocumentMetadata,
    ExtractionResult,
    RawDocument,
    RawInput,
)
from selection_maid.domain.ports import (
    ChunkerPort,
    ExtractorPort,
    FilterPort,
    MetadataEnricherPort,
)
from selection_maid.errors import (
    ChunkingError,
    EnrichmentError,
    ExtractionError,
    FilterError,
    SelectionMaidError,
)


class ExtractionService:
    """Orchestrates the document extraction pipeline.

    All four port adapters are injected at construction time — ExtractionService
    never imports a concrete adapter. This enforces the hexagonal architecture
    constraint (ARCH-06): the domain core has zero dependencies on infrastructure.

    Exception wrapping (D-16):
      - If an adapter raises a SelectionMaidError subclass, it propagates unchanged.
      - Any other exception is wrapped in the appropriate domain error subclass so
        callers of process() always deal with a typed domain error, never raw adapter
        exceptions.
    """

    def __init__(
        self,
        extractor: ExtractorPort,
        filter_: FilterPort,
        chunker: ChunkerPort,
        enricher: MetadataEnricherPort,
    ) -> None:
        self._extractor = extractor
        self._filter = filter_
        self._chunker = chunker
        self._enricher = enricher

    def process(self, input: RawInput) -> ExtractionResult:
        """Run the full extract → filter → chunk → enrich pipeline.

        Args:
            input: Entry value object identifying the file to process.

        Returns:
            ExtractionResult containing enriched metadata and an immutable
            tuple of DocumentChunk objects.

        Raises:
            ExtractionError: Extractor adapter failed for a non-domain reason.
            FilterError: Filter adapter failed for a non-domain reason.
            ChunkingError: Chunker adapter failed for a non-domain reason.
            EnrichmentError: Enricher adapter failed for a non-domain reason.
            SelectionMaidError: Any domain error raised by an adapter directly
                (propagated unchanged per D-16).
        """
        # Step 1 — extract
        try:
            raw: RawDocument = self._extractor.extract(input)
        except SelectionMaidError:
            raise
        except Exception as e:
            raise ExtractionError(message=f"Extraction failed: {e}", cause=e) from e

        # Step 2 — filter
        try:
            filtered: RawDocument = self._filter.filter(raw)
        except SelectionMaidError:
            raise
        except Exception as e:
            raise FilterError(message=f"Filtering failed: {e}", cause=e) from e

        # Step 3 — chunk
        try:
            chunks_list: list[DocumentChunk] = self._chunker.chunk(filtered.content)
        except SelectionMaidError:
            raise
        except Exception as e:
            raise ChunkingError(message=f"Chunking failed: {e}", cause=e) from e

        # Step 4 — enrich
        try:
            metadata: DocumentMetadata = self._enricher.enrich(raw, chunks_list)
        except SelectionMaidError:
            raise
        except Exception as e:
            raise EnrichmentError(message=f"Enrichment failed: {e}", cause=e) from e

        return ExtractionResult(metadata=metadata, chunks=tuple(chunks_list))
