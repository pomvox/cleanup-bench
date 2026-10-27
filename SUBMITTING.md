# Submitting a row

The mechanics. The rules are in `GOVERNANCE.md`; the contract is
`docs/spec.md` section 9 (manifest and outputs) and section 10 (what the
board shows). A row is a replay, not a number: what you submit is everything
needed to recompute the scores from the outputs and to regenerate the outputs
from the system.

## 1. Fork and install

```
git clone <your fork>
cd cleanup-bench
uv sync
```

Check the item files and the committed rows before you start:

```
uv run cleanupbench validate
```

## 2. Run your system

Pick one of the five adapters, or write one.

| Adapter | What it talks to |
| --- | --- |
| `identity` | nothing; output equals input (the floor row) |
| `openai-compatible` | any server that speaks the OpenAI chat-completions API (`llama-server`, vLLM, a vendor endpoint) |
| `anthropic` | the Anthropic Messages API (a hosted row) |
| `mlx-lm` | a local model through `mlx-lm` on Apple silicon |
| `pomvox-localserver` | the Pomvox engine's local server (`POST /v1/clean`) |

If none fits, write an adapter for your system behind the interface in
`src/cleanupbench/adapters/base.py` (`Adapter`, `CleanOutput`,
`SystemDescription`) and submit it in a separate pull request before the row.
An adapter never scores, never normalizes and never applies a guard; it stores
the raw output and the scorer does the rest.

Then:

```
uv run cleanupbench run --adapter <name> --config <run-config.json> [--adapter-config <adapter-config.json>]
```

`run` scores nothing. It runs every scorable item twice, hashes both passes,
and writes `runs/<system>/<date>/run.json` and `outputs.jsonl`.

Rules that apply to every run:

- Greedy decoding (`temperature: 0`, thinking off where the model has it).
  The manifest records what was used; nothing is assumed.
- One prompt per system, fixed across all categories. No category names, no
  per-item hints, no vocabulary beyond what the item supplies. The prompt
  text and its hash are in the manifest.
- The vocabulary policy (`item` or `none`, and how the list is rendered) is
  in the manifest.
- Nothing in `runs/` is edited by hand.

## 3. The two-pass determinism rule

`run` performs two passes over the items and records both hashes in
`determinism.run_a_sha256` and `determinism.run_b_sha256`. The two passes
must hash identical (`determinism.identical: true`) for every row on the main
board. `score` refuses a row whose passes differ.

The one exception is a hosted row (section 7 below).

## 4. Score the row

```
uv run cleanupbench score runs/<system>/<date>
```

This writes `scores.json`. The scorer, not the submitter, produces the
scores: CI recomputes `scores.json` from `outputs.jsonl` on every pull
request and fails on a difference. Before opening the PR, run the same check
CI runs:

```
uv run cleanupbench score --check runs/<system>/<date>
```

## 5. What the manifest must contain

`run` fills the manifest from the adapter and your run config. `score`
refuses a manifest missing any required field. Every required field, and
what it means (`docs/spec.md` section 9):

| Field | Meaning |
| --- | --- |
| `schema_version` | the manifest schema version this file follows |
| `bench_version` | the item release the row was scored against; items are frozen per version |
| `items_sha256` | hash of the item files the row was scored against, proving which items were used |
| `system.name`, `system.org` | the system and who produced the row |
| `system.organizer_row` | `true` for rows produced by the maintainer; marked on the board |
| `system.model_id`, `system.model_revision` | the exact weights: a commit hash or content digest, not a tag |
| `system.open_weights`, `system.license` | whether the weights are public and under what license |
| `system.params_total` | the total parameter count; `null` is allowed with a reason in `system.params_total_note` |
| `system.weights_sha256` | local rows: hash of the weight file(s) |
| `system.api_model_id`, `system.api_date` | hosted rows: the provider's model identifier and the date it was called |
| `adapter.name`, `adapter.version`, `adapter.config` | the bench code path used; the config has the endpoint without secrets, model path, control line and max tokens |
| `prompt.sha256`, `prompt.text` | the frozen prompt, verifiable (empty for identity) |
| `decoding` | `strategy: greedy`, `temperature`, `max_tokens`, `thinking: false` where applicable |
| `vocabulary_policy` | `item` when the item's list is passed, `none` otherwise, and how it is rendered |
| `hardware.machine`, `hardware.os`, `hardware.accelerator`, `hardware.ram_gb` | what the row ran on; the latency table names it |
| `software.python`, `software.packages`, `software.bench_commit` | what the row ran with, for replay |
| `run.started_at`, `run.finished_at` | when; hosted rows are dated by this |
| `determinism.run_a_sha256`, `determinism.run_b_sha256`, `determinism.identical` | the two-pass evidence |
| `outputs_sha256` | ties `scores.json` to `outputs.jsonl` |
| `attestation.no_training_on_items` | boolean: the system was not trained on the items |
| `attestation.known_overlap` | text: any known overlap between the items and the system's training data |
| `attestation.declared_exposure` | `none`, `possible` or `yes` |
| `hosted` | whether the system was called through a hosted API |
| `hosted_expiry_flag` | `null` unless a hosted model is withdrawn; set by a later commit that edits no other field |
| `checked_by`, `checked_date` | `null` by default; the organizer's re-run mark |

