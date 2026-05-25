"""Generate adversarial test fixtures for SelectionMaid integration hardening.

Run with: uv run python tests/fixtures/generate_adversarial.py

Fixtures produced in tests/fixtures/adversarial/:
  corrupt.pdf       -- 1KB of random bytes (corrupted PDF)
  empty.pdf         -- 0-byte file
  spoofed.pdf       -- plain text file with .pdf extension
  protected.pdf     -- AES-256 encrypted PDF (password: "test")
  large_sample.pdf  -- concatenated sample.pdf until > 40MB

Prerequisites:
  - tests/fixtures/sample.pdf must exist (downloaded by integration test conftest.py)
  - pypdf must be installed (uv add --dev pypdf)
"""

from __future__ import annotations

import os
import random
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent
ADV_DIR = FIXTURES_DIR / "adversarial"
SAMPLE_PDF = FIXTURES_DIR / "sample.pdf"


def _check_prerequisites() -> bool:
    """Verify required files and packages are available."""
    if not SAMPLE_PDF.exists():
        print(
            f"ERROR: {SAMPLE_PDF} not found.\n"
            "Run integration tests first to download fixtures:\n"
            "  uv run pytest tests/adapters/extractor/test_docling_adapter.py -k pdf",
            file=sys.stderr,
        )
        return False
    try:
        import pypdf  # noqa: F401
    except ImportError:
        print(
            "ERROR: pypdf not installed.\n"
            "Run: uv add --dev pypdf",
            file=sys.stderr,
        )
        return False
    return True


def generate_corrupt_pdf(target: Path) -> None:
    """Generate a 1KB file filled with random bytes."""
    print(f"  Generating {target.name}...")
    rng = random.Random(42)  # seeded for reproducibility
    with open(target, "wb") as f:
        f.write(bytes(rng.getrandbits(8) for _ in range(1024)))


def generate_empty_pdf(target: Path) -> None:
    """Generate a 0-byte file with .pdf extension."""
    print(f"  Generating {target.name}...")
    target.write_bytes(b"")


def generate_spoofed_pdf(target: Path) -> None:
    """Generate a plain text file renamed to .pdf."""
    print(f"  Generating {target.name}...")
    target.write_text("I am a text file", encoding="utf-8")


def generate_protected_pdf(target: Path) -> None:
    """Encrypt sample.pdf with password 'test' using pypdf."""
    print(f"  Generating {target.name}...")
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(SAMPLE_PDF)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt("test")
    with open(target, "wb") as f:
        writer.write(f)


def generate_large_pdf(target: Path, target_bytes: int = 40 * 1024 * 1024) -> None:
    """Concatenate sample.pdf bytes until the file exceeds target_bytes."""
    print(f"  Generating {target.name} (target: {target_bytes // (1024*1024)}MB)...")
    sample_data = SAMPLE_PDF.read_bytes()
    with open(target, "wb") as f:
        while f.tell() < target_bytes:
            f.write(sample_data)
    size = target.stat().st_size
    print(f"    Done: {size / (1024*1024):.1f}MB")


def main() -> int:
    """Generate all adversarial fixtures. Returns 0 on success, 1 on failure."""
    print("SelectionMaid — Adversarial Fixture Generator")
    print(f"Output directory: {ADV_DIR}")
    print()

    if not _check_prerequisites():
        return 1

    ADV_DIR.mkdir(parents=True, exist_ok=True)

    generators = [
        (ADV_DIR / "corrupt.pdf", generate_corrupt_pdf),
        (ADV_DIR / "empty.pdf", generate_empty_pdf),
        (ADV_DIR / "spoofed.pdf", generate_spoofed_pdf),
        (ADV_DIR / "protected.pdf", generate_protected_pdf),
        (ADV_DIR / "large_sample.pdf", generate_large_pdf),
    ]

    for target, generator in generators:
        generator(target)  # type: ignore[call-arg]

    print()
    print("All adversarial fixtures generated successfully.")
    print()
    # Summary
    for target, _ in generators:
        size = os.path.getsize(target)
        print(f"  {target.name:<20} {size:>12,} bytes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
