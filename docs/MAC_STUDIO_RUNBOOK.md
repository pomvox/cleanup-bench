# Mac Studio runbook: the v1 baseline rows

Paste this file to Claude Code on the Mac Studio. It produces the baseline
rows of `docs/spec.md` section 8 with the adapters from phase 3, in order,
and stops before anything leaves the machine other than a git push of run
folders to this repository on a branch.

Rules that apply throughout:

- No secret is ever written to a file. `HF_TOKEN`, `POMVOX_LOCALSERVER_TOKEN`
  and `ANTHROPIC_API_KEY` live in the shell session only (`export` at the
  prompt or a shell profile that is not in any repository). The adapters read
  them by name; the manifests record the variable name, never the value.
- No number goes into any document unless a command in this repository
  produced it or a cited page states it.
- A disagreement between the two SimpleWords rows is filed as an issue in the
  engine repository. Nothing in the engine or the app repositories is changed
  from this session, and the bench is not patched to hide a disagreement.
- Our model's losses stay on the board.
- Stop and ask the owner before any tag, GitHub Pages deploy, Hugging Face
  upload or post.

## 0. Prerequisites

- Xcode installed (the LocalServer build needs an Xcode build: mlx-swift's
  Metal library is an Xcode build phase), plus `xcodegen`.
- `uv` installed.
- `llama-server` from llama.cpp on `PATH` (Homebrew `llama.cpp` or a local
  build).
- A Hugging Face account that has accepted the gate on
  `ReFyneLabs/simplewords-dictation-cleanup-v3`, logged in with the token in
  `HF_TOKEN`.
- The engine repository checked out next to this one with the pinned
  SimpleWords pack in `.local/simplewords-v3` and the diarizer pack in
  `.local/pyannote-community1-coreml` (see `Examples/LocalServer/README.md`
  in the engine repository).
- Environment variables set in the shell, never in files:

```sh
export HF_TOKEN=...                    # Hugging Face, gated download
export POMVOX_LOCALSERVER_TOKEN=...    # captured from the LocalServer's start-up output (step 3)
export ANTHROPIC_API_KEY=...           # the hosted generic-cloud row
```

Check them without printing values:

```sh
for v in HF_TOKEN POMVOX_LOCALSERVER_TOKEN ANTHROPIC_API_KEY; do printf '%s: %s\n' "$v" "${(P)v:+set}"; done
```

(`ANTHROPIC_API_KEY` and `POMVOX_LOCALSERVER_TOKEN` can be set later, right
before the step that needs them.)

## 1. Clone and install

```sh
git clone git@github.com:pomvox/cleanup-bench.git
cd cleanup-bench
# Start from the newest build branch that has been merged, or from build/05-site
# if the stacked build PRs are still open (research/part-1 <- spec/v1 <- build/01..05).
git checkout build/05-site
uv sync --group dev --extra mlx
uv run pytest
uv run ruff check .
```

Both must be clean before any row is produced. Note the date; every run
folder below is `runs/<system>/<date>/` and the branch is `runs/<date>`:

```sh
export RUN_DATE=$(date -u +%F)
git checkout -b "runs/$RUN_DATE"   # branched from the checkout above
```

## 2. Build and start the Pomvox LocalServer (engine repository)

From the engine repository checkout, exactly as its
`Examples/LocalServer/README.md` says:

```sh
cd ../pomvox-cleanup-engine
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
xcodegen generate --spec Examples/LocalServer/project.yml
xcodebuild -project Examples/LocalServer/LocalServer.xcodeproj -scheme LocalServer \
  -configuration Release -derivedDataPath /tmp/pomvox-local-server \
  -destination 'platform=macOS,arch=arm64' build

/tmp/pomvox-local-server/Build/Products/Release/LocalServer \
  "$PWD/.local/simplewords-v3" "$PWD/.local/pyannote-community1-coreml" --port 8787 --no-stt
```

The server prints its bearer token at start. Copy it into the shell of the
bench session (`export POMVOX_LOCALSERVER_TOKEN=...`); do not paste it into
any file or commit message. Leave the server running in its own terminal.

Confirm the served pack is the pinned one before running anything:

```sh
curl -s http://127.0.0.1:8787/v1/status
```

`cleanupPack` must be `simplewords-v3` and `cleanupPackVersion`
`0.1.0-preview`, matching `configs/adapter-simplewords-v3-engine.json`. The
adapter's `open()` refuses any other pack.

