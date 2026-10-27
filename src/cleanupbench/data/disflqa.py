"""Deriving candidate items from Disfl-QA (docs/spec.md sections 7.1, 12; docs/research/03-data.md R1).

Disfl-QA (Gupta, Xu, Upadhyay, Yang and Faruqui, Findings of ACL-IJCNLP
2021) maps a SQuAD-v2 id to `original` (the fluent question) and `disfluent`
(an expert-written disfluent version). For cleanup, the disfluent text
lower-cased and de-punctuated is the input and the original is the single
reference. The repository ships no per-item category, so this module
pre-labels each pair with a heuristic that a reviewer confirms or rejects:

- `correction-interrogative`: the disfluent question opens with an
  interrogative phrase that differs from the original's, and the original's
  phrase appears later (the speaker restarted the question).
- `correction-intra`: otherwise, a same-sentence slot correction (entity,
  adverb or adjective, entity type).
- `negatives/already-clean`: the original question itself, lower-cased and
  de-punctuated, with the original as reference.

Candidates are drafts: they go to `data/drafts/` and reach `data/items/`
only through review and `promote`. The attribution wording is decision 21.
"""

from __future__ import annotations

import json
import random
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from cleanupbench.scorer.text import content_tokens, minimal_normalize

ATTRIBUTION = (
    "Derived from Disfl-QA (Gupta, Xu, Upadhyay, Yang and Faruqui, Findings of ACL-IJCNLP 2021), "
    "CC BY 4.0 as asserted in the repository README and Hugging Face dataset card; the repository has no "
    "LICENSE file and was archived on 2026-04-19. Inputs lower-cased and de-punctuated by Cleanup Bench; "
    "the original question is the reference."
)

EDITING_TERMS: frozenset[str] = frozenset(
    {
        "no",
        "wait",
        "sorry",
        "i",
        "mean",
        "rather",
        "or",
        "actually",
        "er",
        "uh",
        "um",
        "umm",
        "scratch",
        "that",
        "oops",
        "instead",
        "tell",
        "me",
        "oh",
        "well",
        "hmm",
        "eh",
        "ah",
        "err",
        "correction",
        "excuse",
    }
)
"""Tokens that appear in the interregnum of Disfl-QA corrections and are not reparanda on their own."""

INTERROGATIVES: tuple[str, ...] = ("what", "which", "who", "whom", "whose", "when", "where", "why", "how")

_PUNCT = re.compile(r"[^\w\s'\-]", re.UNICODE)


