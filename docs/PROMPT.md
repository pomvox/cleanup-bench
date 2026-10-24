# Cleanup Bench: research first, then decide, then build

You are starting a new public repository, `pomvox/cleanup-bench`, from an empty checkout. This prompt has three parts. Part 1 is research and ends with a written report and a stop. Part 2 is a decision meeting with me that produces the spec. Part 3 is the build, which does not start until Part 2 is done. Do not skip ahead. Do not fabricate any number, date or quote; every factual claim in your reports carries the URL you actually opened and the date you opened it.

## Why this exists

Pomvox is a local-first voice dictation app for macOS (pomvox/pomvox) with a separate Swift SDK, the Pomvox Cleanup Engine (pomvox/pomvox-cleanup-engine). The engine turns raw speech-recognizer output into what the speaker meant: fillers removed, restarts collapsed, self-corrections resolved ("Thursday, no wait, Friday" becomes "Friday"), casing and punctuation restored, with every edit returned as a byte range and the exact input returned when the model cannot do better. We call that job cleanup. Our model is SimpleWords v3 (Hugging Face `ReFyneLabs/simplewords-dictation-cleanup-v3`, Apache-2.0, a fused Qwen3.5-2B fine-tune).

Nobody measures cleanup as its own layer. Dictation products skip it, send it to a cloud model, or prompt a generic local model, and none publish how often they lose a word, invent one, or change a meaning. We want to publish the measure. It must be fair enough that a competitor would submit to it, so it is not named after our model, our model is listed with its failures, and every row is reproducible by a stranger with one command.

Three laws govern cleanup and must shape the scoring: never lose words; every edit is accounted for; when unsure, leave it as said. A benchmark that rewards fluent rewriting over faithful editing is the wrong benchmark. Hold every finding in Part 1 against those laws.

## Local context you may read (read-only; never copy private data into the repo)

- Engine repo: `/Users/abhiram/Desktop/projects/pomvox-cleanup-engine`. Read `README.md`, `docs/contract.md` (outcomes, UTF-8 byte edits, fallback), `docs/cloud.md` (cleanup wire protocol v1) and `Examples/LocalServer/README.md` (the real local engine served at `POST /v1/clean` on loopback; that is how this bench will run SimpleWords without Swift bindings).
- App repo: `/Users/abhiram/Desktop/projects/murmur`. Read `scripts/eval_cleanup_v2.py` (the frozen prompt recipe, a Python port of the output guard, and a Hugging Face snapshot-glob warning you must honour later) and `tests/test_cleanup.py`.
- Vault: `/Users/abhiram/Desktop/projects/pomvox_obsidian_vault`. Read `10 Architecture/SimpleWords Model and Corpus.md` in full: the private eval categories (A, B, C, NAMED, G cross-sentence self-correction; D negatives; E; F ordinary speech; an intra-sentence `regression.jsonl`; Disfl-QA as a held-out set never trained on), why scoring is per category, why violations are discarded not repaired, and the finding that interrogative-phrase corrections were the majority of real disfluency and absent from the corpus. Also `10 Architecture/Eval Capture.md` (record format of real dictations) and `20 Code Review/Review Philosophy.md` (house rules on evidence).

Private data rule: `~/.pomvox/eval/`, `~/.pomvox/history.db` and the vault are the owner's own speech and notes. Do not read the speech data unless a file `data/consent/OWNER_CONSENT.md` exists in this repo stating what may be used and how it must be scrubbed. Ask before creating it.

## Part 1: research

Goal: find out what a credible public benchmark for dictation cleanup should contain, by studying what already exists, what the adjacent fields learned, and what users actually suffer from. The output is a set of reports under `docs/research/`, each a Markdown file with a Sources section listing every page you opened (URL, access date, one line on what it gave you). Use web search and fetch the pages; a search snippet is not a source. Where a question comes back empty, write "not found" and what you searched. Separate what you found from what you recommend, under different headings, in every file.

Write these files:

