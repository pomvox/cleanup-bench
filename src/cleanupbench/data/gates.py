"""Generation gates that discard and log, never repair (docs/spec.md section 7.3).

Gates (all mechanical; the law gate is a human answer in review):

- `schema`: the candidate validates against the item schema and the
  consistency rules.
- `slots`: every reference satisfies the candidate's own slots.
- `no-content-loss`: every content token of the input that the reference keeps
  is... trivially true; what this gate checks is that no reference is empty
  unless the input is filler-only by the candidate's own declaration
  (`notes` contains "filler-only").
- `no-invention`: every content token of every reference appears in the
  input, except tokens the candidate declares as sanctioned conversions in
  `sanctioned_tokens` (a list the generator must supply and that the
  promotion step records in `notes`).
- `input-form`: the input matches its declared `input_form` (for
  `lowercase-unpunctuated`: no uppercase letters, no punctuation except
  apostrophes and hyphens inside words).
- `no-canary`: the canary GUID does not appear inside any text field.

A candidate that fails any gate is written to the discard log with the gate
names and is never edited into compliance.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from cleanupbench.canary import CANARY_GUID
from cleanupbench.items import validate_item_object
from cleanupbench.scorer.metrics import slot_failure
from cleanupbench.scorer.text import content_tokens

_LOWER_UNPUNCT = re.compile(r"^[a-z0-9]+(?:['\-][a-z0-9]+)*(?: [a-z0-9]+(?:['\-][a-z0-9]+)*)*$")

GATE_NAMES: tuple[str, ...] = ("schema", "slots", "no-content-loss", "no-invention", "input-form", "no-canary")


def gate_schema(candidate: dict[str, Any]) -> list[str]:
    return validate_item_object(candidate)


def gate_slots(candidate: dict[str, Any]) -> list[str]:
    slots = candidate.get("slots", {})
    must, must_not = slots.get("must_contain", []), slots.get("must_not_contain", [])
    problems = []
    for k, ref in enumerate(candidate.get("references", [])):
        if slot_failure(ref, must, must_not):
            problems.append(f"reference {k} fails the candidate's own slots")
    return problems


def gate_no_content_loss(candidate: dict[str, Any]) -> list[str]:
    problems = []
    filler_only = "filler-only" in candidate.get("notes", "")
    for k, ref in enumerate(candidate.get("references", [])):
        if not content_tokens(ref) and not filler_only:
            problems.append(f"reference {k} is empty but the notes do not declare the input filler-only")
    return problems


def gate_no_invention(candidate: dict[str, Any], sanctioned_tokens: Iterable[str] = ()) -> list[str]:
    allowed = set(content_tokens(candidate.get("input", "")))
    allowed.update(t.lower() for t in sanctioned_tokens)
    for term in candidate.get("vocabulary", []):
        allowed.update(content_tokens(term))
    problems = []
    for k, ref in enumerate(candidate.get("references", [])):
        extra = sorted({t for t in content_tokens(ref) if t not in allowed})
        if extra:
            problems.append(f"reference {k} introduces tokens not in the input or sanctioned: {extra}")
    return problems


def gate_input_form(candidate: dict[str, Any]) -> list[str]:
    form = candidate.get("input_form")
    text = candidate.get("input", "")
    if form == "lowercase-unpunctuated" and not _LOWER_UNPUNCT.match(text):
        return ["input is not lowercase-unpunctuated (only a-z, 0-9, in-word apostrophes and hyphens, single spaces)"]
    return []


def gate_no_canary(candidate: dict[str, Any]) -> list[str]:
    texts = [candidate.get("input", ""), candidate.get("notes", ""), *candidate.get("references", [])]
    return ["the canary GUID appears in a text field"] if any(CANARY_GUID in t for t in texts) else []


def run_gates(candidate: dict[str, Any], *, sanctioned_tokens: Iterable[str] = ()) -> dict[str, list[str]]:
    """Return {gate_name: [problems]} for the gates that failed (empty dict when all pass)."""
    results = {
        "schema": gate_schema(candidate),
        "slots": gate_slots(candidate),
        "no-content-loss": gate_no_content_loss(candidate),
        "no-invention": gate_no_invention(candidate, sanctioned_tokens),
        "input-form": gate_input_form(candidate),
        "no-canary": gate_no_canary(candidate),
    }
    return {k: v for k, v in results.items() if v}


def append_discards(log_path: Path, records: Sequence[dict[str, Any]]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")


def discard_record(candidate: dict[str, Any], failed: dict[str, list[str]], *, stage: str) -> dict[str, Any]:
    return {
        "id": candidate.get("id"),
        "stage": stage,
        "date": dt.date.today().isoformat(),
        "gates_failed": sorted(failed),
        "problems": failed,
        "source": candidate.get("source"),
        "input": candidate.get("input"),
        "references": candidate.get("references"),
    }


def gate_candidates(
    candidates: Sequence[dict[str, Any]],
    *,
    discard_log: Path,
    stage: str,
    sanctioned: dict[str, Sequence[str]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split candidates into (passing, discarded) and append the discards to the log."""
    passing: list[dict[str, Any]] = []
    discarded: list[dict[str, Any]] = []
    for cand in candidates:
        failed = run_gates(cand, sanctioned_tokens=(sanctioned or {}).get(cand.get("id", ""), ()))
        if failed:
            discarded.append(discard_record(cand, failed, stage=stage))
        else:
            passing.append(cand)
    if discarded:
        append_discards(discard_log, discarded)
    return passing, discarded
