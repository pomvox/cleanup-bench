"""Pinned per-item metric tests (docs/spec.md sections 6.2 to 6.9).

Each expected number is worked by hand in a comment next to the assertion.
"""

from __future__ import annotations

import math

import pytest

from cleanupbench.scorer.metrics import (
    BETA,
    best_edit_counts,
    best_word_loss,
    exact_match,
    f_beta,
    insertion_rate,
    is_noop_item,
    over_cleaned,
    precision_recall,
    score_item,
    slot_failure,
    word_loss,
)


def test_beta_and_f_formula():
    assert BETA == 0.5
    # CoNLL-2014: F0.5 = (1 + 0.25) * P * R / (0.25 * P + R). With P = 0.5, R = 1.0:
    # 1.25 * 0.5 * 1.0 / (0.125 + 1.0) = 0.625 / 1.125 = 0.5555...
    assert math.isclose(f_beta(0.5, 1.0), 0.625 / 1.125)
    # Precision weighs more: P = 1.0, R = 0.5 -> 1.25 * 0.5 / (0.25 + 0.5) = 0.625 / 0.75 = 0.8333...
    assert math.isclose(f_beta(1.0, 0.5), 0.625 / 0.75)
    assert f_beta(0.0, 0.0) == 0.0
    assert f_beta(None, 1.0) is None
    assert f_beta(1.0, None) is None


def test_precision_recall_undefined_is_none():
    assert precision_recall(0, 0, 0) == (None, None)
    assert precision_recall(0, 0, 2) == (None, 0.0)
    assert precision_recall(0, 3, 0) == (0.0, None)
    assert precision_recall(2, 2, 6) == (0.5, 0.25)


# --- metric 1 ---------------------------------------------------------------------


def test_edit_counts_perfect_output():
    src = "um so let's go"
    ref = "Let's go."
    # Output equals the reference: both extractions give [Edit(0,3,("Let's",)), Edit(4,4,("."))]
    assert best_edit_counts(src, "Let's go.", [ref]) == (2, 0, 0, 0)


def test_edit_counts_identity_output_is_all_false_negatives():
    src = "um so let's go"
    assert best_edit_counts(src, src, ["Let's go."]) == (0, 0, 2, 0)


def test_edit_counts_partial_credit():
    src = "um so let's go"
    # Output removes the fillers and cases but forgets the period: TP = 1 (the first edit), FN = 1.
    assert best_edit_counts(src, "Let's go", ["Let's go."]) == (1, 0, 1, 0)
    # Output removes fillers but with the wrong replacement text ("lets"): FP = 1, FN = 2.
    assert best_edit_counts(src, "lets go.", ["Let's go."]) == (1, 1, 1, 0)


def test_best_reference_is_chosen_per_item():
    src = "we sold twenty five units"
    refs = ["We sold twenty five units.", "We sold 25 units."]
    # Output matches the second reference exactly -> all three edits (We, 25, .) are TP against ref 1.
    tp, fp, fn, idx = best_edit_counts(src, "We sold 25 units.", refs)
    assert (tp, fp, fn, idx) == (3, 0, 0, 1)
    # Output matches the first reference -> ref 0.
    assert best_edit_counts(src, "We sold twenty five units.", refs)[3] == 0


def test_no_output_edits_picks_fewest_false_negatives():
    src = "hello there"
    refs = ["Hello there.", "hello there"]  # second reference is a noop
    tp, fp, fn, idx = best_edit_counts(src, src, refs)
    assert (tp, fp, fn, idx) == (0, 0, 0, 1)


# --- metric 2 ---------------------------------------------------------------------


def test_exact_match_uses_minimal_normalizer_only():
    assert exact_match("Let’s go.", ["Let's go."])
    assert exact_match("  Let's go. ", ["Let's go."])
    assert not exact_match("let's go.", ["Let's go."])  # case counts
    assert not exact_match("Let's go", ["Let's go."])  # punctuation counts
    assert exact_match("", [""])


# --- metric 3 ---------------------------------------------------------------------


def test_word_loss_hand_worked():
    ref = "Never merge a change like this without a review."
    # reference content tokens: never merge a change like this without a review = 9 tokens ("a" twice)
    # output drops "never": missing 1 of 9
    assert math.isclose(word_loss("Merge a change like this without a review.", ref), 1 / 9)
    # output drops nothing (only casing/punctuation differ): 0
    assert word_loss("never merge a change like this without a review", ref) == 0.0
    # output drops one of the two "a": multiset difference catches it: 1/9
    assert math.isclose(word_loss("Never merge change like this without a review.", ref), 1 / 9)
    # empty output: everything lost
    assert word_loss("", ref) == 1.0
    # empty reference: no loss possible
    assert word_loss("anything", "") == 0.0


def test_word_loss_is_against_reference_not_input():
    # Sanctioned deletions (fillers, reparandum) are not losses.
    assert best_word_loss("Let's meet on Friday at noon.", ["Let's meet on Friday at noon."]) == 0.0
    # Keeping the reparandum is not a loss either (it is an FN edit in metric 1).
    assert best_word_loss("Let's meet on Tuesday wait no Friday at noon.", ["Let's meet on Friday at noon."]) == 0.0


def test_best_word_loss_takes_min_over_references():
    refs = ["We sold twenty five units.", "We sold 25 units."]
    assert best_word_loss("We sold 25 units.", refs) == 0.0
    # Against ref 0 the output "We sold 25 units." misses "twenty" and "five": 2/5; min is 0.
    assert math.isclose(word_loss("We sold 25 units.", refs[0]), 2 / 5)


# --- metric 4 ---------------------------------------------------------------------


