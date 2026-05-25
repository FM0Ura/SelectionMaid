"""Unit tests for HeuristicFilter.

Test structure per D-43 (one class per rule):
  - TestFILT01Headers: frequency-based header/footer removal (D-31 to D-34)
  - TestFILT02PageNumbers: isolated page number removal (D-35, D-36)
  - TestFILT03Whitespace: whitespace compression (D-37)
  - TestContentPreservation: legitimate content survives filtering (D-44)

All fixtures are inline Markdown strings (D-42) — no external .md files.
"""
from __future__ import annotations

import pytest

from selection_maid.adapters.filter.heuristic import (
    HeuristicFilter,
    build_heuristic_filter,
)
from selection_maid.config import FilterConfig
from selection_maid.domain.models import RawDocument


def _make_doc(content: str) -> RawDocument:
    """Build a minimal RawDocument for test fixtures (D-42)."""
    return RawDocument(
        content=content,
        filename="test.pdf",
        page_count=5,
        format="pdf",
    )


class TestFILT01Headers:
    """Frequency-based header/footer removal (D-31 to D-34).

    Safety net strategy: trust Docling first; HeuristicFilter handles edge cases.
    Candidates: lines ≤ 80 chars appearing ≥ 3 times.
    Exclusions: lines starting with '#' or containing '|' (D-33).
    """

    def test_removes_repeated_short_line(self) -> None:
        """A line repeating 3+ times that is ≤ 80 chars must be removed (D-32, D-34)."""
        header = "My Company — Confidential"
        content = (
            f"{header}\n\n"
            "## Section 1\n\nSome text here.\n\n"
            f"{header}\n\n"
            "## Section 2\n\nMore text here.\n\n"
            f"{header}\n\n"
            "## Section 3\n\nFinal text here."
        )
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert header not in result.content

    def test_does_not_remove_line_repeated_only_twice(self) -> None:
        """A line repeating < 3 times must NOT be removed (D-34 threshold)."""
        repeated = "Half-repeated line"
        content = (
            f"{repeated}\n\n"
            "## Section 1\n\nSome text here.\n\n"
            f"{repeated}\n\n"
            "## Section 2\n\nMore text here."
        )
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert result.content.count(repeated) == 2

    def test_does_not_remove_repeated_heading_line(self) -> None:
        """Lines starting with '#' are NEVER removed, even repeated 3+ times (D-33)."""
        heading = "# My Title"
        content = "\n\n".join([heading] * 4)
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert result.content.count(heading) == 4

    def test_does_not_remove_repeated_table_row(self) -> None:
        """Lines containing '|' are NEVER removed, even repeated 3+ times (D-33)."""
        row = "| Col A | Col B |"
        content = "\n".join([row] * 4)
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert result.content.count(row) == 4

    def test_does_not_remove_long_line_even_if_repeated(self) -> None:
        """Lines longer than max_line_len are not candidates even if repeated (D-32)."""
        long_line = "A" * 81
        content = "\n\n".join([long_line] * 3)
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert result.content.count(long_line) == 3

    def test_configurable_min_repeat(self) -> None:
        """min_repeat constructor argument controls the threshold (D-39)."""
        repeated = "Quarterly Report"
        # Repeats 4 times — removed with min_repeat=4, kept with min_repeat=5.
        content = "\n\n".join(
            [repeated, "Para A.", repeated, "Para B.", repeated, "Para C.", repeated]
        )
        doc = _make_doc(content)
        # With min_repeat=4: should be removed
        result_strict = HeuristicFilter(min_repeat=4).filter(doc)
        assert repeated not in result_strict.content
        # With min_repeat=5: should NOT be removed (only 4 occurrences)
        result_loose = HeuristicFilter(min_repeat=5).filter(doc)
        assert result_loose.content.count(repeated) == 4

    def test_configurable_max_line_len(self) -> None:
        """max_line_len constructor argument controls the candidate length (D-39)."""
        # Line is 90 chars — default 80 excludes it, but 100 includes it.
        line_90 = "B" * 90
        content = "\n\n".join([line_90] * 3)
        doc = _make_doc(content)
        # Default max_line_len=80: NOT removed (too long)
        result_default = HeuristicFilter().filter(doc)
        assert result_default.content.count(line_90) == 3
        # max_line_len=100: IS removed (within length limit)
        result_wide = HeuristicFilter(max_line_len=100).filter(doc)
        assert line_90 not in result_wide.content


class TestFactory:
    """Factory construction for centralized filter config (D-39, D-41)."""

    def test_build_heuristic_filter_uses_explicit_config(self) -> None:
        """Explicit FilterConfig values configure the generated filter."""
        repeated = "Quarterly Report"
        content = "\n\n".join([repeated, "Para A.", repeated, "Para B."])
        doc = _make_doc(content)

        default_result = build_heuristic_filter().filter(doc)
        assert default_result.content.count(repeated) == 2

        configured = build_heuristic_filter(FilterConfig(min_repeat=2))
        configured_result = configured.filter(doc)
        assert repeated not in configured_result.content


