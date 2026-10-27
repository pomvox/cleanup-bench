"""Sizing categories from a pilot (docs/spec.md section 7.2; docs/research/03-data.md section 6).

Miller (2024), "Adding Error Bars to Evals", gives the paired sample size for
detecting a difference δ between two systems scored on the same items:

    n = (z_{α/2} + z_β)^2 · σ_paired^2 / δ^2

where σ_paired^2 is the variance of the per-item paired differences. With
greedy decoding there is no answer-sampling variance, so the per-question
resampling terms of Miller's fuller formula vanish and only the item variance
remains. Nothing here chooses δ: the owner does (decision 6), and the dataset
card records the choice.

Everything is computed from scores.json files produced in this repository;
no number is assumed.
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist
from typing import Any

from cleanupbench.items import CATEGORY_ORDER
from cleanupbench.manifest import SCORES_NAME

PER_ITEM_METRICS: tuple[str, ...] = ("exact_match", "word_loss", "insertion", "slot_fail", "over_clean", "f_item")
"""Per-item quantities a paired difference can be formed on.

`f_item` is the item-level F0.5 (0 when undefined with any edit present, skipped when no edits on either side)."""


class PowerError(ValueError):
    pass


def z_two_sided(alpha: float) -> float:
    return NormalDist().inv_cdf(1.0 - alpha / 2.0)


def z_power(power: float) -> float:
    return NormalDist().inv_cdf(power)


def paired_sample_size(sigma_paired: float, delta: float, *, alpha: float, power: float) -> int:
    """Miller's n for a paired comparison; ceiling of the real-valued formula."""
    if delta <= 0:
        raise PowerError("delta must be positive")
    if sigma_paired == 0.0:
        return 1
    z = z_two_sided(alpha) + z_power(power)
    return math.ceil((z * z) * (sigma_paired * sigma_paired) / (delta * delta))


def _item_value(item: dict[str, Any], metric: str) -> float | None:
    if item["status"] == "invalid":
        return None
    if metric == "f_item":
        tp, fp, fn = item["tp"], item["fp"], item["fn"]
        if tp + fp + fn == 0:
            return None
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        if p == 0.0 and r == 0.0:
            return 0.0
        return 1.25 * p * r / (0.25 * p + r)
    v = item.get(metric)
    if v is None:
        return None
    return float(v)


@dataclass(frozen=True, slots=True)
class PairedStats:
    category: str
    metric: str
    n_items: int
    mean_diff: float | None
    sd_diff: float | None


def paired_stats(scores_a: dict[str, Any], scores_b: dict[str, Any], category: str, metric: str) -> PairedStats:
    a = {i["id"]: i for i in scores_a["items"] if i["category"] == category}
    b = {i["id"]: i for i in scores_b["items"] if i["category"] == category}
    diffs: list[float] = []
    for id_, ia in a.items():
        ib = b.get(id_)
        if ib is None:
            continue
        va = _item_value(ia, metric)
        vb = _item_value(ib, metric)
        if va is None or vb is None:
            continue
        diffs.append(va - vb)
    n = len(diffs)
    if n == 0:
        return PairedStats(category, metric, 0, None, None)
    mean = sum(diffs) / n
    if n == 1:
        return PairedStats(category, metric, 1, mean, None)
    var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
    return PairedStats(category, metric, n, mean, math.sqrt(var))


def load_scores(run_dir: Path) -> dict[str, Any]:
    path = run_dir / SCORES_NAME
    if not path.is_file():
        raise PowerError(f"{path}: missing scores.json (run `cleanupbench score` first)")
    return json.loads(path.read_text("utf-8"))


