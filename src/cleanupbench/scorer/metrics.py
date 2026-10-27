"""Per-item metrics (docs/spec.md sections 6.2 to 6.9).

Each function takes plain strings so that the unit tests can state expected
values worked by hand. `score_item` combines them into one ItemScore.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from cleanupbench.scorer.align import Edit, edit_counts, extract_edits
from cleanupbench.scorer.edits import check_edits
from cleanupbench.scorer.text import (
    content_tokens,
    is_empty_output,
    minimal_normalize,
    phrase_present,
    token_texts,
)

BETA = 0.5
"""F-beta weight: precision counts twice as much as recall (CoNLL-2014; decision 1)."""


def f_beta(precision: float | None, recall: float | None, beta: float = BETA) -> float | None:
    if precision is None or recall is None:
        return None
    if precision == 0.0 and recall == 0.0:
        return 0.0
    b2 = beta * beta
    return (1.0 + b2) * precision * recall / (b2 * precision + recall)


def precision_recall(tp: int, fp: int, fn: int) -> tuple[float | None, float | None]:
    p = tp / (tp + fp) if (tp + fp) > 0 else None
    r = tp / (tp + fn) if (tp + fn) > 0 else None
    return p, r


# --- metric 1: edits ------------------------------------------------------------


def reference_edits(input_text: str, reference: str) -> list[Edit]:
    return extract_edits(token_texts(input_text), token_texts(reference))


def output_edits(input_text: str, output_text: str) -> list[Edit]:
    return extract_edits(token_texts(input_text), token_texts(output_text))


def best_edit_counts(input_text: str, output_text: str, references: Sequence[str]) -> tuple[int, int, int, int]:
    """(TP, FP, FN, reference index) for the reference that maximizes the item's F0.5.

    Ties, and the all-null case (no output edits), fall to the reference with
    the fewest false negatives, then the lowest index.
    """
    out = output_edits(input_text, output_text)
    best: tuple[int, int, int, int] | None = None
    best_key: tuple[float, int, int] | None = None
    for idx, ref in enumerate(references):
        tp, fp, fn = edit_counts(out, reference_edits(input_text, ref))
        p, r = precision_recall(tp, fp, fn)
        f = f_beta(p, r)
        key = (f if f is not None else -1.0, -fn, -idx)
        if best_key is None or key > best_key:
            best_key = key
            best = (tp, fp, fn, idx)
    assert best is not None
    return best


# --- metric 2: normalized exact match ----------------------------------------------


def exact_match(output_text: str, references: Sequence[str]) -> bool:
    out = minimal_normalize(output_text)
    return any(out == minimal_normalize(ref) for ref in references)


# --- metric 3: word loss ------------------------------------------------------------


def word_loss(input_text: str, output_text: str, reference: str) -> float:
    """Reference content tokens the speaker said (present in the input) that the output lacks.

    R is the multiset intersection of the reference's and the input's content
    tokens: a token the reference introduces (a digit form, a vocabulary
    spelling) is scored by metric 1, never as loss. Loss = |R - O| / |R|.
    """
    ref = Counter(content_tokens(reference)) & Counter(content_tokens(input_text))
    if not ref:
        return 0.0
    out = Counter(content_tokens(output_text))
    missing = sum((ref - out).values())
    return missing / sum(ref.values())


def best_word_loss(input_text: str, output_text: str, references: Sequence[str]) -> float:
    return min(word_loss(input_text, output_text, ref) for ref in references)


# --- metric 4: insertions ----------------------------------------------------------


def insertion_rate(input_text: str, output_text: str, references: Sequence[str]) -> float:
    out = content_tokens(output_text)
    if not out:
        return 0.0
    allowed = set(content_tokens(input_text))
    for ref in references:
        allowed.update(content_tokens(ref))
    inserted = sum(1 for tok in out if tok not in allowed)
    return inserted / len(out)


# --- metric 5: slots --------------------------------------------------------------


def slot_failure(output_text: str, must_contain: Sequence[str], must_not_contain: Sequence[str]) -> bool | None:
    """True when a slot fails, False when all pass, None when the item has no slots."""
    if not must_contain and not must_not_contain:
        return None
    for phrase in must_contain:
        if not phrase_present(phrase, output_text):
            return True
    for phrase in must_not_contain:
        if phrase_present(phrase, output_text):
            return True
    return False


# --- metric 6: noop items and over-cleaning -------------------------------------------


def is_noop_item(input_text: str, references: Sequence[str]) -> bool:
    src = content_tokens(input_text)
    return all(content_tokens(ref) == src for ref in references)


def over_cleaned(input_text: str, output_text: str) -> bool:
    return content_tokens(output_text) != content_tokens(input_text)


# --- combined -------------------------------------------------------------------


@dataclass(slots=True)
class ItemScore:
    id: str
    category: str
    slice: str | None
    outcome: str
    fallback_reason: str | None
    status: str  # cleaned | unchanged | fallback | empty | invalid | error
    invalid_reason: str | None = None
    tp: int = 0
    fp: int = 0
    fn: int = 0
    best_reference: int = 0
    exact_match: bool = False
    word_loss: float = 0.0
    insertion: float = 0.0
    slot_fail: bool | None = None
    noop: bool = False
    over_clean: bool | None = None
    latency_ms: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def valid(self) -> bool:
        return self.status != "invalid"

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "slice": self.slice,
            "outcome": self.outcome,
            "fallback_reason": self.fallback_reason,
            "status": self.status,
            "invalid_reason": self.invalid_reason,
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "best_reference": self.best_reference,
            "exact_match": self.exact_match,
            "word_loss": round(self.word_loss, 6),
            "insertion": round(self.insertion, 6),
            "slot_fail": self.slot_fail,
            "noop": self.noop,
            "over_clean": self.over_clean,
            "latency_ms": self.latency_ms,
        }


def score_item(
    *,
    item_id: str,
    category: str,
    slice_: str | None,
    input_text: str,
    references: Sequence[str],
    must_contain: Sequence[str],
    must_not_contain: Sequence[str],
    output_text: str,
    outcome: str,
    fallback_reason: str | None,
    edits: Sequence[dict[str, Any]] | None,
    latency_ms: float | None,
) -> ItemScore:
    """Score one item. Invalid rows (metric 8) carry no other scores."""
    score = ItemScore(
        id=item_id,
        category=category,
        slice=slice_,
        outcome=outcome,
        fallback_reason=fallback_reason,
        status=outcome,
        latency_ms=latency_ms,
    )
    if outcome == "error":
        score.status = "invalid"
        score.invalid_reason = "adapter error"
        return score
    if edits is not None:
        reason = check_edits(input_text, output_text, list(edits))
        if reason is not None:
            score.status = "invalid"
            score.invalid_reason = reason
            return score
    if outcome == "fallback" and output_text != input_text:
        score.status = "invalid"
        score.invalid_reason = "fallback output is not the exact input"
        return score
    if is_empty_output(output_text):
        score.status = "empty"
    tp, fp, fn, idx = best_edit_counts(input_text, output_text, references)
    score.tp, score.fp, score.fn, score.best_reference = tp, fp, fn, idx
    score.exact_match = exact_match(output_text, references)
    score.word_loss = best_word_loss(input_text, output_text, references)
    score.insertion = insertion_rate(input_text, output_text, references)
    score.slot_fail = slot_failure(output_text, must_contain, must_not_contain)
    score.noop = is_noop_item(input_text, references)
    score.over_clean = over_cleaned(input_text, output_text) if score.noop else None
    return score
