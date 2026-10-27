# Cleanup Bench: continue from Part 1

You are in `pomvox/cleanup-bench`, a public repository. Part 1 of `docs/PROMPT.md` is finished: seven research reports sit under `docs/research/`, committed on branch `research/part-1`, open as PR #1 against `main`. Your job is everything after Part 1: close the research gaps that can be closed, run the decision meeting with me, write the spec, and then build in phases. The rules in `docs/PROMPT.md` all still apply; this file only tells you where we are and how to proceed from here.

## Step 0: orient (no writing yet)

1. Read `docs/PROMPT.md` in full. It is the contract. Its appendix is a working hypothesis that the research has partly overturned; do not treat it as the spec.
2. Read `docs/research/README.md`, then `docs/research/00-summary.md` in full, then the six reports. The summary's four sections matter most: "Decisions for the owner" (21 rows), "What contradicts the working hypothesis", "Conflicts with the vault, stated for the owner", and "What could not be found out".
3. Run `gh pr view 1` and `git log --all --oneline`. Confirm you are starting from the tip of `research/part-1`. If PR #1 has been merged, start from `main`.
4. Note the repository rule from `docs/PROMPT.md`: at most two open PRs at a time. PR #1 counts. Every PR you open is reviewed by me and never merged by you.

Tell me in one short message what state you found and that you are ready for Step 1. Do not summarize the research back to me; I wrote the table with you.

## Step 1: close the research gaps that can be closed (Part 1b)

`00-summary.md` ends with "What could not be found out". Some of those gaps were blocked by access on 2026-10-24 and may be reachable now; some are unreachable and stay listed. Try once more, with the same rules as Part 1 (open the primary page, record the access date, a snippet is not a source, no numbers from memory):

- Reddit threads on dictation cleanup complaints (try old.reddit.com and the JSON endpoints; if still blocked, say so).
- VoiceInk's `LICENSE.md` for the Refine model, which decides decision 13.
- Whether Wispr Flow has a developer API, and which model Willow, Typeless, Wispr Flow and Aqua use for cleanup, if any page states it.
- Kaggle's own description of its public/private split and OpenAI's SWE-bench Verified post, which decide nothing but were cited second-hand.
- A consent template for releasing one's own dictations, for decision 7.

Append the findings to the report that owns each question under a dated heading ("Addendum 2026-MM-DD"), update the "What could not be found out" list in `00-summary.md`, and commit on `research/part-1` so PR #1 carries them. Budget this at a fraction of Part 1; it is a second attempt, not a new study. Stop and tell me what changed.

## Step 2: the decision meeting (Part 2, first half)

Walk me through the 21 decisions in `00-summary.md`, but do it efficiently:

- Present them in three batches: scoring (1, 2, 14, 15, 16, 17), data and categories (3, 4, 5, 6, 7, 8, 20, 21), and systems and governance (9, 10, 11, 12, 13, 18, 19).
- For each batch, list the decision number, a one-line restatement, and your recommendation. I will answer with numbers and letters, or "all recommended", or "all recommended except N: (x) because ...".
- Where two reports disagree (decision 2, contractions in the normalizer) or where a recommendation conflicts with the vault or the engine (decisions 4, 15, 17 and the length-ratio guard), say so in one sentence each. Do not relitigate what the reports already argued.
- Decision 11 (Hugging Face gating) and decision 17 (fragments vs the engine guard) have consequences outside this repo. If I pick an option that needs a change in `pomvox/pomvox-cleanup-engine` or in the model card, write the issue text for me to file there; never change those repos from here.
- Record every answer, with my stated reason where I give one, in `docs/decisions.md` as a table: number, question, choice, reason, date. That file is the audit trail for the spec.

## Step 3: the spec (Part 2, second half)

Write `docs/spec.md` as `docs/PROMPT.md` Part 2 describes: task definition and input form, item schema (with the fields the research added: `input_form`, `released`, per-item `source` type and license), category list with the mapping from the vault's private letters, metric definitions with formulas and provenance (including the edit-accountability metric and the human-ceiling row the research added, and the empty-output rule from decision 14), data sources and sizes (pilot plus power calculation, not fixed numbers), baselines, run manifest fields (including organizer-provenance, attestation and expiry), leaderboard columns, governance (dispute process, external reviewer, retire-never-edit, `ERRATA.md`, conflict-of-interest statement), licenses and attribution wording. Every choice cites the research file and section that supports it and the row in `docs/decisions.md` that chose it.

Also write the one-page `GOVERNANCE.md` at the repo root that the spec refers to, and a `README.md` that says in ten lines what the bench is, what it is not, and that no code exists yet.

Open this as one PR on a branch `spec/v1`, based on `main` if PR #1 has merged, otherwise stacked on `research/part-1` with the PR description saying so. Stop until I approve it. If there are already two open PRs, tell me which one must merge first and stop.

## Step 4: build (Part 3)

Only after the spec PR is approved. Follow `docs/PROMPT.md` Part 3 exactly, one phase per PR, stopping after each:

1. Scaffold: `uv` project, `cleanupbench` package with `validate`, `run`, `score`, `report` entry points that do nothing yet, item and manifest JSON schemas from the spec, CI that runs schema and unit tests. No adapters, no data.
2. Scorer: every metric in the spec with pinned unit tests whose expected values are worked by hand in the test file, plus the first hand-written items (a handful per category, enough to exercise every metric). The identity baseline row, produced by the real `run` command.
3. Adapters: the interface, then identity, OpenAI-compatible (which also covers `llama-server` per decision 19), Anthropic, mlx-lm, and the Pomvox LocalServer adapter against `Examples/LocalServer` in the engine repo. The SimpleWords v3 rows through the engine and through mlx-lm must agree byte for byte wherever the engine returns `cleaned`; if they do not, that is a finding for the engine repo, filed as an issue, not patched here. The S1-mini row per decision 12 with its control line in the manifest. The determinism check: two runs, identical hashes.
4. Dataset v1: the pilot run, the power calculation, the per-category sizes it yields, generation with gates that discard and log, the Disfl-QA-derived slice with the attribution wording from decision 21, the review pass, the freeze. Owner dictations only if decision 7 chose (a) and `data/consent/OWNER_CONSENT.md` exists.
5. Site and release: the static leaderboard generated from `runs/`, `SUBMITTING.md`, the dispute issue template, release notes with our model's failure analysis, and the `v1.0.0` tag prepared but not pushed.

Before anything leaves this machine beyond a git push to this repository (GitHub Pages, a Hugging Face upload, a post, a tag), ask.

## Standing rules, restated

- Conventional commits, 72-character subject, GPG-signed, one concern per PR, review from Abhi, never merge, never delete branches.
- No number anywhere unless a command in this repo produced it or a cited page states it. No comparative claims.
- Our model's losses stay on the board.
- Never modify the engine or app repositories or the vault from this session. File issues there.
- `~/.pomvox/eval/`, `~/.pomvox/history.db` and vault speech data stay unread unless `data/consent/OWNER_CONSENT.md` exists.
- Secrets from the environment only.
- Where a finding conflicts with the vault's reasoning, say so and let me decide.

Start with Step 0.
