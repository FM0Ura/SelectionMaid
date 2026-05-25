"""Memory regression audit for DoclingAdapter.

Validates that proactive memory management (gc.collect + backend.unload in
try/finally) prevents unbounded RAM growth across repeated extractions
(D-31, D-32 from docling.py decision log).

Design decisions:
  - 5 consecutive extractions (plan originally specified 20; reduced to 5 because
    each Docling call takes 10-30s -- 5 iterations give meaningful signal in ~75s
    without a 10-minute test run that would time out most CI pipelines).
  - Warm-up extraction before baseline measurement: Docling lazy-loads model
    weights on the first convert() call, causing a one-time RSS spike (~1 GB).
    Measuring RSS after warm-up gives an accurate baseline for detecting genuine
    unbounded growth in subsequent calls. The 2x rule is applied to the
    post-warm-up baseline so that lazy model loading does not trigger a false
    positive.
  - Assertion: final_rss <= 2 * warmup_rss (2x rule allows for caching and
    internal state while still catching genuine unbounded leaks).
  - Marked @pytest.mark.slow so fast CI runs can skip with: -m "not slow".
  - Uses real_converter fixture from tests/conftest.py (session-scoped, model
    loading happens once for the whole session).

Run with verbose RSS output:
    pytest tests/test_memory_regression.py -s -v
"""

from __future__ import annotations

import gc
import os
from pathlib import Path
from typing import Any

import psutil
import pytest

from selection_maid.adapters.extractor.docling import DoclingAdapter
from selection_maid.domain.models import RawInput

# Number of consecutive extractions to perform AFTER the warm-up call.
# Set to 5 (instead of 20) to keep the test wall-clock time under 2 minutes on
# a CPU-only machine. The 2x RSS assertion remains meaningful at this count.
_EXTRACTION_COUNT = 5

# Threshold: final RSS must not exceed this multiple of warm-up RSS.
# The warm-up baseline already includes all lazy-loaded model weights, so a
# genuine leak should push the ratio well above 2x, while normal caching and
# temporary buffers stay well below it.
_RSS_GROWTH_LIMIT = 2.0


def _current_rss_mb() -> float:
    """Return resident set size of the current process in megabytes."""
    info = psutil.Process(os.getpid()).memory_info()
    return info.rss / (1024 * 1024)


@pytest.mark.slow
def test_memory_leak_audit(
    real_converter: Any,
    real_pdf_path: Path | None,
) -> None:
    """Audit RSS growth over repeated DoclingAdapter.extract() calls.

    Validates that the try/finally gc.collect + backend.unload hardening
    introduced in Phase 07-01 prevents unbounded RAM growth.

    Measurement strategy:
      1. Warm-up: one extraction to trigger lazy model weight loading (DocLayNet,
         TableFormer) that would otherwise inflate the baseline RSS.
      2. Baseline: measure RSS *after* warm-up and a forced gc.collect().
      3. Audit loop: _EXTRACTION_COUNT extractions, measuring RSS after each.
      4. Assert: final_rss <= _RSS_GROWTH_LIMIT * warmup_rss.

    The test fails if post-warm-up RSS more than doubles, which would indicate
    genuine unbounded memory growth rather than expected one-time model loading.

    Args:
        real_converter: Session-scoped Docling DocumentConverter (from conftest).
        real_pdf_path:  Path to tests/fixtures/sample.pdf, or None if the file
                        could not be downloaded.
    """
    if real_pdf_path is None:
        pytest.skip("sample.pdf not available (download failed or no connectivity)")

    adapter = DoclingAdapter(converter=real_converter, timeout_seconds=120)
    raw_input = RawInput(
        path=real_pdf_path,
        filename="sample.pdf",
        mime_type="application/pdf",
    )

    pre_warmup_rss = _current_rss_mb()
    print(f"\n[memory_audit] pre-warmup RSS: {pre_warmup_rss:.1f} MB")

    # Warm-up extraction: forces lazy model weight loading (DocLayNet + TableFormer).
    # This one-time ~1 GB RSS spike must not be counted against the leak threshold.
    warmup_result = adapter.extract(raw_input)
    assert warmup_result.content, "Warm-up extraction returned empty content"

    # Force GC after warm-up to release any temporary allocations before baseline.
    gc.collect()

    warmup_rss = _current_rss_mb()
    print(
        f"[memory_audit] post-warmup RSS: {warmup_rss:.1f} MB  "
        f"(model load cost: +{warmup_rss - pre_warmup_rss:.1f} MB)"
    )

    peak_rss = warmup_rss
    rss_per_iteration: list[float] = []

    for i in range(1, _EXTRACTION_COUNT + 1):
        result = adapter.extract(raw_input)

        # Verify extraction produced content (sanity guard -- a silent failure
        # would produce an empty string and pollute the memory audit).
        assert result.content, f"Iteration {i}: extract() returned empty content"

        current_rss = _current_rss_mb()
        rss_per_iteration.append(current_rss)
        if current_rss > peak_rss:
            peak_rss = current_rss

        print(
            f"[memory_audit] iteration {i:02d}/{_EXTRACTION_COUNT}: "
            f"RSS = {current_rss:.1f} MB  (delta from warmup: "
            f"{current_rss - warmup_rss:+.1f} MB)"
        )

    final_rss = _current_rss_mb()
    growth_ratio = final_rss / warmup_rss

    print(
        f"[memory_audit] final RSS: {final_rss:.1f} MB  |  "
        f"peak RSS: {peak_rss:.1f} MB  |  "
        f"growth ratio (vs warmup): {growth_ratio:.2f}x  "
        f"(limit: {_RSS_GROWTH_LIMIT:.1f}x)"
    )

    assert growth_ratio <= _RSS_GROWTH_LIMIT, (
        f"Memory leak detected: RSS grew {growth_ratio:.2f}x after warm-up "
        f"(warmup={warmup_rss:.1f} MB, final={final_rss:.1f} MB). "
        f"Expected <= {_RSS_GROWTH_LIMIT}x growth after {_EXTRACTION_COUNT} "
        "consecutive extractions post warm-up. "
        "Check D-32 (gc.collect + backend.unload) in DoclingAdapter.extract()."
    )
