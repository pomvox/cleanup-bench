"""Per-category aggregation and uncertainty (docs/spec.md sections 6.2, 6.11, 6.13).

Nothing is pooled across categories. Standard errors follow Miller (2024):
binary per-item scores use sqrt(p(1-p)/n); per-item rates use the sample
standard deviation over sqrt(n); the pooled F0.5 gets a paired bootstrap
interval over items with a fixed seed.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from collections.abc import Sequence
from typing import Any

from cleanupbench.scorer.metrics import ItemScore, f_beta, precision_recall

DEFAULT_BOOTSTRAP_RESAMPLES = 1000
DEFAULT_BOOTSTRAP_SEED = 20261027
FALLBACK_REASONS = ("timedOut", "rejected", "unavailable", "busy", "tokenLimit", "transport", "invalidResponse")


def _round(x: float | None) -> float | None:
    return None if x is None else round(x, 6)


def mean_and_se_binary(values: Sequence[bool]) -> tuple[float | None, float | None, int]:
    n = len(values)
    if n == 0:
        return None, None, 0
    p = sum(1 for v in values if v) / n
    return p, math.sqrt(p * (1.0 - p) / n), n


def mean_and_se_rate(values: Sequence[float]) -> tuple[float | None, float | None, int]:
    n = len(values)
    if n == 0:
        return None, None, 0
    mean = sum(values) / n
    if n == 1:
        return mean, None, n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return mean, math.sqrt(var / n), n


def percentile_nearest_rank(sorted_values: Sequence[float], pct: float) -> float:
    """Nearest-rank percentile on an ascending sequence (deterministic, no interpolation)."""
    n = len(sorted_values)
    if n == 0:
        raise ValueError("empty")
    rank = max(1, math.ceil(pct / 100.0 * n))
    return sorted_values[min(rank, n) - 1]


def bootstrap_f(
    counts: Sequence[tuple[int, int, int]], *, resamples: int, seed: int
) -> dict[str, Any]:
    """Paired bootstrap of the pooled F0.5 over items. Returns the interval and how many resamples were defined."""
    n = len(counts)
    if n == 0 or resamples <= 0:
        return {"low": None, "high": None, "defined_resamples": 0, "resamples": resamples}
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(resamples):
        tp = fp = fn = 0
        for _ in range(n):
            a, b, c = counts[rng.randrange(n)]
            tp += a
            fp += b
            fn += c
        p, r = precision_recall(tp, fp, fn)
        f = f_beta(p, r)
        if f is not None:
            values.append(f)
    if not values:
        return {"low": None, "high": None, "defined_resamples": 0, "resamples": resamples}
    values.sort()
    return {
        "low": _round(percentile_nearest_rank(values, 2.5)),
        "high": _round(percentile_nearest_rank(values, 97.5)),
        "defined_resamples": len(values),
        "resamples": resamples,
    }


def aggregate_category(
    scores: Sequence[ItemScore],
    *,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    bootstrap_seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Aggregate the ItemScores of one category into the leaderboard columns."""
    n_total = len(scores)
    valid = [s for s in scores if s.valid]
    invalid = [s for s in scores if not s.valid]
    tp = sum(s.tp for s in valid)
    fp = sum(s.fp for s in valid)
    fn = sum(s.fn for s in valid)
    p, r = precision_recall(tp, fp, fn)
    f = f_beta(p, r)
    em, em_se, _ = mean_and_se_binary([s.exact_match for s in valid])
    wl, wl_se, _ = mean_and_se_rate([s.word_loss for s in valid])
    ins, ins_se, _ = mean_and_se_rate([s.insertion for s in valid])
    slot_values = [s.slot_fail for s in valid if s.slot_fail is not None]
    sf, sf_se, sf_n = mean_and_se_binary(slot_values)
    noop_values = [s.over_clean for s in valid if s.noop and s.over_clean is not None]
    oc, oc_se, oc_n = mean_and_se_binary(noop_values)
    status_counts = Counter(s.status for s in scores)
    reason_counts = Counter(s.fallback_reason for s in scores if s.status == "fallback")
    latencies = sorted(s.latency_ms for s in scores if s.latency_ms is not None)
    return {
        "n": n_total,
        "n_valid": len(valid),
        "edit": {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": _round(p),
            "recall": _round(r),
            "f0_5": _round(f),
            "f0_5_bootstrap_95": bootstrap_f(
                [(s.tp, s.fp, s.fn) for s in valid], resamples=bootstrap_resamples, seed=bootstrap_seed
            ),
        },
        "exact_match": {"mean": _round(em), "se": _round(em_se), "n": len(valid)},
        "word_loss": {"mean": _round(wl), "se": _round(wl_se), "n": len(valid)},
        "insertion": {"mean": _round(ins), "se": _round(ins_se), "n": len(valid)},
        "slot_fail": {"mean": _round(sf), "se": _round(sf_se), "n": sf_n},
        "over_clean": {"mean": _round(oc), "se": _round(oc_se), "n": oc_n},
        "status": {
            "cleaned": status_counts.get("cleaned", 0),
            "unchanged": status_counts.get("unchanged", 0),
            "fallback": status_counts.get("fallback", 0),
            "empty": status_counts.get("empty", 0),
            "invalid": len(invalid),
            "fallback_reasons": {k: reason_counts.get(k, 0) for k in FALLBACK_REASONS if reason_counts.get(k, 0)},
            "invalid_reasons": sorted({s.invalid_reason or "" for s in invalid}),
        },
        "latency_ms": {
            "n": len(latencies),
            "p50": _round(percentile_nearest_rank(latencies, 50)) if latencies else None,
            "p95": _round(percentile_nearest_rank(latencies, 95)) if latencies else None,
        },
    }


def aggregate_latency(scores: Sequence[ItemScore]) -> dict[str, Any]:
    latencies = sorted(s.latency_ms for s in scores if s.latency_ms is not None)
    return {
        "n": len(latencies),
        "p50": _round(percentile_nearest_rank(latencies, 50)) if latencies else None,
        "p95": _round(percentile_nearest_rank(latencies, 95)) if latencies else None,
    }
