"""Power calculation (docs/spec.md section 7.2), worked by hand against Miller's formula."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from cleanupbench.power import (
    PowerError,
    format_power_table,
    paired_sample_size,
    paired_stats,
    power_table,
    z_power,
    z_two_sided,
)


def test_z_values():
    # Standard normal quantiles: z_{0.025} = 1.959963..., z_{0.80} = 0.841621...
    assert math.isclose(z_two_sided(0.05), 1.959963984540054, rel_tol=1e-9)
    assert math.isclose(z_power(0.80), 0.8416212335729143, rel_tol=1e-9)


def test_paired_sample_size_hand_worked():
    # n = (1.95996 + 0.84162)^2 * sigma^2 / delta^2 = 7.8489 * sigma^2 / delta^2
    # sigma = 0.5, delta = 0.1: 7.8489 * 0.25 / 0.01 = 196.22 -> 197
    assert paired_sample_size(0.5, 0.1, alpha=0.05, power=0.80) == 197
    # sigma = 0: one item suffices (no variance)
    assert paired_sample_size(0.0, 0.1, alpha=0.05, power=0.80) == 1
    with pytest.raises(PowerError):
        paired_sample_size(0.5, 0.0, alpha=0.05, power=0.80)


def scores_with(items: list[dict]) -> dict:
    return {"items_sha256": "a" * 64, "categories": {"fillers": {}}, "items": items}


def item(id_, **kw):
    base = {
        "id": id_,
        "category": "fillers",
        "status": "cleaned",
        "tp": 1,
        "fp": 0,
        "fn": 0,
        "exact_match": True,
        "word_loss": 0.0,
        "insertion": 0.0,
        "slot_fail": False,
        "over_clean": None,
    }
    base.update(kw)
    return base


def test_paired_stats_hand_worked():
    a = scores_with(
        [item("f-core-0001", word_loss=0.0), item("f-core-0002", word_loss=0.5), item("f-core-0003", word_loss=1.0)]
    )
    b = scores_with(
        [item("f-core-0001", word_loss=0.0), item("f-core-0002", word_loss=0.0), item("f-core-0003", word_loss=0.0)]
    )
    st = paired_stats(a, b, "fillers", "word_loss")
    # diffs 0, 0.5, 1.0: mean 0.5, sample sd = sqrt(((0.25 + 0 + 0.25) / 2)) = 0.5
    assert st.n_items == 3 and st.mean_diff == 0.5 and math.isclose(st.sd_diff, 0.5)
    # Items with the metric undefined on either side are skipped (over_clean None).
    st2 = paired_stats(a, b, "fillers", "over_clean")
    assert st2.n_items == 0 and st2.sd_diff is None


def test_f_item_values():
    a = scores_with([item("f-core-0001", tp=1, fp=1, fn=0), item("f-core-0002", tp=0, fp=0, fn=0)])
    b = scores_with([item("f-core-0001", tp=2, fp=0, fn=0), item("f-core-0002", tp=0, fp=0, fn=0)])
    st = paired_stats(a, b, "fillers", "f_item")
    # item 1: a has P=0.5,R=1 -> F0.5 = 1.25*0.5/(0.125+1) = 0.5556; b has F = 1; item 2 undefined both -> skipped
    assert st.n_items == 1
    assert math.isclose(st.mean_diff, 0.625 / 1.125 - 1.0)


def test_power_table_end_to_end(tmp_path: Path):
    ra = tmp_path / "runs" / "a" / "2026-10-27"
    rb = tmp_path / "runs" / "b" / "2026-10-27"
    ra.mkdir(parents=True)
    rb.mkdir(parents=True)
    a = scores_with(
        [item("f-core-0001", word_loss=0.0), item("f-core-0002", word_loss=0.5), item("f-core-0003", word_loss=1.0)]
    )
    b = scores_with(
        [item("f-core-0001", word_loss=0.0), item("f-core-0002", word_loss=0.0), item("f-core-0003", word_loss=0.0)]
    )
    (ra / "scores.json").write_text(json.dumps(a), "utf-8")
    (rb / "scores.json").write_text(json.dumps(b), "utf-8")
    table = power_table([ra, rb], deltas=[0.1], alpha=0.05, power=0.80)
    # word_loss paired sd = 0.5 -> n = 197 at delta 0.1 (as above); other metrics have sd 0 -> n = 1
    assert table["per_category_n"]["fillers"]["0.1"] == 197
    text = format_power_table(table)
    assert "fillers" in text and "197" in text
    # Different item sets are refused.
    b2 = dict(b, items_sha256="b" * 64)
    (rb / "scores.json").write_text(json.dumps(b2), "utf-8")
    with pytest.raises(PowerError, match="different item sets"):
        power_table([ra, rb], deltas=[0.1], alpha=0.05, power=0.80)
    with pytest.raises(PowerError, match="at least two"):
        power_table([ra], deltas=[0.1], alpha=0.05, power=0.80)
