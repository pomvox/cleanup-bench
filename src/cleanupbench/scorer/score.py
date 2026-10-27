"""Scoring a run folder and the human-ceiling row (docs/spec.md sections 6, 9).

`score_run` refuses (raises ManifestError) when the manifest is incomplete,
the outputs do not match the manifest, the determinism check failed, the
item hash does not match the item directory, or the output ids do not cover
exactly the scorable items.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from cleanupbench import BENCH_VERSION
from cleanupbench.hashing import canonical_json
from cleanupbench.items import CATEGORY_ORDER, Item, items_sha256, load_items, scorable
from cleanupbench.manifest import SCORES_NAME, ManifestError, OutputRecord, check_run_dir
from cleanupbench.scorer import SCORER_VERSION
from cleanupbench.scorer.aggregate import (
    DEFAULT_BOOTSTRAP_RESAMPLES,
    DEFAULT_BOOTSTRAP_SEED,
    aggregate_category,
    aggregate_latency,
)
from cleanupbench.scorer.align import CASE_SUBSTITUTION_COST, SUBSTITUTION_COST
from cleanupbench.scorer.metrics import BETA, ItemScore, score_item


def score_records(
    items: Sequence[Item],
    records: Sequence[OutputRecord],
) -> list[ItemScore]:
    by_id = {r.id: r for r in records}
    scores: list[ItemScore] = []
    for item in items:
        rec = by_id[item.id]
        scores.append(
            score_item(
                item_id=item.id,
                category=item.category,
                slice_=item.slice,
                input_text=item.input,
                references=item.references,
                must_contain=item.must_contain,
                must_not_contain=item.must_not_contain,
                output_text=rec.output_text,
                outcome=rec.outcome,
                fallback_reason=rec.fallback_reason,
                edits=rec.edits,
                latency_ms=rec.latency_ms,
            )
        )
    return scores


def human_ceiling_scores(items: Sequence[Item]) -> list[ItemScore]:
    """Reference 2 scored as a system against reference 1, for items with two or more references."""
    scores: list[ItemScore] = []
    for item in items:
        if len(item.references) < 2:
            continue
        scores.append(
            score_item(
                item_id=item.id,
                category=item.category,
                slice_=item.slice,
                input_text=item.input,
                references=item.references[:1],
                must_contain=item.must_contain,
                must_not_contain=item.must_not_contain,
                output_text=item.references[1],
                outcome="unchanged" if item.references[1] == item.input else "cleaned",
                fallback_reason=None,
                edits=None,
                latency_ms=None,
            )
        )
    return scores


def build_scores(
    *,
    scores: Sequence[ItemScore],
    bootstrap_resamples: int,
    bootstrap_seed: int,
) -> dict[str, Any]:
    categories: dict[str, Any] = {}
    for cat in CATEGORY_ORDER:
        cat_scores = [s for s in scores if s.category == cat]
        if cat_scores:
            categories[cat] = aggregate_category(
                cat_scores, bootstrap_resamples=bootstrap_resamples, bootstrap_seed=bootstrap_seed
            )
    slices: dict[str, Any] = {}
    for s in scores:
        if s.slice:
            slices.setdefault(f"{s.category}/{s.slice}", [])
    for key in list(slices):
        cat, sl = key.split("/", 1)
        slices[key] = aggregate_category(
            [s for s in scores if s.category == cat and s.slice == sl],
            bootstrap_resamples=bootstrap_resamples,
            bootstrap_seed=bootstrap_seed,
        )
    return {
        "categories": categories,
        "slices": dict(sorted(slices.items())),
        "latency": aggregate_latency(scores),
        "items": [s.to_json() for s in sorted(scores, key=lambda s: s.id)],
    }


def parameters(bootstrap_resamples: int, bootstrap_seed: int) -> dict[str, Any]:
    return {
        "scorer_version": SCORER_VERSION,
        "beta": BETA,
        "case_substitution_cost": CASE_SUBSTITUTION_COST,
        "substitution_cost": SUBSTITUTION_COST,
        "bootstrap_resamples": bootstrap_resamples,
        "bootstrap_seed": bootstrap_seed,
    }


def score_run(
    run_dir: Path,
    items_dir: Path,
    *,
    allow_nondeterministic: bool = False,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    bootstrap_seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> dict[str, Any]:
    manifest, records = check_run_dir(run_dir, allow_nondeterministic=allow_nondeterministic)
    expected_hash = items_sha256(items_dir)
    if manifest["items_sha256"] != expected_hash:
        raise ManifestError(
            f"{run_dir}: manifest items_sha256 {manifest['items_sha256']} does not match the item files "
            f"({expected_hash}); the row was produced against a different item set"
        )
    if manifest["bench_version"] != BENCH_VERSION:
        raise ManifestError(
            f"{run_dir}: manifest bench_version {manifest['bench_version']!r} != package {BENCH_VERSION!r}"
        )
    items = scorable(load_items(items_dir))
    item_ids = {i.id for i in items}
    record_ids = {r.id for r in records}
    if item_ids != record_ids:
        missing = sorted(item_ids - record_ids)
        extra = sorted(record_ids - item_ids)
        raise ManifestError(
            f"{run_dir}: outputs do not cover exactly the scorable items; "
            f"missing={missing[:5]}{'...' if len(missing) > 5 else ''} "
            f"extra={extra[:5]}{'...' if len(extra) > 5 else ''}"
        )
    scores = score_records(items, records)
    body = build_scores(scores=scores, bootstrap_resamples=bootstrap_resamples, bootstrap_seed=bootstrap_seed)
    return {
        "schema_version": 1,
        "bench_version": manifest["bench_version"],
        "items_sha256": manifest["items_sha256"],
        "system": manifest["system"]["name"],
        "run_dir": run_dir.as_posix(),
        "parameters": parameters(bootstrap_resamples, bootstrap_seed),
        **body,
    }


def human_ceiling(
    items_dir: Path,
    *,
    bootstrap_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    bootstrap_seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> dict[str, Any]:
    items = scorable(load_items(items_dir))
    scores = human_ceiling_scores(items)
    body = build_scores(scores=scores, bootstrap_resamples=bootstrap_resamples, bootstrap_seed=bootstrap_seed)
    return {
        "schema_version": 1,
        "bench_version": BENCH_VERSION,
        "items_sha256": items_sha256(items_dir),
        "system": "human-ceiling",
        "run_dir": None,
        "parameters": parameters(bootstrap_resamples, bootstrap_seed),
        "items_with_two_references": len(scores),
        **body,
    }


def scores_text(scores: dict[str, Any]) -> str:
    """Deterministic serialization: sorted keys, two-space indent, trailing newline."""
    return json.dumps(scores, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_scores(run_dir: Path, scores: dict[str, Any]) -> Path:
    path = run_dir / SCORES_NAME
    path.write_text(scores_text(scores), "utf-8")
    return path


def scores_match(run_dir: Path, scores: dict[str, Any]) -> tuple[bool, str]:
    """Compare freshly computed scores with the committed scores.json (CI's check)."""
    path = run_dir / SCORES_NAME
    if not path.is_file():
        return False, f"{path}: missing scores.json"
    try:
        stored = json.loads(path.read_text("utf-8"))
    except json.JSONDecodeError as exc:
        return False, f"{path}: invalid JSON: {exc}"
    if canonical_json(stored) == canonical_json(scores):
        return True, "scores.json matches"
    return False, f"{path}: stored scores differ from recomputed scores"
