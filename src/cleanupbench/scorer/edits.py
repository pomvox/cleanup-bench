"""Edit accountability (docs/spec.md section 6.9; engine docs/contract.md).

A system that returns byte-range edits must reconstruct its output from the
input exactly. Ranges are half-open UTF-8 byte offsets into the input, must be
ordered, non-overlapping, within bounds and on scalar (code point) boundaries.
"""

from __future__ import annotations

from typing import Any


def _is_scalar_boundary(data: bytes, offset: int) -> bool:
    if offset == 0 or offset == len(data):
        return True
    if offset < 0 or offset > len(data):
        return False
    # A UTF-8 continuation byte has the bit pattern 10xxxxxx.
    return (data[offset] & 0xC0) != 0x80


def check_edits(
    input_text: str, output_text: str, edits: list[dict[str, Any]] | tuple[dict[str, Any], ...]
) -> str | None:
    """Return None when the edits reconstruct the output, else a reason string."""
    src = input_text.encode("utf-8")
    out = output_text.encode("utf-8")
    pieces: list[bytes] = []
    cursor = 0
    prev_was_insertion = False
    for n, edit in enumerate(edits):
        try:
            start = int(edit["start"])
            end = int(edit["end"])
            replacement = str(edit["replacement"]).encode("utf-8")
        except (KeyError, TypeError, ValueError):
            return f"edit {n}: malformed"
        if start < 0 or end < start or end > len(src):
            return f"edit {n}: range [{start}, {end}) out of bounds for {len(src)} bytes"
        if start < cursor:
            return f"edit {n}: overlaps or is not ordered after the previous edit"
        if start == cursor and prev_was_insertion and start == end:
            return f"edit {n}: two insertions at the same offset are ambiguous"
        if not _is_scalar_boundary(src, start) or not _is_scalar_boundary(src, end):
            return f"edit {n}: range [{start}, {end}) is not on a scalar boundary"
        pieces.append(src[cursor:start])
        pieces.append(replacement)
        cursor = end
        prev_was_insertion = start == end
    pieces.append(src[cursor:])
    rebuilt = b"".join(pieces)
    if rebuilt != out:
        return "applying the edits to the input does not reproduce the output byte for byte"
    return None
