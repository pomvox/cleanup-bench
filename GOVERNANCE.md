# Governance

How Cleanup Bench stays credible. One page; the mechanics are in
`SUBMITTING.md`, the reasoning in `docs/research/04-governance.md`, the
choices in `docs/decisions.md` (rows 9, 10, 18 and S4).

## Who runs what

- Anyone may submit a row. A row is a committed `runs/<system>/<date>/`
  folder: manifest, every output, scores. It is a replay, not a number.
- The scorer, not the submitter, produces the scores: CI recomputes
  `scores.json` from `outputs.jsonl` on every pull request and fails on a
  difference.
- Two runs must hash identical. Greedy decoding, one prompt per system, no
  per-category hints.
- The maintainer re-runs a random subset of items for rows that ask for a
  "checked" mark. Unchecked rows stay on the board, labelled unchecked.
- Hosted-API rows live in a separate dated table with an expiry flag and are
  never edited; a withdrawn model keeps its row with the flag set.
- Submitters attest in the manifest that they did not train on the items and
  declare any known overlap. The attestation is disclosure, not verification.

## Disputes

- An item dispute is a public issue from the `item-dispute` template: item
  id, bench version, which law or rule the item violates, the reference the
  disputant believes is wrong and why, a proposed fix, and whether the
  disputant has a row on the board.
- Two reviewers decide in public on the issue: the maintainer and the external
  reviewer named below. The decision is recorded on the issue.
- Items are retired, never edited. A retired item keeps its id and line with
  `status: retired`, is excluded from scoring in the next bench version, and
  is listed in `ERRATA.md` with date, issue link and reason. Published rows
  for earlier versions are unchanged. A replacement item may be added under a
  new id in the next version.
- A row dispute is a replay failure only: hashes do not match, the scorer
  disagrees with `scores.json`, or the manifest is incomplete. A row found
  non-reproducible is flagged with the issue linked, not deleted.
- First response within one week is the target, not a guarantee.

## Conflict of interest

Cleanup Bench is maintained by Pomvox, whose model SimpleWords appears on the
board. These rules are checkable from the repository history:

1. The bench is not named after our model and no category is defined by what
   our model does well. Categories are weighted by the user-pain evidence in
   `docs/research/06-user-pain.md`.
2. Our rows follow the same submission rule as every other row. We have no
   private test variants; every run of our system that produced a score is in
   `runs/`, including the ones that scored worse.
3. Our model's failures stay on the board. Each release's notes include a
   failure analysis of our rows.
4. Items are frozen per version. We cannot edit an item after release; we can
   only retire it through the public dispute process, which applies to us as
   to anyone, and in which our declared interest is recorded.
5. Any item-dispute decision affecting a category where our model's rank
   would change is decided by the external reviewer, not the maintainer.
6. We make no comparative claim about our model anywhere in this repository
   or its site.
7. Rows produced by the maintainer carry `system.organizer_row: true` in the
   manifest and are marked on the board.

## People

- Maintainer: Abhi Ram Salammagari (GitHub `abhiram304`), Pomvox.
- External reviewer: **not yet named**. The owner fills this line before the
  `v1.0.0` tag; until then, disputes under rule 5 above cannot be decided and
  are held open.

## Versions

The dataset follows Semantic Versioning: MAJOR when a released item is removed
or the scoring contract changes, MINOR when items are added, PATCH for
documentation. Every release is a git tag; every manifest records the item
file hash it was scored against.
