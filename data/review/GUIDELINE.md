# Review guideline

Every candidate item is reviewed by someone who did not write it before it can
enter `data/items/` (`docs/spec.md` section 7.3; `docs/research/03-data.md`
R3). The reviewer answers three yes/no questions per item. Any "no" discards
the item; nothing is repaired.

## The three questions

1. **Consistent.** Does every reference mean what the input means? A
   reference that resolves a self-correction the wrong way, keeps a
   superseded value, or changes a fact is inconsistent. (Disfl-QA's first
   question.)
2. **Natural.** Could a person have dictated the input? Inputs that read as
   constructed puzzles rather than speech are unnatural. (Disfl-QA's second
   question.) For `adversarial-meaning` items, "natural" still applies: the
   trap must be something a speaker would actually say.
3. **Laws.** Does every reference obey the three laws? No content word the
   speaker said is missing unless it is a filler, stutter, unintentional
   repetition, reparandum or editing term (law 1); no word appears that the
   speaker did not say, except a sanctioned conversion named in `notes` or a
   vocabulary spelling (law 1); where the right cleanup is unclear, the
   reference leaves the text as said (law 3). Also check the reference
   guideline in `docs/spec.md` section 5: contractions and slang as said,
   homophones as said, fragments without a forced period, lists only when
   invited.

Also check the slots: a `must_not_contain` phrase that is legitimately
present in a correct output, or a `must_contain` phrase that a correct
output could drop, is a "no" on question 3.

## Mechanics

```sh
# one blank sheet per reviewer over everything under data/drafts/
cleanupbench data review-sheet --reviewer <name> --out data/review/<name>.jsonl
# fill in consistent / natural / laws (true or false) and an optional comment per line
cleanupbench data agreement data/review/<a>.jsonl data/review/<b>.jsonl
cleanupbench data promote data/review/<a>.jsonl data/review/<b>.jsonl --released <date>
```

`agreement` prints raw agreement and Cohen's κ per category and question, as
Disfl-QA reported; the dataset card records them. `promote` appends items
every reviewer accepted to `data/items/`, runs the generation gates once
more, and logs every rejection in `data/discards.jsonl`. Promoted lines are
removed from `data/drafts/` by hand in the same commit.

## Blind re-score before release

Before a release, a random sample per category is re-scored blind by a
reviewer who sees only input and reference (no notes, no slots), following
the label-noise finding in `docs/research/03-data.md` section 1. The sample
and the outcome go into the release notes.

## Disfl-QA-derived candidates

The derivation pre-labels each pair as `correction-interrogative` or
`correction-intra` with a heuristic (`src/cleanupbench/data/disflqa.py`).
The reviewer confirms the label; a mislabelled item is a "no" on question 3
(the category is part of what the reference claims). Pairs whose original
question changed words beyond the correction (the generation gate
`no-invention` catches most of these) are discarded, not rewritten.