def test_insertion_rate_hand_worked():
    src = "um so let's go"
    refs = ["Let's go."]
    # Output "Let's go now.": content tokens let's, go, now = 3; "now" in neither input nor refs: 1/3
    assert math.isclose(insertion_rate(src, "Let's go now.", refs), 1 / 3)
    # Casing never counts
    assert insertion_rate(src, "LET'S GO.", refs) == 0.0
    # Duplicating an input word is not an insertion (metric 1 sees it as an FP edit)
    assert insertion_rate(src, "Let's go go.", refs) == 0.0
    # Empty output: 0
    assert insertion_rate(src, "", refs) == 0.0
    # A numeral no reference sanctions counts (section 6.5)
    assert math.isclose(insertion_rate("step one is easy", "Step 1 is easy.", ["Step one is easy."]), 1 / 4)


# --- metric 5 ---------------------------------------------------------------------


def test_slot_failure():
    assert slot_failure("anything", [], []) is None
    assert slot_failure("Let's meet on Friday.", ["friday"], ["tuesday"]) is False
    assert slot_failure("Let's meet on Tuesday.", ["friday"], ["tuesday"]) is True
    assert slot_failure("Let's meet on Friday.", ["friday"], ["friday"]) is True
    assert slot_failure("", ["friday"], []) is True


# --- metric 6 ---------------------------------------------------------------------


def test_noop_and_over_clean():
    src = "never merge a change like this"
    assert is_noop_item(src, ["Never merge a change like this."])
    assert not is_noop_item(src, ["Never merge a change like this.", "Merge a change like this."])
    assert not over_cleaned(src, "Never merge a change like this.")
    assert over_cleaned(src, "Merge a change like this.")
    assert over_cleaned(src, "")


# --- combined ----------------------------------------------------------------------


def base_kwargs(**overrides):
    kw = dict(
        item_id="x-core-0001",
        category="fillers",
        slice_=None,
        input_text="um so let's go",
        references=["Let's go."],
        must_contain=["go"],
        must_not_contain=["um"],
        output_text="Let's go.",
        outcome="cleaned",
        fallback_reason=None,
        edits=None,
        latency_ms=1.0,
    )
    kw.update(overrides)
    return kw


def test_score_item_perfect():
    s = score_item(**base_kwargs())
    assert (s.tp, s.fp, s.fn) == (2, 0, 0)
    assert s.exact_match and s.word_loss == 0.0 and s.insertion == 0.0
    assert s.slot_fail is False and s.noop is False and s.over_clean is None
    assert s.status == "cleaned" and s.valid


def test_score_item_identity_output():
    s = score_item(**base_kwargs(output_text="um so let's go", outcome="unchanged"))
    assert (s.tp, s.fp, s.fn) == (0, 0, 2)
    assert not s.exact_match
    assert s.word_loss == 0.0  # nothing in the reference is missing
    assert s.slot_fail is True  # "um" still present
    assert s.status == "unchanged"


def test_score_item_empty_output_with_nonempty_reference():
    s = score_item(**base_kwargs(output_text="", outcome="cleaned"))
    assert s.status == "empty"
    assert s.word_loss == 1.0
    assert (s.tp, s.fp, s.fn) == (0, 1, 2)  # one deletion edit (FP), two reference edits missed
    assert s.slot_fail is True


def test_score_item_empty_output_with_empty_reference():
    s = score_item(
        **base_kwargs(
            input_text="um uh so yeah",
            references=[""],
            must_contain=[],
            must_not_contain=["um"],
            output_text="",
            outcome="cleaned",
        )
    )
    assert s.status == "empty"
    assert s.exact_match
    assert s.word_loss == 0.0 and s.insertion == 0.0
    assert (s.tp, s.fp, s.fn) == (1, 0, 0)  # the whole-input deletion matches the reference edit
    assert s.slot_fail is False


def test_score_item_invalid_edits():
    s = score_item(**base_kwargs(edits=[{"start": 0, "end": 1, "replacement": "L"}]))
    assert s.status == "invalid" and not s.valid
    assert "byte for byte" in s.invalid_reason
    assert (s.tp, s.fp, s.fn) == (0, 0, 0)


def test_score_item_valid_edits():
    # Input "um so let's go" (14 bytes) -> "Let's go." as one contiguous replacement.
    s = score_item(**base_kwargs(edits=[{"start": 0, "end": 14, "replacement": "Let's go."}]))
    assert s.valid and s.exact_match


def test_score_item_fallback_must_echo_input():
    s = score_item(**base_kwargs(output_text="um so let's go", outcome="fallback", fallback_reason="rejected"))
    assert s.status == "fallback" and s.valid
    assert s.fallback_reason == "rejected"
    bad = score_item(**base_kwargs(output_text="Let's go.", outcome="fallback", fallback_reason="rejected"))
    assert bad.status == "invalid"


def test_score_item_error_is_invalid():
    s = score_item(**base_kwargs(output_text="", outcome="error"))
    assert s.status == "invalid" and s.invalid_reason == "adapter error"


def test_score_item_noop_over_clean():
    s = score_item(
        **base_kwargs(
            category="negatives",
            slice_="negation",
            input_text="never merge a change like this",
            references=["Never merge a change like this."],
            must_contain=["never"],
            must_not_contain=[],
            output_text="Merge a change like this.",
        )
    )
    assert s.noop is True and s.over_clean is True and s.slot_fail is True
    assert math.isclose(s.word_loss, 1 / 6)


@pytest.mark.parametrize("latency", [None, 0.0, 12.5])
def test_latency_passthrough(latency):
    assert score_item(**base_kwargs(latency_ms=latency)).latency_ms == latency
