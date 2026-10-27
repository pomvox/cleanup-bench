"""Aggregation and uncertainty (docs/spec.md sections 6.2, 6.11, 6.13), worked by hand."""

from __future__ import annotations

import math

from cleanupbench.scorer.aggregate import (
    aggregate_category,
    bootstrap_f,
    mean_and_se_binary,
    mean_and_se_rate,
    percentile_nearest_rank,
)
from cleanupbench.scorer.metrics import ItemScore


def mk(id_, **kw) -> ItemScore:
    base = dict(category="fillers", slice=None, outcome="cleaned", fallback_reason=None, status="cleaned")
    base.update(kw)
    return ItemScore(id=id_, **base)


def test_mean_and_se_binary():
    # p = 2/4 = 0.5; SE = sqrt(0.5 * 0.5 / 4) = 0.25
    p, se, n = mean_and_se_binary([True, False, True, False])
    assert (p, se, n) == (0.5, 0.25, 4)
    assert mean_and_se_binary([]) == (None, None, 0)
    # p = 1: SE = 0
    assert mean_and_se_binary([True, True]) == (1.0, 0.0, 2)


def test_mean_and_se_rate():
    # values 0, 0.5, 1: mean 0.5; sample variance = ((0.25 + 0 + 0.25) / 2) = 0.25; sd = 0.5; SE = 0.5/sqrt(3)
    mean, se, n = mean_and_se_rate([0.0, 0.5, 1.0])
    assert mean == 0.5 and n == 3
    assert math.isclose(se, 0.5 / math.sqrt(3))
    assert mean_and_se_rate([0.3]) == (0.3, None, 1)
    assert mean_and_se_rate([]) == (None, None, 0)


def test_percentile_nearest_rank():
    vals = [1.0, 2.0, 3.0, 4.0, 5.0]
    # p50: rank ceil(0.5 * 5) = 3 -> 3.0; p95: rank ceil(4.75) = 5 -> 5.0; p2.5: rank 1 -> 1.0
    assert percentile_nearest_rank(vals, 50) == 3.0
    assert percentile_nearest_rank(vals, 95) == 5.0
    assert percentile_nearest_rank(vals, 2.5) == 1.0
    assert percentile_nearest_rank([7.0], 95) == 7.0


def test_bootstrap_is_deterministic_and_bounded():
    counts = [(1, 0, 0), (0, 1, 1), (2, 0, 1), (1, 1, 0)]
    a = bootstrap_f(counts, resamples=200, seed=1)
    b = bootstrap_f(counts, resamples=200, seed=1)
    assert a == b
    assert a["defined_resamples"] == 200
    assert 0.0 <= a["low"] <= a["high"] <= 1.0
    assert bootstrap_f([], resamples=10, seed=1)["defined_resamples"] == 0
    # All items with no edits at all: F undefined in every resample.
    assert bootstrap_f([(0, 0, 0), (0, 0, 0)], resamples=10, seed=1)["defined_resamples"] == 0


def test_aggregate_category_hand_worked():
    scores = [
        mk("a-core-0001", tp=2, fp=0, fn=0, exact_match=True, word_loss=0.0, insertion=0.0, slot_fail=False),
        mk("a-core-0002", tp=1, fp=1, fn=1, exact_match=False, word_loss=0.2, insertion=0.1, slot_fail=True),
        mk(
            "a-core-0003", tp=0, fp=0, fn=2, exact_match=False, word_loss=0.0, insertion=0.0, slot_fail=None,
            status="unchanged", outcome="unchanged",
        ),
        mk("a-core-0004", status="invalid", invalid_reason="adapter error", outcome="error"),
        mk(
            "a-core-0005", tp=0, fp=0, fn=0, exact_match=True, word_loss=0.0, insertion=0.0, slot_fail=False,
            noop=True, over_clean=False,
        ),
        mk(
            "a-core-0006", tp=0, fp=1, fn=0, exact_match=False, word_loss=0.5, insertion=0.0, slot_fail=True,
            noop=True, over_clean=True, status="fallback", outcome="fallback", fallback_reason="rejected",
        ),
    ]
    agg = aggregate_category(scores, bootstrap_resamples=50, bootstrap_seed=3)
    assert agg["n"] == 6 and agg["n_valid"] == 5
    # TP = 2+1+0+0+0 = 3; FP = 0+1+0+0+1 = 2; FN = 0+1+2+0+0 = 3
    assert (agg["edit"]["tp"], agg["edit"]["fp"], agg["edit"]["fn"]) == (3, 2, 3)
    # P = 3/5 = 0.6; R = 3/6 = 0.5; F0.5 = 1.25 * 0.6 * 0.5 / (0.25 * 0.6 + 0.5) = 0.375 / 0.65
    assert agg["edit"]["precision"] == 0.6 and agg["edit"]["recall"] == 0.5
    assert math.isclose(agg["edit"]["f0_5"], round(0.375 / 0.65, 6))
    # exact match over 5 valid: 2/5 = 0.4
    assert agg["exact_match"]["mean"] == 0.4 and agg["exact_match"]["n"] == 5
    # word loss mean over 5 valid: (0 + 0.2 + 0 + 0 + 0.5) / 5 = 0.14
    assert math.isclose(agg["word_loss"]["mean"], 0.14)
    # slot fail over items with slots (4 of the valid 5): 2/4 = 0.5
    assert agg["slot_fail"]["mean"] == 0.5 and agg["slot_fail"]["n"] == 4
    # over-clean over noop items (2): 1/2
    assert agg["over_clean"]["mean"] == 0.5 and agg["over_clean"]["n"] == 2
    assert agg["status"] == {
        "cleaned": 3,
        "unchanged": 1,
        "fallback": 1,
        "empty": 0,
        "invalid": 1,
        "fallback_reasons": {"rejected": 1},
        "invalid_reasons": ["adapter error"],
    }
    assert agg["edit"]["f0_5_bootstrap_95"]["resamples"] == 50


def test_aggregate_all_noop_category_has_null_f():
    scores = [mk("n-core-0001", noop=True, over_clean=False), mk("n-core-0002", noop=True, over_clean=False)]
    agg = aggregate_category(scores, bootstrap_resamples=10, bootstrap_seed=1)
    assert agg["edit"]["precision"] is None
    assert agg["edit"]["recall"] is None
    assert agg["edit"]["f0_5"] is None
    assert agg["over_clean"]["mean"] == 0.0