def to_input_form(text: str) -> str:
    """Lower-case and de-punctuate (keep in-word apostrophes and hyphens), single spaces."""
    text = minimal_normalize(text).lower()
    text = _PUNCT.sub(" ", text)
    text = re.sub(r"(?<!\w)['\-]+|['\-]+(?!\w)", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def interrogative_phrase(tokens: Sequence[str]) -> tuple[str, ...]:
    """The leading interrogative phrase: tokens up to and including the first interrogative word, at most four."""
    for i, tok in enumerate(tokens[:4]):
        if tok in INTERROGATIVES:
            return tuple(tokens[: i + 1])
    return ()


def label(original: str, disfluent: str) -> str:
    """Heuristic pre-label: `correction-interrogative` or `correction-intra`."""
    o = content_tokens(original)
    d = content_tokens(disfluent)
    op = interrogative_phrase(o)
    dp = interrogative_phrase(d)
    if op and dp and op != dp:
        # The original's interrogative phrase must reappear later in the disfluent version.
        n = len(op)
        for i in range(1, len(d) - n + 1):
            if tuple(d[i : i + n]) == op:
                return "correction-interrogative"
    if op and not dp:
        n = len(op)
        if any(tuple(d[i : i + n]) == op for i in range(1, len(d) - n + 1)):
            return "correction-interrogative"
    return "correction-intra"


def reparandum_tokens(original: str, disfluent: str) -> list[str]:
    """Content tokens of the disfluent version absent from the original, minus editing terms, in order."""
    keep = set(content_tokens(original))
    seen: set[str] = set()
    out: list[str] = []
    for tok in content_tokens(disfluent):
        if tok not in keep and tok not in EDITING_TERMS and tok not in seen:
            seen.add(tok)
            out.append(tok)
    return out


def candidate(
    squad_id: str,
    original: str,
    disfluent: str,
    *,
    category: str,
    slice_: str | None,
    seq: int,
    released: str,
) -> dict[str, Any]:
    input_text = to_input_form(disfluent if category != "negatives" else original)
    reference = minimal_normalize(original)
    must_not = reparandum_tokens(original, disfluent)[:3] if category != "negatives" else []
    item_id = f"{category}-{slice_ or 'core'}-{seq:04d}"
    notes = {
        "correction-interrogative": "Disfl-QA pair pre-labelled as an interrogative restart: the interrogative phrase "
        "itself is replaced; reviewer confirms the label and the reference.",
        "correction-intra": "Disfl-QA pair pre-labelled as a same-sentence correction (entity, adverb/adjective or "
        "entity type); reviewer confirms the label and the reference.",
        "negatives": "Disfl-QA original question as an already-clean input: only casing and punctuation change.",
    }[category]
    obj: dict[str, Any] = {"id": item_id, "category": category}
    if slice_:
        obj["slice"] = slice_
    obj.update(
        {
            "input": input_text,
            "input_form": "lowercase-unpunctuated",
            "vocabulary": [],
            "references": [reference],
            "slots": {"must_contain": [], "must_not_contain": must_not},
            "source": {
                "type": "derived",
                "method": "corpus",
                "origin": f"Disfl-QA test split, SQuAD-v2 id {squad_id}",
                "license": "CC-BY-4.0",
                "attribution": ATTRIBUTION,
            },
            "notes": notes,
            "taxonomy": ["substitution"] if category != "negatives" else [],
            "released": released,
            "status": "active",
            "scored": True,
        }
    )
    return obj


def load_disflqa(path: Path) -> dict[str, dict[str, str]]:
    data = json.loads(path.read_text("utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object mapping ids to pairs")
    for k, v in data.items():
        if not isinstance(v, dict) or "original" not in v or "disfluent" not in v:
            raise ValueError(f"{path}: entry {k!r} lacks original/disfluent")
    return data


def derive(
    data: dict[str, dict[str, str]],
    *,
    per_category: int,
    seed: int,
    released: str,
    start_seq: dict[str, int] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Deterministically sample candidates per target category.

    Ids are shuffled with the seed; the first `per_category` whose heuristic
    label matches each target are taken. Negatives are taken from pairs not
    used for the correction categories so that no input appears twice.
    """
    rng = random.Random(seed)
    ids = sorted(data)
    rng.shuffle(ids)
    start_seq = start_seq or {}
    buckets: dict[str, list[dict[str, Any]]] = {
        "correction-interrogative": [],
        "correction-intra": [],
        "negatives": [],
    }
    used: set[str] = set()
    for sid in ids:
        if all(len(b) >= per_category for b in buckets.values()):
            break
        pair = data[sid]
        cat = label(pair["original"], pair["disfluent"])
        if len(buckets[cat]) < per_category and sid not in used:
            seq = start_seq.get(cat, 0) + len(buckets[cat]) + 1
            buckets[cat].append(
                candidate(
                    sid, pair["original"], pair["disfluent"], category=cat, slice_=None, seq=seq, released=released
                )
            )
            used.add(sid)
            continue
        if len(buckets["negatives"]) < per_category and sid not in used:
            seq = start_seq.get("negatives", 0) + len(buckets["negatives"]) + 1
            buckets["negatives"].append(
                candidate(
                    sid,
                    pair["original"],
                    pair["disfluent"],
                    category="negatives",
                    slice_="already-clean",
                    seq=seq,
                    released=released,
                )
            )
            used.add(sid)
    return buckets