class TestFILT02PageNumbers:
    r"""Isolated page number removal (D-35, D-36).

    Patterns: pure digits (^\d+$), Roman numerals (^[IVXLCDMivxlcdm]{1,10}$),
    hyphenated variants (^-\s*\d+\s*-$). Strip whitespace before comparing (D-36).
    Only completely isolated lines -- inline numbers are NOT affected (D-36).
    """

    def test_removes_arabic_page_number(self) -> None:
        """A line containing only digits must be removed (D-35)."""
        content = "## Chapter 1\n\nSome text.\n\n42\n\n## Chapter 2\n\nMore text."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert "\n42\n" not in result.content
        assert "42" not in result.content.splitlines()

    def test_removes_lowercase_roman_numeral(self) -> None:
        """A line containing only lowercase Roman numeral must be removed (D-35)."""
        content = "Introduction\n\niv\n\nChapter content."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        lines = [line.strip() for line in result.content.splitlines()]
        assert "iv" not in lines

    def test_removes_uppercase_roman_numeral(self) -> None:
        """A line containing only uppercase Roman numeral must be removed (D-35)."""
        content = "Introduction\n\nXII\n\nChapter content."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        lines = [line.strip() for line in result.content.splitlines()]
        assert "XII" not in lines

    def test_removes_hyphenated_page_number(self) -> None:
        """A line like '- 10 -' must be removed (D-35)."""
        content = "## Section A\n\nSome text here.\n\n- 10 -\n\n## Section B"
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        lines = [line.strip() for line in result.content.splitlines()]
        assert "- 10 -" not in lines

    def test_removes_hyphenated_page_number_no_spaces(self) -> None:
        """A line like '-5-' (no spaces) must be removed (D-35)."""
        content = "## Section A\n\nSome text here.\n\n-5-\n\n## Section B"
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        lines = [line.strip() for line in result.content.splitlines()]
        assert "-5-" not in lines

    def test_does_not_remove_inline_number(self) -> None:
        """Numbers inside sentences must NOT be removed (D-36 — inline numbers)."""
        content = "See item 42 in the list."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert "42" in result.content

    def test_does_not_remove_inline_roman_number(self) -> None:
        """Roman numerals inside text must NOT be removed (D-36)."""
        content = "Refer to Chapter XII for details."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert "XII" in result.content

    def test_page_number_with_surrounding_whitespace_is_removed(self) -> None:
        """Page number lines with leading/trailing spaces are removed (D-36 strip)."""
        content = "## Section\n\n  7  \n\nContent here."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        lines = [line.strip() for line in result.content.splitlines()]
        assert "7" not in lines

    def test_does_not_remove_roman_numeral_exceeding_max_length(self) -> None:
        """Roman numeral patterns limited to 10 chars avoids false positives (D-35)."""
        # Use an 11-char string to exceed the limit.
        long_roman = "MMMCMXCIXII"  # 11 chars — exceeds limit
        content = f"## Section\n\n{long_roman}\n\nContent here."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert long_roman in result.content


class TestFILT03Whitespace:
    """Whitespace compression (D-37).

    3+ consecutive newlines → exactly 2 newlines (one blank line between blocks).
    Applied LAST in the rule chain (after header/footer and page number removal).
    """

    def test_compresses_triple_newline(self) -> None:
        """Three consecutive newlines must be compressed to two (D-37)."""
        content = "Block A.\n\n\nBlock B."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert "\n\n\n" not in result.content
        assert "Block A." in result.content
        assert "Block B." in result.content

    def test_compresses_many_newlines(self) -> None:
        """Six consecutive newlines must be compressed to exactly two (D-37)."""
        content = "Block A.\n\n\n\n\n\nBlock B."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert "\n\n\n" not in result.content
        assert result.content == "Block A.\n\nBlock B."

    def test_preserves_single_blank_line(self) -> None:
        """Two newlines (one blank line) must NOT be further compressed (D-37)."""
        content = "Block A.\n\nBlock B."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert result.content == "Block A.\n\nBlock B."

    def test_preserves_no_blank_line(self) -> None:
        """Single newline (no blank line between blocks) must be preserved (D-37)."""
        content = "Line A.\nLine B."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert result.content == "Line A.\nLine B."

    def test_whitespace_only_lines_are_normalized(self) -> None:
        """Lines with only spaces/tabs count as blank lines in compression (D-37)."""
        # Whitespace-only line between blank lines → 3+ newlines after normalization.
        content = "Block A.\n\n   \n\nBlock B."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        # After whitespace-only lines normalized to empty, \n\n \n\n → \n\n\n\n → \n\n
        assert "\n\n\n" not in result.content
        assert "Block A." in result.content
        assert "Block B." in result.content


