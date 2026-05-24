"""Tests for DoclingAdapter.

Test class organisation:
  TestDoclingAdapterUnit        -- unit tests with mock converter (always run)
  TestDoclingAdapterIntegration -- integration tests with real Docling (skip if
                                   fixtures unavailable per D-27)

Plans that populate these classes:
  02-02 (extract() implementation) -> both unit and integration tests
  02-03 (EXT-04/05/06/07 format fidelity) -> integration tests
  02-04 (timeout mechanism) -> unit tests
  02-05 (error wrapping) -> unit + integration tests
"""

from __future__ import annotations


class TestDoclingAdapterUnit:
    """Unit tests -- mock converter, no real Docling, always run."""

    def test_placeholder(self) -> None:
        pass


class TestDoclingAdapterIntegration:
    """Integration tests -- real Docling converter, real fixture files.

    Each test must check if its fixture is None and call pytest.skip() if so
    (D-27: graceful skip on connectivity failure, no CI block).
    """

    def test_placeholder(self) -> None:
        pass
