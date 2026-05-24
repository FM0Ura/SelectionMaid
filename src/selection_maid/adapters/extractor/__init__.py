"""Extractor adapter subpackage — ExtractorPort implementations."""

from selection_maid.adapters.extractor.docling import (
    DoclingAdapter,
    build_docling_adapter,
)

__all__ = ["DoclingAdapter", "build_docling_adapter"]
