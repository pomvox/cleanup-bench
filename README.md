# Cleanup Bench

A public benchmark for dictation cleanup: the text-to-text layer that turns a raw speech-recognizer transcript into what the speaker meant.

It scores three things, in this order: did any content word disappear, did any word appear that nobody said, and were the edits that were made the right ones. Scores are per category and never pooled.

It is not a speech-recognition benchmark, not a measure of capture or latency, not English-plus-anything, and not named after any model. The maintainer's own model is on the board under the same rules as every other row, losses included (`GOVERNANCE.md`).

Every leaderboard row is a committed run folder that a stranger can replay with one command; two runs must hash identical.

The research that shaped it is under `docs/research/`; the specification is `docs/spec.md`; the decisions behind the specification are `docs/decisions.md`.

Status: the specification is under review. The scorer, the schemas, the identity adapter and the first hand-written items exist (`cleanupbench validate`, `run`, `score`, `human-ceiling`); all five adapters exist with tests against fake servers (no model rows yet; `docs/MAC_STUDIO_RUNBOOK.md` produces them); the dataset tooling (power calculation, Disfl-QA derivation, gates, review, promotion) exists and the v1 freeze waits for the pilot and the owner's decisions; the static leaderboard is generated from `runs/` by `cleanupbench report` and checked by CI; `docs/MAC_STUDIO_RUNBOOK.md` produces the model rows. No `v1.0.0` tag exists yet.