Optional: `system.display_name` (how the row is printed), `system.gated_download`
(the weights need an account to download), `prompt.control_line`, `notes`, and
`nondeterministic` (hosted rows only, section 7).

### The attestation

The manifest carries the attestation; the pull request copies it. You attest
that the system was not trained on the items (`no_training_on_items`), you
declare any overlap you know of (`known_overlap`), and you declare the
exposure (`declared_exposure`). The attestation is disclosure, not
verification.

### Naming

Rows are printed under `system.display_name` when present, else
`system.name`. A row of Superwhisper's S1-mini must set the name so that it
prints as "S1-mini" by "Superwhisper" wherever the row appears, with that
capitalisation: the model's Apache 2.0 license carries a naming clause.

## 6. The pull request

The PR adds exactly one `runs/<system>/<date>/` folder containing `run.json`,
`outputs.jsonl` and `scores.json`, and nothing else. Model files stay out of
the repository. A PR that touches items, the scorer, the site or another row
is not a submission and is reviewed as a code change.

The PR body follows `.github/PULL_REQUEST_TEMPLATE.md`: the checklist, the
attestation statement copied from the manifest, and a link to a system
description (a model card, a README or a paper; a closed system still needs a
description of what was called and how). It contains no comparative claims:
the board has no overall score and no ranking, and neither does PR text.

CI runs `validate`, recomputes every `scores.json` and compares, and
regenerates the site. A difference fails the PR.

### The optional "checked" mark

The maintainer re-runs a random subset of items for rows that ask for it in
the PR. A row whose re-run agrees gets `checked_by` and `checked_date` set in
a commit by the maintainer and prints as checked. Rows without it stay on the
board, printed as unchecked. Hosted rows are unchecked unless re-run, because
the endpoint can change under the row.

## 7. Hosted-API rows

A row with `hosted: true` goes to the hosted table, not the main board. It
prints `api_model_id`, `api_date`, the expiry flag and the nondeterministic
flag next to the same columns as the main board. Hosted rows are never
edited; when the provider withdraws the model, a later commit sets
`hosted_expiry_flag` and nothing else, and the row stays.

The nondeterministic flag: a hosted row whose two passes differ may still be
scored when the manifest sets `nondeterministic: true` and the row is scored
with `score --allow-nondeterministic`. It is then shown only in the hosted
table, marked nondeterministic. A main-board row has no such option.

## 8. Systems invited but not runnable yet

These systems have no text-in interface the adapters can call, or no
published prompt and decoding setting that would make two passes hash
identical. Each is welcome on the board under the same rules as every other
row. What each would need:

| System | What a row would need |
| --- | --- |
| Wispr Flow | an OpenAI-compatible text-in endpoint, or a vendor-run submission under the same rules |
| Willow | an OpenAI-compatible text-in endpoint, or a vendor-run submission under the same rules |
| Typeless | an OpenAI-compatible text-in endpoint, or a vendor-run submission under the same rules |
| Aqua Voice cleanup | an OpenAI-compatible text-in endpoint, or a vendor-run submission under the same rules |
| Superwhisper S1-Language | a published prompt and greedy setting with the weights, or a vendor-run submission under the same rules |
| Monologue mono-1 | an OpenAI-compatible text-in endpoint, or a vendor-run submission under the same rules |
| Apple dictation | a text-in cleanup interface callable without audio, or a vendor-run submission under the same rules |

A vendor-run submission is a row the vendor produces with the bench's own
`run` command (or an adapter it contributes), with the full manifest, two
passes, and the attestation, submitted by the vendor as a pull request.

## 9. Disputes

A dispute about an item goes through the `item-dispute` issue template; a
dispute about a row (hashes do not match, the scorer disagrees with
`scores.json`, the manifest is incomplete, the two passes differ) goes
through the `row-dispute` template. Items are retired, never edited; a
non-reproducible row is flagged with the issue linked, not deleted. The
process and who decides are in `GOVERNANCE.md`.
