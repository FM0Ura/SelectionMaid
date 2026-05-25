"""HeuristicFilter — concrete FilterPort implementation using heuristic rules.

Addresses structural noise in Markdown content produced by DoclingAdapter:
  - Repetitive headers/footers detected via frequency analysis (D-31 to D-34)
  - Isolated page numbers (Arabic, Roman, hyphenated) removed via regex (D-35, D-36)
  - Excessive whitespace compressed to at most one blank line (D-37)

This module uses only stdlib (re, collections.Counter, dataclasses.replace).
No imports from selection_maid.config — thresholds are injected via constructor (D-39).

Decision references:
  D-31: Safety net strategy — trust Docling first.
  D-32: Frequency analysis over full Markdown blob.
  D-33: Exclusions — heading lines (#) and table lines (|) never removed.
  D-34: Default min_repeat=3 threshold.
  D-35: Page number regex patterns compiled as module constants.
  D-36: Only completely isolated lines match; strip whitespace before comparing.
  D-37: 3+ newlines → exactly 2 newlines; applied last.
  D-39: Constructor injection: HeuristicFilter(min_repeat, max_line_len).
  D-41: File location: src/selection_maid/adapters/filter/heuristic.py.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import replace

from selection_maid.domain.models import RawDocument
from selection_maid.errors import FilterError, SelectionMaidError

# ---------------------------------------------------------------------------
# Module-level compiled regex constants (D-35)
# Non-backtracking patterns to avoid ReDoS (T-03-02).
# ---------------------------------------------------------------------------

#: Pure Arabic digit page numbers: "1", "42", "100"
_ARABIC_RE: re.Pattern[str] = re.compile(r"^\d+$")

#: Roman numeral page numbers (case-insensitive, 1–10 chars to avoid false positives).
#: "i", "iv", "XII", "viii", "MCMLXXXIX" (9 chars) — but NOT 11+ char strings (D-35).
_ROMAN_RE: re.Pattern[str] = re.compile(r"^[ivxlcdm]{1,10}$", re.IGNORECASE)

#: Hyphenated page numbers: "- 10 -", "-42-", "- iv -"
_HYPHEN_RE: re.Pattern[str] = re.compile(
    r"^-\s*(\d+|[ivxlcdm]{1,10})\s*-$", re.IGNORECASE
)


class HeuristicFilter:
    """Concrete FilterPort implementation using heuristic rules.

    Addresses repetitive headers/footers, isolated page numbers, and
    excessive whitespace in Markdown content.

    Satisfies FilterPort Protocol via structural typing (no inheritance required).
    """

    def __init__(
        self,
        min_repeat: int = 3,
        max_line_len: int = 80,
    ) -> None:
        """Initialise the filter with configurable thresholds (D-39).

        Args:
            min_repeat: Minimum number of times a line must appear to be
                considered a repeated header/footer. Defaults to 3 (D-34).
            max_line_len: Maximum line length in characters for a line to be
                considered a header/footer candidate. Defaults to 80 (D-32).
        """
        self._min_repeat = min_repeat
        self._max_line_len = max_line_len

    def filter(self, document: RawDocument) -> RawDocument:
        """Clean structural noise from Markdown content and return a new document.

        Rule application order (important for correctness):
          1. Frequency-based header/footer removal (D-31 to D-34)
          2. Isolated page number removal (D-35, D-36)
          3. Whitespace compression (D-37) — applied last

        Args:
            document: RawDocument with Markdown content to clean.

        Returns:
            A new RawDocument with cleaned content. All other fields are
            preserved unchanged via dataclasses.replace (D-06).

        Raises:
            FilterError: Unexpected error during filtering (D-16).
                SelectionMaidError subclasses propagate unchanged.
        """
        try:
            cleaned_content = self._apply_rules(document.content)
            return replace(document, content=cleaned_content)
        except SelectionMaidError:
            raise
        except Exception as exc:
            raise FilterError(
                f"Filtering failed: {exc}",
                cause=exc,
            ) from exc

    def _apply_rules(self, content: str) -> str:
        """Apply all filtering rules in the correct order.

        Args:
            content: Raw Markdown string to process.

        Returns:
            Cleaned Markdown string.
        """
        # Rule 1: Remove repeated headers/footers (D-31 to D-34)
        content = self._remove_repeated_lines(content)
        # Rule 2: Remove isolated page numbers (D-35, D-36)
        content = self._remove_page_numbers(content)
        # Rule 3: Compress excessive whitespace (D-37) — must be last
        content = self._compress_whitespace(content)
        return content

    def _remove_repeated_lines(self, content: str) -> str:
        """Remove lines that repeat >= min_repeat times (header/footer candidates).

        Candidates (D-32): lines with stripped length <= max_line_len.
        Exclusions (D-33): lines starting with '#' (headings) or '|' (tables).

        Args:
            content: Markdown string to process.

        Returns:
            Markdown string with repeated header/footer lines removed.
        """
        lines = content.splitlines()

        # Build frequency map of candidate lines
        candidates: list[str] = []
        for line in lines:
            stripped = line.strip()
            if (
                stripped  # not empty
                and len(stripped) <= self._max_line_len
                and not stripped.startswith("#")  # D-33: exclude headings
                and "|" not in stripped  # D-33: exclude table lines
            ):
                candidates.append(stripped)

        counts = Counter(candidates)
        to_remove = {
            line for line, count in counts.items() if count >= self._min_repeat
        }

        if not to_remove:
            return content

        # Filter out lines whose stripped form is in to_remove
        filtered_lines = [
            line for line in lines if line.strip() not in to_remove
        ]
        return "\n".join(filtered_lines)

    def _remove_page_numbers(self, content: str) -> str:
        """Remove completely isolated page number lines (D-35, D-36).

        A line qualifies if its stripped form matches one of:
          - Pure Arabic digits: "1", "42"
          - Roman numerals (case-insensitive, 1–10 chars): "iv", "XII"
          - Hyphenated: "- 10 -", "-5-"

        Lines are compared after stripping whitespace (D-36). Numbers
        inline within paragraphs are NOT affected.

        Args:
            content: Markdown string to process.

        Returns:
            Markdown string with isolated page number lines removed.
        """
        lines = content.splitlines()
        filtered_lines = [
            line
            for line in lines
            if not self._is_page_number(line)
        ]
        return "\n".join(filtered_lines)

    @staticmethod
    def _is_page_number(line: str) -> bool:
        """Return True if the entire stripped line is a page number (D-35, D-36).

        Args:
            line: A single line from the document.

        Returns:
            True if line (stripped) matches a page number pattern.
        """
        stripped = line.strip()
        if not stripped:
            return False
        return bool(
            _ARABIC_RE.match(stripped)
            or _ROMAN_RE.match(stripped)
            or _HYPHEN_RE.match(stripped)
        )

    @staticmethod
    def _compress_whitespace(content: str) -> str:
        """Compress sequences of 3+ newlines to exactly 2 newlines (D-37).

        Also normalizes whitespace-only lines to empty lines before
        applying the compression, so whitespace-only separators are treated
        as blank lines.

        Args:
            content: Markdown string to process.

        Returns:
            Markdown string with excessive blank lines compressed.
        """
        # Normalize whitespace-only lines to truly empty lines
        normalized = "\n".join(
            line if line.strip() else "" for line in content.splitlines()
        )
        # Compress 3+ consecutive newlines to exactly 2
        return re.sub(r"\n{3,}", "\n\n", normalized)


def build_heuristic_filter(
    config: "FilterConfig | None" = None,
) -> HeuristicFilter:
    """Factory function for HeuristicFilter (D-23/D-39).

    Consistent with the build_docling_adapter(), build_markdown_chunker() and
    build_metadata_enricher() factory pattern. Callers (app.py, tests) pass
    the resolved FilterConfig from get_config().filter; calling without
    arguments uses centralized config defaults (D-38, D-39).

    Args:
        config: FilterConfig instance with resolved configuration values.
            ``None`` (default) resolves to ``get_config().filter`` (D-38).
            Use ``get_config().filter`` to obtain from the centralized config.

    Returns:
        A fully configured HeuristicFilter instance.
    """
    from selection_maid.config import FilterConfig as _FilterConfig  # noqa: PLC0415
    from selection_maid.config import get_config  # noqa: PLC0415 avoid circular import

    resolved: _FilterConfig = config if config is not None else get_config().filter
    return HeuristicFilter(
        min_repeat=resolved.min_repeat,
        max_line_len=resolved.max_line_len,
    )