class TestContentPreservation:
    """Legitimate content must survive filtering unchanged (D-44).

    Required to survive: H1/H2/H3 headings, paragraphs, GFM tables,
    ordered and unordered lists.
    """

    def test_preserves_h1_heading(self) -> None:
        """H1 headings must survive all filtering rules (D-44)."""
        content = "# Document Title\n\nSome paragraph text."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert "# Document Title" in result.content

    def test_preserves_h2_heading(self) -> None:
        """H2 headings must survive all filtering rules (D-44)."""
        content = "# Title\n\n## Section Overview\n\nParagraph text here."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert "## Section Overview" in result.content

    def test_preserves_h3_heading(self) -> None:
        """H3 headings must survive all filtering rules (D-44)."""
        content = "# Title\n\n### Subsection Details\n\nParagraph text here."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert "### Subsection Details" in result.content

    def test_preserves_paragraph(self) -> None:
        """Paragraphs with normal text must survive all filtering rules (D-44)."""
        paragraph = "Regular paragraph with important content about the topic."
        content = f"# Title\n\n{paragraph}"
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert paragraph in result.content

    def test_preserves_gfm_table(self) -> None:
        """GFM tables must survive all filtering rules (D-44, D-33)."""
        table = (
            "| Name | Age | City |\n"
            "|------|-----|------|\n"
            "| Alice | 30 | NYC |\n"
            "| Bob | 25 | LA |"
        )
        content = f"# Title\n\n{table}"
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert "| Name | Age | City |" in result.content
        assert "| Alice | 30 | NYC |" in result.content
        assert "| Bob | 25 | LA |" in result.content

    def test_preserves_unordered_list(self) -> None:
        """Unordered lists must survive all filtering rules (D-44)."""
        content = "# Title\n\n- Item one\n- Item two\n- Item three"
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert "- Item one" in result.content
        assert "- Item two" in result.content
        assert "- Item three" in result.content

    def test_preserves_ordered_list(self) -> None:
        """Ordered lists must survive all filtering rules (D-44)."""
        content = "# Title\n\n1. First item\n2. Second item\n3. Third item"
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert "1. First item" in result.content
        assert "2. Second item" in result.content
        assert "3. Third item" in result.content

    def test_preserves_all_content_types_together(self) -> None:
        """All content types coexist and survive a realistic document (D-44)."""
        content = (
            "# Annual Report 2024\n\n"
            "## Executive Summary\n\n"
            "This report covers the annual performance of our organization.\n\n"
            "### Key Metrics\n\n"
            "| Metric | Value | Change |\n"
            "|--------|-------|--------|\n"
            "| Revenue | $10M | +15% |\n"
            "| Employees | 120 | +10 |\n\n"
            "## Highlights\n\n"
            "- Strong Q3 performance\n"
            "- New product launch\n"
            "- Expanded into 3 new markets\n\n"
            "## Next Steps\n\n"
            "1. Finalize Q4 budget\n"
            "2. Launch new hiring campaign\n"
            "3. Review partnership agreements"
        )
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert "# Annual Report 2024" in result.content
        assert "## Executive Summary" in result.content
        assert "### Key Metrics" in result.content
        assert "| Revenue | $10M | +15% |" in result.content
        assert "- Strong Q3 performance" in result.content
        assert "1. Finalize Q4 budget" in result.content


class TestErrorHandling:
    """Exception wrapping behavior (D-16).

    Unexpected exceptions must be wrapped in FilterError, not propagate as-is.
    SelectionMaidError subclasses must propagate unchanged.
    """

    def test_filter_returns_new_rawdocument_instance(self) -> None:
        """filter() must return a NEW RawDocument, not the same object (D-06)."""
        content = "# Title\n\nSome content."
        doc = _make_doc(content)
        result = HeuristicFilter().filter(doc)
        assert result is not doc

    def test_filter_preserves_non_content_fields(self) -> None:
        """filter() must preserve filename, page_count, and format fields (D-06)."""
        content = "# Title\n\nSome content."
        doc = RawDocument(
            content=content,
            filename="my_report.pdf",
            page_count=42,
            format="pdf",
        )
        result = HeuristicFilter().filter(doc)
        assert result.filename == "my_report.pdf"
        assert result.page_count == 42
        assert result.format == "pdf"

    def test_filter_error_wraps_unexpected_exceptions(self) -> None:
        """Unexpected exceptions in filter() are wrapped as FilterError (D-16)."""
        from unittest.mock import patch

        from selection_maid.errors import FilterError

        doc = _make_doc("Some content.")
        f = HeuristicFilter()
        # Patch _apply_rules to raise an unexpected error
        with (
            patch.object(f, "_apply_rules", side_effect=RuntimeError("boom")),
            pytest.raises(FilterError) as exc_info,
        ):
            f.filter(doc)
        assert "Filtering failed" in exc_info.value.message

    def test_filter_error_passes_through_selection_maid_errors(self) -> None:
        """SelectionMaidError propagates unchanged through filter() (D-16)."""
        from unittest.mock import patch

        from selection_maid.errors import FilterError

        doc = _make_doc("Some content.")
        f = HeuristicFilter()
        original_error = FilterError("already a domain error")
        with (
            patch.object(f, "_apply_rules", side_effect=original_error),
            pytest.raises(FilterError) as exc_info,
        ):
            f.filter(doc)
        assert exc_info.value is original_error
