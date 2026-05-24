"""Unit tests for MarkdownChunker heading-based split logic.

Test structure:
  - TestHeadingBasedSplit: H1/H2 splitting, pre-heading text, section_title,
    basic metadata fields (Task 1, D-45, D-46, D-53, D-54, D-55, D-56).
  - TestLargeSectionSubdivision: paragraph-boundary subdivision for oversized
    sections (Task 2, D-47, D-48).
  - TestFixedSizeFallback: fixed-size token-budget chunking for documents
    without H1/H2 headings (Plan 04-03 Task 1, D-49, D-50, D-51, D-52, D-56).

All fixtures are inline Markdown strings — no external .md files.
"""
from __future__ import annotations

import re
import uuid

import pytest

from selection_maid.adapters.chunker.markdown import MarkdownChunker


class TestHeadingBasedSplit:
    """Heading-based split on H1/H2 boundaries (D-45).

    Covers:
      - H1 and H2 headings each trigger a new chunk
      - H3+ headings do NOT trigger a split (treated as content)
      - Pre-heading text is preserved as a chunk with section_title=""
      - section_title contains heading text without leading '#' characters
      - Basic metadata: page_start=0, page_end=0, chunk_id as UUID v4,
        word_count = len(content.split())
      - chunk_index and total_chunks are consistent (second pass, D-57)
    """

    def test_h1_splits_into_separate_chunks(self) -> None:
        """A document with two H1 headings produces three separate chunks."""
        content = (
            "# Introduction\n\nThis is the introduction.\n\n"
            "# Methods\n\nThis is the methods section."
        )
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        assert len(chunks) == 2
        assert chunks[0].section_title == "Introduction"
        assert chunks[1].section_title == "Methods"

    def test_h2_splits_into_separate_chunks(self) -> None:
        """H2 headings also trigger splits like H1."""
        content = (
            "## Background\n\nSome background text.\n\n"
            "## Results\n\nSome results text."
        )
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        assert len(chunks) == 2
        assert chunks[0].section_title == "Background"
        assert chunks[1].section_title == "Results"

    def test_h3_does_not_split(self) -> None:
        """H3 headings must NOT trigger a split — treated as content (D-45)."""
        content = (
            "# Main Section\n\n"
            "Some text.\n\n"
            "### Subsection\n\n"
            "More text under subsection."
        )
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        assert len(chunks) == 1
        assert chunks[0].section_title == "Main Section"
        assert "### Subsection" in chunks[0].content

    def test_h4_does_not_split(self) -> None:
        """H4 headings must NOT trigger a split."""
        content = (
            "## Section\n\n"
            "Text.\n\n"
            "#### Deep heading\n\n"
            "Deep text."
        )
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        assert len(chunks) == 1
        assert "#### Deep heading" in chunks[0].content

    def test_pre_heading_text_is_chunk_with_empty_section_title(self) -> None:
        """Content before the first H1/H2 is preserved as a chunk with section_title='' (D-46)."""
        content = (
            "This is a preamble paragraph.\n\n"
            "Another preamble line.\n\n"
            "# Introduction\n\nActual introduction."
        )
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        assert len(chunks) == 2
        assert chunks[0].section_title == ""
        assert "preamble" in chunks[0].content
        assert chunks[1].section_title == "Introduction"

    def test_no_pre_heading_text_no_empty_chunk(self) -> None:
        """When document starts with a heading, no empty pre-heading chunk is created."""
        content = "# Title\n\nContent here."
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        assert len(chunks) == 1
        assert chunks[0].section_title == "Title"

    def test_section_title_strips_hash_prefix(self) -> None:
        """section_title must be the heading text without the '#' prefix (D-56)."""
        content = "# My Great Title\n\nSome content."
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        assert chunks[0].section_title == "My Great Title"

    def test_section_title_strips_double_hash_prefix(self) -> None:
        """H2 section_title also strips both '##' characters."""
        content = "## Sub Title\n\nSome content."
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        assert chunks[0].section_title == "Sub Title"

    def test_page_start_and_page_end_are_zero(self) -> None:
        """page_start and page_end must both be 0 for all chunks (D-53)."""
        content = (
            "# Section A\n\nText A.\n\n"
            "## Section B\n\nText B."
        )
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        for chunk in chunks:
            assert chunk.page_start == 0
            assert chunk.page_end == 0

    def test_chunk_id_is_uuid_v4(self) -> None:
        """chunk_id must be a valid UUID v4 string (D-54)."""
        content = "# A Section\n\nContent here."
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        for chunk in chunks:
            parsed = uuid.UUID(chunk.chunk_id)
            assert parsed.version == 4

    def test_chunk_ids_are_unique(self) -> None:
        """Each chunk must have a unique chunk_id across a single call."""
        content = (
            "# Section One\n\nContent one.\n\n"
            "# Section Two\n\nContent two.\n\n"
            "# Section Three\n\nContent three."
        )
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids))

    def test_word_count_correct(self) -> None:
        """word_count must equal len(content.split()) (D-55)."""
        content = "# Title\n\nOne two three four five."
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        assert len(chunks) == 1
        # heading line + content words
        expected_wc = len(chunks[0].content.split())
        assert chunks[0].word_count == expected_wc

    def test_chunk_index_and_total_chunks_consistent(self) -> None:
        """chunk_index and total_chunks must be consistent (second pass, D-57)."""
        content = (
            "# Alpha\n\nAlpha content.\n\n"
            "# Beta\n\nBeta content.\n\n"
            "# Gamma\n\nGamma content."
        )
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        total = len(chunks)
        for i, chunk in enumerate(chunks):
            assert chunk.total_chunks == total
            assert chunk.chunk_index == i

    def test_mixed_h1_and_h2(self) -> None:
        """A document with mixed H1 and H2 headings all trigger splits."""
        content = (
            "# Chapter 1\n\nChapter text.\n\n"
            "## Section 1.1\n\nSection text.\n\n"
            "# Chapter 2\n\nMore chapter text."
        )
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        assert len(chunks) == 3
        assert chunks[0].section_title == "Chapter 1"
        assert chunks[1].section_title == "Section 1.1"
        assert chunks[2].section_title == "Chapter 2"

    def test_empty_content_returns_empty_list(self) -> None:
        """Empty string input returns an empty list, not an error."""
        chunker = MarkdownChunker()
        chunks = chunker.chunk("")
        assert chunks == []

    def test_whitespace_only_content_returns_empty_list(self) -> None:
        """Whitespace-only content returns an empty list."""
        chunker = MarkdownChunker()
        chunks = chunker.chunk("   \n\n   \n")
        assert chunks == []


