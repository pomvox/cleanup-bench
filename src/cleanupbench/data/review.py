"""Review sheets, agreement, and promotion of drafts into the item set (docs/spec.md section 7.3).

A review sheet is JSON Lines: one line per (item, reviewer) with three yes/no
answers (`consistent`, `natural`, `laws`) and an optional `comment`. Any "no"
discards the item. Agreement between two reviewers is reported as raw
agreement and Cohen's kappa per category, as Disfl-QA did.
"""

from __future__ import annotations

import datetime as dt
import json
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from cleanupbench.canary import CANARY
from cleanupbench.data.gates import append_discards, run_gates
from cleanupbench.items import iter_item_file

QUESTIONS: tuple[str, ...] = ("consistent", "natural", "laws")
"""Disfl-QA's two questions plus the bench's third: does the reference obey the three laws."""


def read_drafts(path: Path) -> list[dict[str, Any]]:
    return [obj for _, obj in iter_item_file(path)]


def write_item_file(path: Path, items: Sequence[dict[str, Any]], *, append: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append and path.exists() else "w"
    with path.open(mode, encoding="utf-8") as fh:
        if mode == "w":
            fh.write(f"# {CANARY}\n")
        for obj in items:
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")


def review_sheet(drafts: Sequence[dict[str, Any]], *, reviewer: str) -> list[dict[str, Any]]:
    """Blank sheet rows for one reviewer: the item text, the reference, the slots, and empty answers."""
    rows = []
    for obj in drafts:
        rows.append(
            {
                "id": obj["id"],
                "reviewer": reviewer,
                "category": obj["category"],
                "input": obj["input"],
                "references": obj["references"],
                "slots": obj["slots"],
                "notes": obj["notes"],
                "consistent": None,
                "natural": None,
                "laws": None,
                "comment": "",
            }
        )
    return rows


def read_sheet(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            obj = json.loads(line)
            for q in QUESTIONS:
                if obj.get(q) not in (True, False):
                    raise ValueError(f"{path}:{lineno}: {q!r} must be answered true or false")
            rows.append(obj)
    return rows


def verdicts(sheets: Sequence[Sequence[dict[str, Any]]]) -> dict[str, bool]:
    """Item id -> accepted (every reviewer answered yes to every question)."""
    answers: dict[str, list[bool]] = defaultdict(list)
    for sheet in sheets:
        for row in sheet:
            answers[row["id"]].append(all(bool(row[q]) for q in QUESTIONS))
    return {id_: all(v) for id_, v in answers.items()}


def cohens_kappa(a: Sequence[bool], b: Sequence[bool]) -> float | None:
    n = len(a)
    if n == 0 or len(b) != n:
        return None
    agree = sum(1 for x, y in zip(a, b, strict=True) if x == y) / n
    pa_yes = sum(a) / n
    pb_yes = sum(b) / n
    expected = pa_yes * pb_yes + (1 - pa_yes) * (1 - pb_yes)
    if expected == 1.0:
        return None
    return (agree - expected) / (1 - expected)


def agreement(sheet_a: Sequence[dict[str, Any]], sheet_b: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Raw agreement and Cohen's kappa per category and question, over items both reviewers answered."""
    by_a = {r["id"]: r for r in sheet_a}
    by_b = {r["id"]: r for r in sheet_b}
    common = sorted(set(by_a) & set(by_b))
    cats: dict[str, list[str]] = defaultdict(list)
    for id_ in common:
        cats[by_a[id_]["category"]].append(id_)
    out: dict[str, Any] = {"items_in_common": len(common), "categories": {}}
    for cat, ids in sorted(cats.items()):
        entry: dict[str, Any] = {"n": len(ids)}
        for q in QUESTIONS:
            a = [bool(by_a[i][q]) for i in ids]
            b = [bool(by_b[i][q]) for i in ids]
            raw = sum(1 for x, y in zip(a, b, strict=True) if x == y) / len(ids)
            k = cohens_kappa(a, b)
            entry[q] = {"raw_agreement": round(raw, 6), "kappa": None if k is None else round(k, 6)}
        out["categories"][cat] = entry
    return out


def _discard(obj: dict[str, Any], today: str, stage: str, problems: dict[str, list[str]]) -> dict[str, Any]:
    return {
        "id": obj["id"],
        "stage": stage,
        "date": today,
        "gates_failed": sorted(problems),
        "problems": problems,
        "source": obj.get("source"),
        "input": obj.get("input"),
        "references": obj.get("references"),
    }


def promote(
    drafts: Sequence[dict[str, Any]],
    accepted: dict[str, bool],
    *,
    items_dir: Path,
    discard_log: Path,
    released: str | None = None,
) -> tuple[list[str], list[str]]:
    """Append accepted drafts to data/items/<category>.jsonl; log rejected and gate-failing drafts.

    Returns (promoted ids, discarded ids). Ids are kept as drafted; the
    derivation assigns them with a start sequence past the existing items so
    that they do not collide, and `validate` rejects duplicates anyway.
    """
    promoted: list[str] = []
    discarded: list[str] = []
    to_write: dict[str, list[dict[str, Any]]] = defaultdict(list)
    discards: list[dict[str, Any]] = []
    today = dt.date.today().isoformat()
    for obj in drafts:
        id_ = obj["id"]
        if id_ not in accepted:
            continue  # not reviewed yet; stays a draft
        if not accepted[id_]:
            discards.append(_discard(obj, today, "review", {"review": ["a reviewer answered no"]}))
            discarded.append(id_)
            continue
        failed = run_gates(obj)
        if failed:
            discards.append(_discard(obj, today, "promote", failed))
            discarded.append(id_)
            continue
        final = dict(obj)
        if released:
            final["released"] = released
        to_write[final["category"]].append(final)
        promoted.append(id_)
    for cat, objs in to_write.items():
        write_item_file(items_dir / f"{cat}.jsonl", objs, append=True)
    if discards:
        append_discards(discard_log, discards)
    return promoted, discarded
