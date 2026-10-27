"""Edit accountability (docs/spec.md section 6.9): byte-range edits must rebuild the output."""

from __future__ import annotations

from cleanupbench.scorer.edits import check_edits


def test_single_contiguous_replacement_like_the_engine():
    src = "um hello there"
    out = "Hello there."
    # The engine emits one minimal contiguous replacement; here bytes [0, 14) -> "Hello there."
    assert check_edits(src, out, [{"start": 0, "end": 14, "replacement": "Hello there."}]) is None


def test_multiple_ordered_edits():
    src = "go ahead"
    out = "Go ahead."
    edits = [{"start": 0, "end": 1, "replacement": "G"}, {"start": 8, "end": 8, "replacement": "."}]
    assert check_edits(src, out, edits) is None


def test_no_edits_requires_identical_output():
    assert check_edits("same", "same", []) is None
    assert check_edits("same", "Same", []) is not None


def test_wrong_reconstruction_is_rejected():
    reason = check_edits("um hello", "Hello", [{"start": 0, "end": 3, "replacement": "h"}])
    assert reason is not None and "byte for byte" in reason


def test_out_of_bounds_and_overlap():
    assert "out of bounds" in check_edits("abc", "abc", [{"start": 0, "end": 9, "replacement": ""}])
    assert "overlaps" in check_edits(
        "abcdef", "xx", [{"start": 0, "end": 4, "replacement": "x"}, {"start": 2, "end": 6, "replacement": "x"}]
    )
    assert "out of bounds" in check_edits("abc", "abc", [{"start": 2, "end": 1, "replacement": ""}])


def test_scalar_boundary_in_utf8():
    src = "café au lait"  # é is two bytes: 0xC3 0xA9 at byte offsets 3-4
    assert "scalar boundary" in check_edits(src, src, [{"start": 4, "end": 4, "replacement": ""}])
    # Replacing the whole "é" (bytes 3..5) is fine.
    assert check_edits(src, "cafe au lait", [{"start": 3, "end": 5, "replacement": "e"}]) is None


def test_two_insertions_at_same_offset_are_ambiguous():
    reason = check_edits(
        "ab", "aXYb", [{"start": 1, "end": 1, "replacement": "X"}, {"start": 1, "end": 1, "replacement": "Y"}]
    )
    assert reason is not None and "ambiguous" in reason


def test_malformed_edit():
    assert "malformed" in check_edits("ab", "ab", [{"start": "x"}])