## 3. Row: SimpleWords v3 via the engine

```sh
cd ../cleanup-bench
uv run cleanupbench run --adapter pomvox-localserver \
  --config configs/run-simplewords-v3-engine.json \
  --adapter-config configs/adapter-simplewords-v3-engine.json \
  --organizer-row --date "$RUN_DATE"
```

`run` performs two passes and prints `determinism identical` or `DIFFERS`.
Read section 10 if it differs. The run folder is
`runs/simplewords-v3-engine/$RUN_DATE/`.

## 4. Row: SimpleWords v3 via mlx-lm

The adapter downloads the snapshot with the same `allow_patterns` filter the
app's eval script uses (an unfiltered snapshot pulls adapter safetensors into
the shared cache and breaks the app's loader; see the comment in
`src/cleanupbench/adapters/mlx_lm.py`). `HF_TOKEN` must be set.

```sh
uv run cleanupbench run --adapter mlx-lm \
  --config configs/run-simplewords-v3-mlx.json \
  --adapter-config configs/adapter-simplewords-v3-mlx.json \
  --organizer-row --date "$RUN_DATE"
```

The manifest records the snapshot commit as `model_revision` and the sha256
over the `model*.safetensors` files as `weights_sha256`.

## 5. The byte-for-byte check between the two SimpleWords rows

```sh
uv run cleanupbench compare-rows \
  "runs/simplewords-v3-engine/$RUN_DATE" "runs/simplewords-v3-mlx/$RUN_DATE" \
  --issue-draft docs/issues/engine-mlx-disagreement.md
```

Exit code 0 means every item where the engine returned `cleaned` has a
byte-identical output in the mlx-lm row. Exit code 1 means a disagreement:
the command writes the issue draft. The rule (`docs/spec.md` section 8,
`docs/PROMPT.md` Part 3): the disagreement is **filed as an issue in the
engine repository** using the draft, with both run folders committed as they
are. It is never patched here, and neither row is re-run to make it go away.
Commit the draft with the run folders so the PR carries it.

## 6. Row: S1-mini by Superwhisper (decision 12)

### 6a. Fetch the exact system prompt

Open https://huggingface.co/superwhisper/s1-mini in a browser. Copy the system
prompt from the model card **verbatim** into `prompts/s1-mini-system.txt`
(no trailing edits, no added control line; the adapter appends the control
line). Then record in `prompts/README.md`, under the S1-mini heading, the
card URL and today's date as the date it was copied. Also check the NOTICE
terms in https://huggingface.co/superwhisper/s1-mini-GGUF and note in the
same README entry whether they add anything beyond the naming clause.

### 6b. Start llama-server

In a second terminal, from the GGUF repo's own instructions:

```sh
llama-server -hf superwhisper/s1-mini-GGUF:Q4_K_M --jinja \
  --chat-template-kwargs '{"enable_thinking":false}' --temp 0 --port 8080
```

Wait until it reports the model loaded. `configs/adapter-s1-mini.json`
points at `http://127.0.0.1:8080/v1` with `model` `s1-mini`; if the server
reports a different model id in `GET /v1/models`, set `model` in the adapter
config to the id it reports (that string is only a routing key on
`llama-server`).

### 6c. Run the row

```sh
uv run cleanupbench run --adapter openai-compatible \
  --config configs/run-s1-mini.json \
  --adapter-config configs/adapter-s1-mini.json \
  --organizer-row --date "$RUN_DATE"
```

The manifest records the prompt text and hash, the control line
`[Styling: semi-formal] [Structure: prose] [Context: general]`, and
`thinking: false`. Everywhere the row is printed it is "S1-mini" by
"Superwhisper" (naming clause; `configs/run-s1-mini.json` `display_name`).

Stop llama-server before the next step (Ctrl-C in its terminal).

## 7. Row: generic prompt, local open-weight model

The owner picks the model. Pick an open-weight instruction-tuned model that
`llama-server` or `mlx_lm.server` can serve, record its Hugging Face id,
revision, license and parameter count from its model card, and before the
run edit:

- `configs/adapter-generic-local.json`: `model`, `model_revision`,
  `license`, `params_total` (or `null` plus `params_total_note`), and
  `base_url` if the server is not on port 8080. If the model has a thinking
  switch keep `extra_body.chat_template_kwargs.enable_thinking: false`;
  otherwise remove `extra_body`.