class TestLargeSectionSubdivision:
    """Paragraph-boundary subdivision for oversized sections (D-47, D-48).

    Covers:
      - Section exceeding max_tokens splits at paragraph boundaries (double newline)
      - Subdivision does NOT break inside a paragraph (D-47)
      - Sub-chunks retain the section_title of the parent heading (D-56)
      - total_chunks and chunk_index are correct across all sub-chunks
    """

    def _make_paragraph(self, word_count: int, seed: str = "word") -> str:
        """Build a paragraph with the given number of words (no newlines inside)."""
        return " ".join(f"{seed}{i}" for i in range(word_count))

    def test_large_section_splits_by_paragraph(self) -> None:
        """A section exceeding max_tokens is split into multiple chunks at paragraph boundary."""
        # Each paragraph has 300 words; max_tokens=512 → 2 paragraphs (600 words) should split
        p1 = self._make_paragraph(300, "alpha")
        p2 = self._make_paragraph(300, "beta")
        content = f"# Big Section\n\n{p1}\n\n{p2}"
        chunker = MarkdownChunker(max_tokens=512)
        chunks = chunker.chunk(content)
        # The section exceeds 512 words, so it must be split into at least 2 chunks
        assert len(chunks) >= 2

    def test_subdivision_does_not_break_inside_paragraph(self) -> None:
        """Subdivision must only occur at double-newline paragraph boundaries (D-47)."""
        # Build a section with 3 paragraphs that together exceed max_tokens
        p1 = self._make_paragraph(200, "a")
        p2 = self._make_paragraph(200, "b")
        p3 = self._make_paragraph(200, "c")
        content = f"# Section\n\n{p1}\n\n{p2}\n\n{p3}"
        chunker = MarkdownChunker(max_tokens=350)
        chunks = chunker.chunk(content)
        # Each chunk must contain complete paragraphs (no words from a split paragraph)
        for chunk in chunks:
            # A mid-paragraph cut would leave orphan "a{n}" or "b{n}" words
            # The simplest check: chunk content should not end with a partial word split mid-sentence
            # Verify each chunk's content is composed of complete paragraphs from our input
            chunk_text = chunk.content
            # Each alpha, beta, gamma word must appear in exactly one complete sequence
            # If a paragraph is split, consecutive words like "a0 a1 a2" would be split
            # We check that each paragraph-prefix sequence is not split across chunks
            for prefix in ("a", "b", "c"):
                first_word = f"{prefix}0"
                last_word = f"{prefix}199"
                has_first = first_word in chunk_text
                has_last = last_word in chunk_text
                # Either both are present (complete paragraph) or neither (paragraph in other chunk)
                assert has_first == has_last, (
                    f"Paragraph '{prefix}' appears to be split across chunks: "
                    f"first={has_first}, last={has_last} in chunk {chunk.chunk_index}"
                )

    def test_subdivided_chunks_retain_section_title(self) -> None:
        """All sub-chunks from a subdivided section keep the parent heading title (D-56)."""
        p1 = self._make_paragraph(300, "x")
        p2 = self._make_paragraph(300, "y")
        content = f"# Parent Heading\n\n{p1}\n\n{p2}"
        chunker = MarkdownChunker(max_tokens=512)
        chunks = chunker.chunk(content)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert chunk.section_title == "Parent Heading"

    def test_subdivided_chunks_consistent_indexing(self) -> None:
        """chunk_index and total_chunks are correct when subdivision produces extra chunks."""
        p1 = self._make_paragraph(300, "m")
        p2 = self._make_paragraph(300, "n")
        content = f"# Section\n\n{p1}\n\n{p2}"
        chunker = MarkdownChunker(max_tokens=512)
        chunks = chunker.chunk(content)
        total = len(chunks)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.total_chunks == total

    def test_section_within_limit_is_not_split(self) -> None:
        """A section under max_tokens must remain as a single chunk."""
        p = self._make_paragraph(50, "short")
        content = f"# Small Section\n\n{p}"
        chunker = MarkdownChunker(max_tokens=512)
        chunks = chunker.chunk(content)
        assert len(chunks) == 1
        assert chunks[0].section_title == "Small Section"

    def test_multiple_headings_with_large_section(self) -> None:
        """Large section split does not affect adjacent sections with correct indexing."""
        small = self._make_paragraph(20, "tiny")
        p1 = self._make_paragraph(300, "bigA")
        p2 = self._make_paragraph(300, "bigB")
        content = (
            f"# Small\n\n{small}\n\n"
            f"# Large\n\n{p1}\n\n{p2}"
        )
        chunker = MarkdownChunker(max_tokens=512)
        chunks = chunker.chunk(content)
        # Small section: 1 chunk; Large section: at least 2 chunks
        assert len(chunks) >= 3
        # Small section chunk
        assert chunks[0].section_title == "Small"
        # All subsequent chunks belong to Large
        for chunk in chunks[1:]:
            assert chunk.section_title == "Large"
        # Indexing is correct
        total = len(chunks)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.total_chunks == total