**`docs/research/01-existing-benchmarks.md`.** Everything that measures something close to cleanup. At minimum investigate: Switchboard disfluency annotations and the disfluency-detection literature built on them; Disfl-QA (Gupta et al. 2021) and how it was annotated and licensed; Hyporadise and the GenSEC challenge on LLM-based ASR error correction; the Open ASR Leaderboard and its text normalizer; inverse text normalization and spoken-form test sets (NeMo ITN, the Sproat text-normalization challenge, Whisper's normalizer); punctuation-restoration benchmarks; the transcription industry's "clean verbatim" style guides (Rev, TranscribeMe, Verbit) which define in prose exactly what cleanup removes and keeps; any dataset of real dictation with cleaned references. For each: what it measures, input and output form, size, license, how references were made, how many references per item, what it cannot see. End with a table and a verdict on which pieces can be reused, under which license, with attribution.

**`docs/research/02-metrics.md`.** How adjacent fields score faithful editing. Investigate grammatical error correction scoring (ERRANT, the M2 scorer, GLEU, why GEC reports F0.5 rather than F1 and whether that logic applies to "under-clean rather than over-clean"); multi-reference handling and how agreement between annotators was measured; WER and its normalizers; metrics for hallucination and omission in ASR post-editing; meaning-preservation checks (NLI-based, embedding-based, LLM-as-judge) and the documented biases of each, especially judges preferring fluent outputs. Recommend a metric set that encodes the three laws, say which published metric each one is or derives from, and name what none of them can catch.

**`docs/research/03-data.md`.** How to build the items. Investigate how Switchboard and Disfl-QA produced references; published methods for synthetic disfluency injection and their known artifacts; TTS-to-ASR round trips as a way to get realistic recognizer errors into inputs; consent, PII scrubbing and release norms for speech-derived text datasets; contamination risks for a fully public test set and what other benchmarks do about it (canary strings, hidden splits, rolling refreshes, verified subsets). Recommend sources, sizes per category, a review process, and a versioning rule.

**`docs/research/04-governance.md`.** How respected leaderboards stay credible. Investigate the Open ASR Leaderboard, MTEB, HELM, SWE-bench and SWE-bench Verified, BIG-bench, Dynabench, and Chatbot Arena: submission rules, what a row must include to be reproducible, who runs the evaluation, how disputes about items are handled, how they handle the organizer's own system being on the board. Recommend our submission rule, run manifest contents, dispute process, and the conflict-of-interest statement.

**`docs/research/05-market.md`.** What the products publish. For Wispr Flow, Superwhisper (including its S1-mini cleanup model), Aqua Voice, Willow, Monologue, Typeless (mono-1), Spokenly, VoiceInk, Handy, Apple's SpeechAnalyzer and macOS dictation, and the cleanup or formatting options of Deepgram, AssemblyAI, Speechmatics and Gladia: what cleanup they claim, what evidence they show, which could run on this bench and through which adapter. Note which are open weights and under what license.

**`docs/research/06-user-pain.md`.** What dictation users complain about, from Hacker News, Reddit, app reviews and GitHub issues of the open-source tools. Group complaints into categories and count them roughly, with links. The point is to weight the bench's categories by real pain, not by what is easy to generate.

**`docs/research/00-summary.md`.** Written last. One page: the recommended shape of the bench in plain words; a table of decisions I must make, each with the options, your recommendation and the evidence file that supports it; what you would reuse from existing work; what you found that contradicts the working hypothesis in the appendix below; and what you could not find out.

Rules for Part 1: open the primary page for every claim; prefer papers, official docs and license files over blog summaries; record access dates; no numbers from memory; do not write any benchmark code; do not create a dataset. Budget: be thorough rather than fast. When the summary is written, stop and tell me it is ready.

## Part 2: decide

We read the reports together. I will answer the decision table. You then write `docs/spec.md`: task definition, item schema, category list with the mapping from the vault's private letters, metric definitions with their formulas and provenance, data sources and sizes, baselines, run manifest, leaderboard columns, governance, licenses. Every choice in the spec cites the research file that supports it. Open a PR with the spec and stop until I approve it.

## Part 3: build

Only after the spec is approved. Python 3.12 with `uv`, a package `cleanupbench` with `validate`, `run`, `score` and `report` commands, adapters behind one interface (identity, OpenAI-compatible, Anthropic, mlx-lm, llama-cpp, Pomvox LocalServer), greedy decoding everywhere, a `run.json` manifest that `score` refuses when incomplete, a determinism check, a static leaderboard generated from `runs/` and never hand-edited, CI for schema and scorer tests, and the docs the spec calls for. Phases, each a PR with a stop: scaffold; scorer with pinned unit tests plus the first hand-written items; adapters and the SimpleWords rows (engine and mlx-lm must agree byte for byte where the engine returns `cleaned`); dataset v1 with generation gates that discard violations; site and the `v1.0.0` tag. Ask before anything leaves this machine: GitHub Pages, a Hugging Face upload, or a post.

## House rules for all parts

- Conventional commits, subject at most 72 characters, GPG-signed. One concern per PR. Never merge your own PR; request review from Abhi.
- No number in any document unless a command in this repo produced it or a cited page states it. No comparative claim ("beats", "better than") anywhere.
- Our model's losses stay on the board, with the failure analysis in the release notes.
- Never modify the engine or app repositories from this session. File issues there if you find bugs.
- Secrets come from the environment and are never written to any file.
- Where a finding conflicts with the vault's reasoning, say so explicitly and let me decide.

## Appendix: the working hypothesis to test, not the spec

This is the design we sketched before any research. Treat every line as a claim to confirm, refine or reject in Part 1, and say which in `00-summary.md`.

- Task: raw lowercase unpunctuated transcript plus optional vocabulary in; cleaned text out; outcome and edits scored when returned.
- Item: id, category, input, vocabulary, 1 to 3 references, slots (`must_contain`, `must_not_contain`), source, license, notes.
- Eleven categories: fillers, restarts, correction-intra, correction-cross, correction-interrogative, punctuation-casing, spoken-form, names-vocabulary, lists-layout, negatives, adversarial-meaning.
- Metrics per category, never pooled: normalized exact match; token-edit precision, recall and F-score against the reference-implied edits; word-loss rate; insertion rate; slot failure rate; over-clean rate on negatives; fallback and unchanged rates. Latency off the leaderboard, in a per-run table with hardware named.
- Baselines: identity; one generic prompt on local and cloud models; SimpleWords v3 through the engine and through mlx-lm.
- Evidence: a leaderboard row is a committed `runs/<system>/<date>/` folder with manifest, outputs and scores, replayable by one command; two runs must hash identical.
- Data: synthetic items with generation gates that discard violations; a labelled Disfl-QA subset with attribution; the owner's dictations only behind an explicit consent file; items versioned and never edited after release.
- Governance: a submission guide, an item-dispute issue template, and the rule that our failures stay on the board.

Start with Part 1. Before you begin, write `docs/research/README.md` listing the six reports, the questions each will answer, and the order you will work in, and show it to me.