- `configs/run-generic-local.json`: `system_org` (the model's org) and
  `display_name`, replacing every `REPLACE_ME`.

Serve it with one of:

```sh
llama-server -hf <org>/<repo-GGUF>:<quant> --jinja --temp 0 --port 8080
# or
uv run --with mlx-lm mlx_lm.server --model <org>/<repo> --port 8080
```

then

```sh
uv run cleanupbench run --adapter openai-compatible \
  --config configs/run-generic-local.json \
  --adapter-config configs/adapter-generic-local.json \
  --organizer-row --date "$RUN_DATE"
```

`prompts/generic-v1.txt` is frozen; the manifest records its hash.

## 8. Row: generic prompt, hosted (Anthropic)

`ANTHROPIC_API_KEY` must be set in the shell. This is a hosted row: it goes
to the hosted table (decision 10) and may be nondeterministic (decision S4).

```sh
uv run cleanupbench run --adapter anthropic \
  --config configs/run-generic-cloud.json \
  --adapter-config configs/adapter-generic-cloud.json \
  --organizer-row --date "$RUN_DATE"
```

If the API rejects the request because of the `temperature` field, set
`"send_temperature": false` in `configs/adapter-generic-cloud.json` and
re-run; the manifest still records `temperature: 0` as the requested
decoding, and the adapter config in the manifest shows the switch.

## 9. Score, validate, report

Score every row (the identity row is already committed):

```sh
uv run cleanupbench score "runs/simplewords-v3-engine/$RUN_DATE"
uv run cleanupbench score "runs/simplewords-v3-mlx/$RUN_DATE"
uv run cleanupbench score "runs/s1-mini/$RUN_DATE"
uv run cleanupbench score "runs/generic-local/$RUN_DATE"
uv run cleanupbench score "runs/generic-cloud/$RUN_DATE"          # add --allow-nondeterministic only per section 10
uv run cleanupbench validate
uv run cleanupbench report
```

`score` refuses a row whose two passes differ, whose manifest is incomplete
or whose `outputs.jsonl` hash does not match. Do not edit a manifest by hand
to get past a refusal; section 10 says what to do instead.

## 9b. Pilot sizing and the Disfl-QA drafts (phase 4, docs/spec.md section 7)

The pilot is the identity row plus the two generic rows on the hand-written
items (decision 6). Print Miller's paired sample size per category:

```sh
uv run cleanupbench power runs/identity/2026-10-27 "runs/generic-local/$RUN_DATE" "runs/generic-cloud/$RUN_DATE" \
  --json "data/power-$RUN_DATE.json"
```

The owner picks the minimum detectable difference per metric from that
table; record the choice and the resulting n per category in
`data/README.md` (datasheet section 2). Nothing is sized until the owner
picks.

Then derive Disfl-QA candidates. Download the test split into a fresh empty
directory outside the repository (it is untrusted data), then:

```sh
mkdir -p /tmp/disflqa && cd /tmp/disflqa
curl -sL -o test.json https://raw.githubusercontent.com/google-research-datasets/Disfl-QA/main/test.json
cd - >/dev/null
uv run cleanupbench data derive-disflqa --source /tmp/disflqa/test.json \
  --per-category <N from the power table> --seed <an integer; record it in data/README.md>
uv run cleanupbench data review-sheet --reviewer <name> --out data/review/<name>.jsonl
```

Fill the sheet (see `data/review/GUIDELINE.md`), get a second reviewer's
sheet, run `cleanupbench data agreement` and `cleanupbench data promote`.
Commit the drafts, the sheets, `data/discards.jsonl` and the promoted items
on the same branch. The v1 freeze (release date stamped on every item, the
`v1.0.0` tag prepared with `git tag -s v1.0.0` and NOT pushed) waits for the
owner's confirmation of every provisional row in `docs/decisions.md`.

## 10. What to do if the two passes differ

`run` prints `DIFFERS` and the first divergent item; the manifest has
`determinism.identical: false`.

- **Hosted row (generic-cloud).** The manifest is flagged
  `nondeterministic: true` automatically. Score it with
  `cleanupbench score <run> --allow-nondeterministic`. The row appears only
  in the hosted table, marked nondeterministic (decision S4). Do not re-run
  hoping for an identical pair.
- **Local row (any other).** A local greedy run that differs is a problem to
  investigate, not to flag. In order:
  1. For `llama-server`: check it was started with `--temp 0`; check the
     thread and batch settings are fixed for the whole run (pass explicit
     `-t <threads>` and `-b <batch>` and keep them for both passes); make
     sure no other process was using the server during the run; re-run the
     row with `--date` unchanged after deleting the refused folder (a run
     folder is never overwritten; delete it only because it was refused and
     uncommitted).
  2. For `mlx-lm`: check nothing else was loading the GPU; re-run.
  3. For the LocalServer: check the server was idle (one request at a time;
     a busy call returns exact-input fallback) and that no other client was
     connected; re-run.
  4. If it still differs, keep the refused folder out of the PR, record the
     first divergent item and both outputs in the PR description, and ask
     the owner. Decision 19 notes that a direct llama-cpp binding is only
     needed if the determinism check fails at the server level; this is that
     evidence.

## 11. Commit and open the PR

One commit per run folder, conventional commits, GPG-signed, on
`runs/$RUN_DATE`:

```sh
git add "runs/simplewords-v3-engine/$RUN_DATE" && git commit -S -m "runs: add simplewords-v3-engine $RUN_DATE"
git add "runs/simplewords-v3-mlx/$RUN_DATE"    && git commit -S -m "runs: add simplewords-v3-mlx $RUN_DATE"
git add docs/issues/engine-mlx-disagreement.md && git commit -S -m "docs: issue draft for the engine/mlx-lm disagreement"   # only if written
git add prompts/s1-mini-system.txt prompts/README.md && git commit -S -m "prompts: add the S1-mini system prompt from the model card"
git add "runs/s1-mini/$RUN_DATE"               && git commit -S -m "runs: add s1-mini $RUN_DATE"
git add configs/adapter-generic-local.json configs/run-generic-local.json && git commit -S -m "configs: name the generic-local model"
git add "runs/generic-local/$RUN_DATE"         && git commit -S -m "runs: add generic-local $RUN_DATE"
git add "runs/generic-cloud/$RUN_DATE"         && git commit -S -m "runs: add generic-cloud $RUN_DATE"
git push -u origin "runs/$RUN_DATE"
gh pr create --base main --title "runs: baseline rows $RUN_DATE" --body-file - <<'EOF'
(summary per section 12)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
```

Open **one** PR. Never merge it. Never force-push. Stop here: do not tag,
do not deploy Pages, do not upload anything to Hugging Face, do not post.
Ask the owner.

Before pushing, grep the staged changes for anything that looks like a
token:

```sh
git diff --cached --stat
git grep -n -E 'sk-ant-|hf_[A-Za-z0-9]{20,}|Bearer ' -- runs configs prompts docs || echo "no secrets found"
```

## 12. What to report back

Put the following in the PR description and in the reply to the owner. Every
number comes from a command's output; cite the file it came from.

1. Per-row category table from each `scores.json`: for every category, F0.5,
   P, R, word-loss, insertion, exact-match, slot-fail, over-clean (where noop
   items exist), fallback, unchanged, empty, invalid, n. One table per row,
   row named as the manifest's `system.display_name`.
2. The determinism result of every row (`determinism.identical`), and for the
   hosted row whether it was scored with `--allow-nondeterministic`.
3. The `compare-rows` summary line for the two SimpleWords rows and, if there
   was a disagreement, the path of the issue draft and the first items from
   its table.
4. Failure analysis for our model's rows (both SimpleWords rows): list,
   verbatim from `outputs.jsonl` next to the item's `input` and reference,
   every item where SimpleWords lost a word (word-loss above zero in the
   scorer's per-item output), every item where it over-cleaned a noop item,
   every fallback with its `rejectedBy:` warning, and every empty output.
   No summary in place of the list; the losses stay on the board.
5. The S1-mini card URL and the date the prompt was copied, as recorded in
   `prompts/README.md`, and any NOTICE terms found in the GGUF repo.
6. The generic-local model chosen: id, revision, license, parameter count,
   and the server and command used to serve it.
7. Hardware block from one manifest (`hardware.machine`, `os`,
   `accelerator`, `ram_gb`) and the `software.packages` block from the
   mlx-lm manifest.
8. Anything that was refused, re-run or skipped, with the reason.