class TestFixedSizeFallback:
    """Fixed-size token-budget chunking for documents without H1/H2 headings.

    Covers (Plan 04-03 Task 1):
      - Fallback activates when no H1/H2 heading is present (D-49)
      - tiktoken cl100k_base is used for token counting (D-50)
      - max_tokens (default 512) limits chunk size (D-51)
      - Paragraph boundaries (double newline) are respected — never mid-paragraph (D-52)
      - section_title is "" for all fallback chunks (D-56)
      - chunk_index and total_chunks are consistent across fallback chunks
    """

    def _make_paragraph(self, word_count: int, seed: str = "word") -> str:
        """Build a paragraph with the given number of space-separated words."""
        return " ".join(f"{seed}{i}" for i in range(word_count))

    def test_fallback_activates_when_no_headings(self) -> None:
        """Fixed-size fallback is used when the document has no H1/H2 (D-49)."""
        content = "This is plain prose without any heading.\n\nAnother paragraph here."
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        # The document has no headings — fallback must have produced chunks
        assert len(chunks) >= 1
        # All chunks from the fallback have section_title="" (D-56)
        for chunk in chunks:
            assert chunk.section_title == ""

    def test_fallback_not_activated_when_headings_present(self) -> None:
        """Fallback is NOT used when the document contains an H1 or H2 (D-49)."""
        content = "# A Heading\n\nContent under heading."
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        # Heading-based split used; section_title is set to heading text
        assert chunks[0].section_title == "A Heading"

    def test_fallback_section_title_is_empty_string(self) -> None:
        """All chunks produced by the fallback strategy have section_title='' (D-56)."""
        # Three separate paragraphs; each small enough to fit in one chunk
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunker = MarkdownChunker(max_tokens=512)
        chunks = chunker.chunk(content)
        for chunk in chunks:
            assert chunk.section_title == ""

    def test_fallback_respects_max_tokens(self) -> None:
        """Fallback splits into multiple chunks when token budget is exceeded (D-51)."""
        # Two large paragraphs that together exceed max_tokens=50
        p1 = self._make_paragraph(40, "alpha")
        p2 = self._make_paragraph(40, "beta")
        content = f"{p1}\n\n{p2}"
        # max_tokens=50: each paragraph alone fits but together they do not
        chunker = MarkdownChunker(max_tokens=50)
        chunks = chunker.chunk(content)
        assert len(chunks) == 2
        assert "alpha0" in chunks[0].content
        assert "beta0" in chunks[1].content

    def test_fallback_respects_paragraph_boundaries(self) -> None:
        """Fallback never cuts inside a paragraph — only at double-newline boundaries (D-52)."""
        p1 = self._make_paragraph(30, "a")
        p2 = self._make_paragraph(30, "b")
        p3 = self._make_paragraph(30, "c")
        content = f"{p1}\n\n{p2}\n\n{p3}"
        # max_tokens=40: each paragraph (~30 tokens) fits; two paragraphs (60 tokens) don't
        chunker = MarkdownChunker(max_tokens=40)
        chunks = chunker.chunk(content)
        # Each chunk must contain complete paragraphs
        for chunk in chunks:
            for prefix in ("a", "b", "c"):
                first_word = f"{prefix}0"
                last_word = f"{prefix}29"
                has_first = first_word in chunk.content
                has_last = last_word in chunk.content
                assert has_first == has_last, (
                    f"Paragraph '{prefix}' appears split across chunks: "
                    f"first={has_first}, last={has_last} in chunk {chunk.chunk_index}"
                )

    def test_fallback_single_paragraph_produces_one_chunk(self) -> None:
        """A document with a single paragraph and no headings returns exactly one chunk."""
        content = "Just one paragraph of plain text without any heading markers."
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        assert len(chunks) == 1
        assert chunks[0].section_title == ""

    def test_fallback_chunk_index_and_total_chunks_consistent(self) -> None:
        """chunk_index and total_chunks are consistent across all fallback chunks."""
        p1 = self._make_paragraph(60, "x")
        p2 = self._make_paragraph(60, "y")
        p3 = self._make_paragraph(60, "z")
        content = f"{p1}\n\n{p2}\n\n{p3}"
        chunker = MarkdownChunker(max_tokens=80)
        chunks = chunker.chunk(content)
        total = len(chunks)
        assert total > 0
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.total_chunks == total

    def test_fallback_chunk_ids_are_unique_uuids(self) -> None:
        """Each fallback chunk has a unique UUID v4 chunk_id (D-54)."""
        p1 = self._make_paragraph(60, "u")
        p2 = self._make_paragraph(60, "v")
        content = f"{p1}\n\n{p2}"
        chunker = MarkdownChunker(max_tokens=80)
        chunks = chunker.chunk(content)
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids)), "chunk_ids must be unique"
        for chunk_id in ids:
            parsed = __import__("uuid").UUID(chunk_id)
            assert parsed.version == 4

    def test_fallback_page_start_and_page_end_are_zero(self) -> None:
        """page_start and page_end are always 0 in the fallback path (D-53)."""
        content = "Paragraph one.\n\nParagraph two."
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        for chunk in chunks:
            assert chunk.page_start == 0
            assert chunk.page_end == 0

    def test_fallback_word_count_correct(self) -> None:
        """word_count equals len(content.split()) for each fallback chunk (D-55)."""
        content = "One two three.\n\nFour five six."
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        for chunk in chunks:
            assert chunk.word_count == len(chunk.content.split())

    def test_h3_only_document_uses_fallback(self) -> None:
        """A document with only H3 headings (no H1/H2) uses the fixed-size fallback (D-49)."""
        content = "### Sub-section\n\nSome content under an H3 heading."
        chunker = MarkdownChunker()
        chunks = chunker.chunk(content)
        # H3 is not a split trigger; fallback used — section_title=""
        assert len(chunks) == 1
        assert chunks[0].section_title == ""
