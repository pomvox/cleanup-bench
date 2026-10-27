# Cleanup Bench

A public benchmark for dictation cleanup: the text-to-text layer that turns a raw speech-recognizer transcript into what the speaker meant.

It scores three things, in this order: did any content word disappear, did any word appear that nobody said, and were the edits that were made the right ones. Scores are per category and never pooled.

It is not a speech-recognition benchmark, not a measure of capture or latency, not English-plus-anything, and not named after any model. The maintainer's own model is on the board under the same rules as every other row, losses included (`GOVERNANCE.md`).

Every leaderboard row is a committed run folder that a stranger can replay with one command; two runs must hash identical.

The research that shaped it is under `docs/research/`; the specification is `docs/spec.md`; the decisions behind the specification are `docs/decisions.md`.

Status: the specification is under review. No benchmark code and no dataset exist yet.
