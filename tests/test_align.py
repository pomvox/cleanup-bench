"""Pinned tests for the aligner and edit extraction (docs/spec.md section 6.2, decision S1).

Every expected edit list is worked by hand from the token sequences written
in the test. Costs are repeated here so a change to either side is visible.
"""

from __future__ import annotations

from cleanupbench.scorer.align import (
    CASE_SUBSTITUTION_COST,
    DELETION_COST,
    INSERTION_COST,
    MATCH_COST,
    SUBSTITUTION_COST,
    Edit,
    align,
    edit_counts,
    extract_edits,
)
from cleanupbench.scorer.text import token_texts


def test_costs_are_pinned():
    assert MATCH_COST == 0.0
    assert CASE_SUBSTITUTION_COST == 0.5
    assert SUBSTITUTION_COST == 1.0
    assert INSERTION_COST == 1.0
    assert DELETION_COST == 1.0


def test_identical_sequences_have_no_edits():
    toks = token_texts("nothing to change here")
    assert extract_edits(toks, toks) == []


def test_pure_deletion_of_fillers_is_one_edit_per_run():
    src = token_texts("um so let's go")  # um so let's go
    tgt = token_texts("Let's go.")  # Let's go .
    # Alignment: delete "um", delete "so", substitute "let's"->"Let's" (case), match "go", insert "."
    # The run [um so let's] -> [Let's] is one edit; "." is a separate insertion after "go".
    assert extract_edits(src, tgt) == [
        Edit(0, 3, ("Let's",)),
        Edit(4, 4, (".",)),
    ]


def test_case_only_change_aligns_to_its_own_word():
    src = token_texts("go ahead")
    tgt = token_texts("Go ahead.")
    assert extract_edits(src, tgt) == [Edit(0, 1, ("Go",)), Edit(2, 2, (".",))]


def test_correction_with_reparandum_deleted():
    src = token_texts("let's meet on tuesday wait no friday at noon")
    # tokens: let's(0) meet(1) on(2) tuesday(3) wait(4) no(5) friday(6) at(7) noon(8)
    tgt = token_texts("Let's meet on Friday at noon.")
    # Let's(0) meet(1) on(2) Friday(3) at(4) noon(5) .(6)
    # "tuesday wait no friday" -> "Friday": delete tuesday, wait, no; case-substitute friday.
    assert extract_edits(src, tgt) == [
        Edit(0, 1, ("Let's",)),
        Edit(3, 7, ("Friday",)),
        Edit(9, 9, (".",)),
    ]


def test_stutter_repetition_collapse():
    src = token_texts("i i i just wanted to to say")
    # i(0) i(1) i(2) just(3) wanted(4) to(5) to(6) say(7)
    tgt = token_texts("I just wanted to say")
    # "i i i" -> "I": the case substitution lands on the last "i" and the first two are deleted,
    # merged into one edit. "to to" -> "to": the later copy is kept (matched), the earlier one deleted.
    assert extract_edits(src, tgt) == [Edit(0, 3, ("I",)), Edit(5, 6, ())]


def test_insertion_only():
    src = token_texts("hello world")
    tgt = token_texts("hello, world")
    assert extract_edits(src, tgt) == [Edit(1, 1, (",",))]


def test_full_deletion_to_empty():
    src = token_texts("um uh so yeah")
    assert extract_edits(src, []) == [Edit(0, 4, ())]


def test_full_replacement():
    src = token_texts("go ahead")
    tgt = token_texts("Okay.")
    assert extract_edits(src, tgt) == [Edit(0, 2, ("Okay", "."))]


def test_align_steps_are_deterministic():
    src = ["a", "b", "b", "c"]
    tgt = ["a", "b", "c"]
    steps = align(src, tgt)
    # One of the two "b"s is deleted; the back-trace order pins which one: the first.
    assert steps == [("M", 0, 0), ("D", 1, -1), ("M", 2, 1), ("M", 3, 2)]
    assert extract_edits(src, tgt) == [Edit(1, 2, ())]


def test_edit_counts_exact_span_and_replacement():
    out = [Edit(0, 1, ("Go",)), Edit(2, 2, (".",))]
    ref = [Edit(0, 1, ("Go",))]
    assert edit_counts(out, ref) == (1, 1, 0)
    assert edit_counts([], ref) == (0, 0, 1)
    assert edit_counts(out, out) == (2, 0, 0)
    # Same span, different replacement: not a TP.
    assert edit_counts([Edit(0, 1, ("go",))], ref) == (0, 1, 1)


def test_long_phrase_deletion_is_one_edit_not_many():
    # Napoles et al.'s gaming concern: a long deletion is one edit here too, which is
    # why word-loss (metric 3) exists alongside F0.5.
    src = token_texts("a quick brown fox jumps over the lazy dog")
    tgt = token_texts("a dog")
    assert extract_edits(src, tgt) == [Edit(1, 8, ())]


def test_repeated_token_keeps_the_later_copy():
    # Both "the"s could match; the back-trace order keeps the later one, deterministically.
    src = token_texts("the quick brown fox jumps over the lazy dog")
    tgt = token_texts("the dog")
    assert extract_edits(src, tgt) == [Edit(0, 6, ()), Edit(7, 8, ())]


def test_tie_between_substitution_and_delete_match_insert_prefers_the_match():
    # "um so let's go" -> "lets go .": cost 4 either way; the path that keeps "go" matched wins.
    src = token_texts("um so let's go")
    tgt = token_texts("lets go.")
    assert align(src, tgt) == [("D", 0, -1), ("D", 1, -1), ("S", 2, 0), ("M", 3, 1), ("I", -1, 2)]
    assert extract_edits(src, tgt) == [Edit(0, 3, ("lets",)), Edit(4, 4, (".",))]
