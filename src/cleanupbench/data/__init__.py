"""Dataset tooling (docs/spec.md section 7): derivation, generation gates, review, promotion.

Nothing here edits a released item. Candidates live under `data/drafts/`,
failures go to `data/discards.jsonl`, and only reviewed items reach
`data/items/` through `promote`.
"""