def power_table(
    run_dirs: Sequence[Path],
    *,
    deltas: Sequence[float],
    alpha: float,
    power: float,
    metrics: Sequence[str] = PER_ITEM_METRICS,
) -> dict[str, Any]:
    """For every pair of pilot rows, category and metric: the paired SD and the n per δ.

    The conservative size for a category is the largest n over all pairs and
    metrics the owner cares about; the table reports everything so that the
    choice is visible.
    """
    if len(run_dirs) < 2:
        raise PowerError("a pilot needs at least two rows to form paired differences")
    scores = [(d, load_scores(d)) for d in run_dirs]
    hashes = {s["items_sha256"] for _, s in scores}
    if len(hashes) != 1:
        raise PowerError("pilot rows were scored against different item sets; rerun them on one item set")
    pairs: list[dict[str, Any]] = []
    categories = [c for c in CATEGORY_ORDER if any(c in s["categories"] for _, s in scores)]
    for i in range(len(scores)):
        for j in range(i + 1, len(scores)):
            (da, sa), (db, sb) = scores[i], scores[j]
            for cat in categories:
                for metric in metrics:
                    st = paired_stats(sa, sb, cat, metric)
                    row: dict[str, Any] = {
                        "row_a": da.as_posix(),
                        "row_b": db.as_posix(),
                        "category": cat,
                        "metric": metric,
                        "n_items": st.n_items,
                        "mean_diff": None if st.mean_diff is None else round(st.mean_diff, 6),
                        "sd_diff": None if st.sd_diff is None else round(st.sd_diff, 6),
                        "n_for_delta": {},
                    }
                    if st.sd_diff is not None:
                        row["n_for_delta"] = {
                            str(d): paired_sample_size(st.sd_diff, d, alpha=alpha, power=power) for d in deltas
                        }
                    pairs.append(row)
    # Conservative per-category n: max over pairs and metrics, per delta.
    per_category: dict[str, dict[str, int | None]] = {}
    for cat in categories:
        per_category[cat] = {}
        for d in deltas:
            ns = [p["n_for_delta"].get(str(d)) for p in pairs if p["category"] == cat and p["n_for_delta"]]
            per_category[cat][str(d)] = max(ns) if ns else None
    return {
        "alpha": alpha,
        "power": power,
        "deltas": [float(d) for d in deltas],
        "items_sha256": next(iter(hashes)),
        "rows": [d.as_posix() for d in run_dirs],
        "pairs": pairs,
        "per_category_n": per_category,
        "note": (
            "n is Miller's paired sample size per category; the owner picks the minimum detectable difference "
            "per metric (decision 6) and the dataset card records the resulting n."
        ),
    }


def format_power_table(table: dict[str, Any]) -> str:
    lines = [
        f"alpha={table['alpha']} power={table['power']} rows={len(table['rows'])} "
        f"items_sha256={table['items_sha256'][:12]}",
        "",
        "conservative n per category (max over pilot pairs and metrics):",
    ]
    deltas = [str(d) for d in table["deltas"]]
    lines.append("  category".ljust(28) + "".join(f"δ={d:>8}" for d in deltas))
    for cat, ns in table["per_category_n"].items():
        cells = "".join(f"{'—' if ns[d] is None else ns[d]:>10}" for d in deltas)
        lines.append(f"  {cat}".ljust(28) + cells)
    lines.append("")
    lines.append("paired SD per pair, category and metric (None where no item had the metric defined on both rows):")
    for p in table["pairs"]:
        lines.append(
            f"  {p['category']:<26} {p['metric']:<12} n={p['n_items']:<4} mean_diff={p['mean_diff']} sd={p['sd_diff']}"
        )
    return "\n".join(lines) + "\n"


DEFAULT_DELTAS: tuple[float, ...] = (0.05, 0.10, 0.20)
"""Differences shown when the owner has not chosen one yet; the owner's choice is recorded in the card."""


def register_commands(sub) -> None:  # type: ignore[no-untyped-def]
    import argparse
    import sys

    def cmd_power(args: argparse.Namespace) -> int:
        deltas = args.delta or list(DEFAULT_DELTAS)
        try:
            table = power_table(args.run_dirs, deltas=deltas, alpha=args.alpha, power=args.power)
        except PowerError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps(table, indent=2, sort_keys=True) + "\n", "utf-8")
            print(f"wrote {args.json}")
        print(format_power_table(table), end="")
        return 0

    p = sub.add_parser("power", help="paired power calculation from pilot rows (spec section 7.2)")
    p.add_argument("run_dirs", type=Path, nargs="+", help="two or more scored run folders from the pilot")
    p.add_argument("--delta", type=float, action="append", default=None, help="minimum detectable difference (repeat)")
    p.add_argument("--alpha", type=float, default=0.05, help="two-sided significance level (Miller: 0.05)")
    p.add_argument("--power", type=float, default=0.80, help="statistical power (Miller: 80 percent)")
    p.add_argument("--json", type=Path, default=None, help="also write the full table as JSON")
    p.set_defaults(func=cmd_power)
