"""Token alignment and edit extraction (docs/spec.md section 6.2, decision S1).

A Levenshtein alignment over tokens with a reduced substitution cost for
case-only differences, followed by merging of maximal runs of non-identical
operations into edits. The same function is applied to (input, output) and to
(input, reference); an output edit is a true positive when a reference edit
has the same span and replacement.

Costs are constants here and are repeated in the unit tests so that a change
to either is visible.
"""

from __future__ import annotations

from dataclasses import dataclass

MATCH_COST = 0.0
CASE_SUBSTITUTION_COST = 0.5
SUBSTITUTION_COST = 1.0
INSERTION_COST = 1.0
DELETION_COST = 1.0


@dataclass(frozen=True, slots=True, order=True)
class Edit:
    """An edit in source-token coordinates: tokens [start, end) are replaced by `replacement`."""

    start: int
    end: int
    replacement: tuple[str, ...]

    @property
    def is_insertion(self) -> bool:
        return self.start == self.end

    @property
    def is_deletion(self) -> bool:
        return not self.replacement


def _sub_cost(a: str, b: str) -> float:
    if a == b:
        return MATCH_COST
    if a.lower() == b.lower():
        return CASE_SUBSTITUTION_COST
    return SUBSTITUTION_COST


def align(src: list[str], tgt: list[str]) -> list[tuple[str, int, int]]:
    """Return an alignment as a list of (op, i, j) steps.

    op is "M" (identical tokens src[i] == tgt[j]), "S" (substitute src[i] by
    tgt[j]), "D" (delete src[i]) or "I" (insert tgt[j]).

    The objective is lexicographic: minimal total cost first, then the
    largest number of exact matches, so that a tie between "substitute" and
    "delete, match, insert" resolves toward keeping the identical token. Among
    paths equal on both, the back-trace prefers substitution/match, then
    deletion, then insertion, which keeps the later copy of a repeated token.
    The tests pin all three rules.
    """
    n, m = len(src), len(tgt)
    # dp[i][j] = (cost, -matches) to align src[:i] with tgt[:j]; smaller is better.
    dp: list[list[tuple[float, int]]] = [[(0.0, 0)] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = (dp[i - 1][0][0] + DELETION_COST, 0)
    for j in range(1, m + 1):
        dp[0][j] = (dp[0][j - 1][0] + INSERTION_COST, 0)
    for i in range(1, n + 1):
        si = src[i - 1]
        row = dp[i]
        prev = dp[i - 1]
        for j in range(1, m + 1):
            c = _sub_cost(si, tgt[j - 1])
            pc, pm = prev[j - 1]
            best = (pc + c, pm - (1 if c == MATCH_COST else 0))
            dc, dm = prev[j]
            d = (dc + DELETION_COST, dm)
            if d < best:
                best = d
            ic, im = row[j - 1]
            ins = (ic + INSERTION_COST, im)
            if ins < best:
                best = ins
            row[j] = best
    steps: list[tuple[str, int, int]] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            c = _sub_cost(src[i - 1], tgt[j - 1])
            pc, pm = dp[i - 1][j - 1]
            if dp[i][j] == (pc + c, pm - (1 if c == MATCH_COST else 0)):
                steps.append(("M" if c == MATCH_COST else "S", i - 1, j - 1))
                i -= 1
                j -= 1
                continue
        if i > 0:
            dc, dm = dp[i - 1][j]
            if dp[i][j] == (dc + DELETION_COST, dm):
                steps.append(("D", i - 1, -1))
                i -= 1
                continue
        steps.append(("I", -1, j - 1))
        j -= 1
    steps.reverse()
    return steps


def extract_edits(src: list[str], tgt: list[str]) -> list[Edit]:
    """Merge maximal runs of non-match steps into edits in source coordinates."""
    edits: list[Edit] = []
    steps = align(src, tgt)
    k = 0
    src_pos = 0  # next source index not yet consumed
    while k < len(steps):
        op, i, j = steps[k]
        if op == "M":
            src_pos = i + 1
            k += 1
            continue
        start = src_pos
        end = start
        repl: list[str] = []
        while k < len(steps) and steps[k][0] != "M":
            op, i, j = steps[k]
            if op in ("S", "D"):
                end = i + 1
            if op in ("S", "I"):
                repl.append(tgt[j])
            k += 1
        edits.append(Edit(start, end, tuple(repl)))
        src_pos = end
    return edits


def edit_counts(output_edits: list[Edit], reference_edits: list[Edit]) -> tuple[int, int, int]:
    """(TP, FP, FN) by exact span-and-replacement match (section 6.2 step 4)."""
    ref = set(reference_edits)
    out = set(output_edits)
    tp = len(out & ref)
    return tp, len(out) - tp, len(ref) - tp
