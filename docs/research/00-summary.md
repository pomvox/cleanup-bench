# 00. Summary: what the research says the bench should be

Written last, after re-reading the six reports together. Every claim below is
backed by one of those files, which carry the URLs and access dates
(2026-10-24). Numbers appear only where a report quotes a page. Findings and
recommendations are separated; the decision table is the part that needs the
owner.

## The recommended shape, in plain words

Cleanup Bench scores a text-to-text layer: a raw recognizer transcript goes in,
a cleaned transcript comes out, and the bench asks three questions of every
output, in this order: did any content word disappear, did any word appear that
nobody said, and were the edits that were made the right ones. The first two are
hard-constraint rates derived from the deletion and insertion terms of word
error rate and from SARI's set partition; the third is edit precision, recall
and F0.5 in the manner of the GEC scorers (M2, ERRANT), with the CoNLL-2014
justification that a wrong edit costs more than a missed one. Slot checks stay
as a gate, not the headline. Everything is scored per category and never
pooled. An identity row sits on the board so that "did nothing" is always
visible as a point of comparison with zero word loss (`02-metrics.md`).

Items come from three source types with equal standing and a per-item `source`
field: synthetic (generator plus gates that discard, never repair), derived
(a labelled Disfl-QA subset under CC BY 4.0, public-domain prose for casing and
spoken-form round trips), and dictation (the owner's own, only behind a consent
file). Sizes per category are set by a pilot and a power calculation, not
guessed. Items are frozen per semantic version; a wrong item is retired with an
erratum, never edited (`03-data.md`).

A leaderboard row is a committed `runs/<system>/<date>/` folder whose scores CI
recomputes from the stored outputs; two runs must hash identical; hosted-API
rows live in a dated table with an expiry flag; the organizer's own rows follow
the same rule and every run of our model that produced a score is committed,
including the losing ones. Disputes go through a public issue template with two
reviewers, one external, and items are retired rather than edited
(`04-governance.md`).

Baselines for v1 are identity, SimpleWords v3 through the LocalServer and
through mlx-lm, Superwhisper S1-mini through `llama-server`, and one fixed
generic prompt on a local and a cloud model. Nothing else on the market exposes
a text-in cleanup endpoint (`05-market.md`). Categories are weighted by the
user-pain evidence: words lost or changed by the cleanup layer, invented
content, the model answering instead of cleaning, and imposed punctuation are
the pains users describe as damaging; fillers are an expectation, not a pain
(`06-user-pain.md`).

## Decisions for the owner

| # | Decision | Options | Recommendation | Evidence |
| --- | --- | --- | --- | --- |
| 1 | Headline metric per category | (a) slot pass/fail as in the vault's eval; (b) edit P/R/F0.5 against references; (c) both, with slots as a gate | (c). F0.5 headline with P and R as separate columns, slots as a pass/fail gate. Slot-only scoring is gameable and understates systems relative to reference scoring. | `02-metrics.md` §1, §2, recommendations |
| 2 | Normalizer for "normalized exact match" | (a) Whisper / Open ASR normalizer; (b) reduced: contractions, spelling variants, whitespace, apostrophes; (c) minimal: whitespace and Unicode form only | (c), with (b)'s contraction and spelling rules reserved for the reference-writing guideline. The Whisper normalizer deletes fillers, casing and punctuation and would score identity as correct on filler items. Files 01 and 02 differ on whether contractions belong in the normalizer; the owner picks. | `01-existing-benchmarks.md` §4, rec. 3; `02-metrics.md` §3 |
| 3 | Category list | (a) the appendix's eleven; (b) eleven plus an `instruction-like` category for assistant-mode breakout, `negatives` split into named slices (negation words, filler-lookalikes, non-English tokens, already-clean, fragments), an unrequested-list negative inside `lists-layout`, and `fillers` demoted to a baseline category | (b) | `06-user-pain.md` §1, §4, recs 1, 2, 5, 8 |
| 4 | Weight of the correction categories | (a) weight by the vault's "roughly 66% of real human disfluency"; (b) keep all three correction categories, justify them by the out-of-distribution finding, weight by user pain | (b). The 66% figure describes Disfl-QA's constructed composition, not speech; no user complaint about interrogative-phrase corrections was found. See the conflict note below. | `01-existing-benchmarks.md` §2; `03-data.md` §1; `06-user-pain.md` §7 |
| 5 | Primary data source | (a) synthetic with generation gates, as in the appendix; (b) three source types of equal standing with a per-item `source` field | (b). Every generator paper reports the same artifacts; a test set built from a generator measures the generator. | `03-data.md` §2, R1 |
| 6 | Size per category | (a) fixed numbers now; (b) pilot with identity and two cheap baselines, then a paired power calculation per category, standard errors on every leaderboard number | (b) | `03-data.md` §6, R2 |
| 7 | Owner's dictations in v1 | (a) scored slice in v1 behind the consent file; (b) deferred to a later MINOR release | (b) unless the consent file and scrubbing review can be done before the v1 freeze. Nothing in `~/.pomvox` is read until the file exists. | `03-data.md` R6, open questions |
| 8 | Contamination defence | (a) fully public with canary string, per-item release date, declared-exposure field, fresh slice per MINOR; (b) add a hidden split scored by a third party | (a) for v1. A hidden split conflicts with one-command replay and needs an operator. Revisit if submissions arrive. | `03-data.md` §5, R4; `04-governance.md` |
| 9 | Who runs the evaluation | (a) organizer re-runs every submission; (b) CI recomputes scores from outputs for every PR, organizer re-runs a random subset for a "checked" mark; (c) self-reported only | (b) | `04-governance.md` recs 2, 5 |
| 10 | Hosted-API rows | (a) main board; (b) separate dated table with an expiry flag, never edited | (b). HELM entered maintenance mode citing API drift and deprecation. | `04-governance.md` §3, rec. 6 |
| 11 | SimpleWords download gating | (a) keep the Hugging Face gate and document the account requirement; (b) remove the gate or publish an ungated mirror | (b), if "reproducible by a stranger with one command" is to hold literally. | `05-market.md` licenses; model card opened 2026-10-24 |
| 12 | S1-mini as a v1 baseline | (a) include via `llama-server` on the Q4_K_M GGUF with the card's prompt and a fixed control line, naming clause honoured; (b) exclude | (a). It is the only other open-weight cleanup model with a published prompt and greedy requirement. Record the control line in the manifest. | `05-market.md` §2, recs |
| 13 | VoiceInk Refine as a baseline | (a) include via mlx-lm if the license permits evaluation and redistribution of outputs; (b) exclude otherwise | (b). LICENSE.md, read 2026-10-27: "provided for use with the VoiceInk application only"; "use in other software or open-source projects are not permitted without permission from the copyright holder"; no evaluation clause. A row is possible only with the holder's written permission, recorded in the manifest. | `05-market.md` §8, Addendum 2026-10-27 |
| 14 | Empty output | (a) score as total word loss; (b) treat as a fallback-like status when the reference is empty, word loss otherwise | (b); the spec must define it because S1-mini returns an empty string for filler-only input. | `05-market.md` §2; `02-metrics.md` metric 7 |
| 15 | Homophone policy in references | (a) fix unambiguous homophones, as the vault's model is trained to; (b) leave as said, as the style guides' "do not correct grammar" implies | Owner's call; this is a reference-writing decision and the scorer is neutral on it. If (a), already-correct cases must appear as negatives. | `01-existing-benchmarks.md` §7; `02-metrics.md` conflicts 3 |
| 16 | Style-guide disagreements | discourse-marker scope ("like", "you know", "I mean", "sort of"); slang expansion ("gonna"); grammar correction; emphatic repetition | Narrow discourse-marker removal (only "like" and "you know" when meaningless, per TranscribeMe); never expand slang; never correct grammar; keep emphatic repetition. All four follow the third law. | `01-existing-benchmarks.md` §7, rec. 7 |
| 17 | Fragments and single words | (a) sentence-case and period-terminate, as the vault's full-sentence negatives and the engine guard assume; (b) return fragments as said, minimally cased, no forced period | (b) as items under `negatives`, with the task definition stating the rule. This may conflict with the engine's guard and is flagged. | `06-user-pain.md` §1, §6, "pain not covered" |
| 18 | Dispute adjudication | who the external reviewer is; retire-never-edit; `ERRATA.md`; response target | Adopt the process in file 04 and name the reviewer in `GOVERNANCE.md`. Decisions that would move our model's rank go to the external reviewer. | `04-governance.md` dispute process, COI statement |
| 19 | Adapters in v1 | (a) all six from the appendix; (b) drop the direct llama-cpp binding since `llama-server` exposes an OpenAI-compatible endpoint | (b), unless the determinism check needs process-level sampling control. | `05-market.md` adapters |
| 20 | Input form | (a) one form, lowercase unpunctuated, as the appendix; (b) a per-item `input_form` field, v1 scored on one declared form | (b). Parakeet, Whisper, Cohere Transcribe and Apple's transcribers emit different raw forms. | `05-market.md` cross-cutting 3, input form |
| 21 | Disfl-QA attribution wording | (a) "CC BY 4.0"; (b) "CC BY 4.0 as asserted in the repository README and Hugging Face card; the repository has no LICENSE file and was archived 2026-04-19" | (b) | `01-existing-benchmarks.md` §2 |

## What to reuse from existing work

- **Disfl-QA**: a labelled subset for `correction-interrogative` and
  `correction-cross`, lower-cased and de-punctuated as input, the original
  question as the single reference, CC BY 4.0 with attribution to Gupta et al.
  (`01`, `03`). It maps to nothing else: no fillers, no negatives, one
  disfluency per item.
- **M2 / ERRANT / CoNLL-2014**: the edit-extraction idea, the same-aligner
  rule for hypothesis and reference, best-reference-per-item, F0.5 with its
  stated justification, the noop convention for negatives (`02`).
- **WER's D and I terms and SARI's partition**: word-loss and insertion rates
  as sets (`02`).
- **Whisper and Open ASR normalizer**: only as a documented list of
  non-semantic surface variants and as a filler inventory, never as the
  comparison function (`01`, `02`, `04`). Whisper is MIT, the HF repo
  Apache-2.0.
- **Switchboard's Meteer taxonomy**: filled pause, explicit editing term,
  discourse marker, restart with and without repair, as the vocabulary for
  item notes and the edit audit. The data itself is LDC-licensed and not
  reusable (`01`, `03`).
- **Sproat and Jaitly's semiotic classes** and their rule to report
  unrecoverable errors separately, for `spoken-form` (`01`).
- **IWSLT TED punctuation metric** (per-class P/R for period, comma,
  question) as lineage for `punctuation-casing`, not as data (`01`).
- **Clean-verbatim style guides** (Rev, TranscribeMe, Verbit, GoTranscript)
  as the prose task definition; their disagreements become decision 16 (`01`).
- **BIG-bench canary pattern, MTEB's attestation and dataset-revision check,
  SWE-bench's entries-not-artifacts split and verify command, Open ASR's
  same-decoding and identical-prompt rules, Arena's retired-models list** for
  governance (`03`, `04`).
- **Miller's standard-error and power formulas, Card et al.'s warning** for
  sizing (`03`).
- **Kubis et al.'s back-transcription** as a justified stand-in for
  recognizer errors in `spoken-form` and `punctuation-casing` items only
  (`03`).
- **Wispr Flow's own help article on over-cleaning and S1-mini's model card**
  as the two vendor documents that name the failure modes the bench scores
  (`05`, `06`).

## What contradicts the working hypothesis

Line by line against the appendix:

- **Task** (raw lowercase unpunctuated in, cleaned out, outcome and edits
  scored): confirmed, refined by decision 20 (`input_form` field) and by the
  rule that spoken layout commands are in scope (`05`).
- **Item** (id, category, input, vocabulary, 1 to 3 references, slots, source,
  license, notes): confirmed; add `input_form`, `released`, and a per-item
  `source` type and license, since Disfl-QA items must stay CC BY 4.0 (`03`).
- **Eleven categories**: refined, decision 3. The user-pain file adds
  instruction-like input and splits negatives; it also finds no user evidence
  behind `correction-interrogative`, which keeps its justification from the
  out-of-distribution finding alone (`06`).
- **Metrics**: confirmed and sharpened. F-score becomes F0.5 with P and R
  published; "normalized exact match" needs a reduced normalizer; slot failure
  rate is a gate, not a headline; two metrics are added that the appendix
  lacks: edit accountability (the second law has no metric otherwise) and a
  human-ceiling row where two references exist (`02`).
- **Baselines**: confirmed and extended with S1-mini; VoiceInk Refine is
  excluded by its license (decision 13); cloud baselines go to a dated table (`04`,
  `05`).
- **Evidence** (committed run folder, one-command replay, two runs hash
  identical): confirmed; the manifest gains organizer-provenance, attestation
  and expiry fields (`04`).
- **Data**: refined, decision 5. "Synthetic items with generation gates" as
  the main source inherits the generator's blind spots, the failure the vault
  describes for v2 (`03`).
- **Governance**: confirmed and extended with a dispute process and a
  conflict-of-interest statement, neither of which any surveyed board
  publishes (`04`).

Two premises in the prompt itself are corrected by the research:

- **mono-1 belongs to Monologue, not Typeless.** Monologue's blog post
  introduces it; nothing on Typeless's site mentions it (`05`).
- **The model id.** The prompt names `ReFyneLabs/simplewords-dictation-cleanup-v3`;
  the vault and the app script name `abhiram3040/...`. Both ids resolved on
  2026-10-24 to the same gated Apache-2.0 card (model card opened directly for
  this summary; `05` §13).

## Conflicts with the vault, stated for the owner

1. **"Roughly 66% of real human disfluency."** Disfl-QA's paper reports that
   over 65% of its own disfluencies are corrections, in a set whose annotators
   were instructed to write corrections into Wikipedia questions and to exclude
   filled pauses and partial words. It is a statement about the brief, not
   about speech. The one natural-speech distribution found (Switchboard, as
   reported by Yang et al. 2020) has repetitions as the majority type. The
   methodological lesson the vault draws, that an outside corpus revealed a
   missing category, stands; the frequency claim does not (`01` §2, `03` §1).
2. **Slot pass/fail as the pass criterion** understates systems and is
   gameable in isolation; the GEC literature scores edits against references
   (`02` conflicts 1).
3. **The length-ratio guard** is a production device, not a metric. The scorer
   should never apply it; the LocalServer adapter's rejections should surface
   as fallback status so the guard's cost is visible (`02` conflicts 2).
4. **Homophone fixing** is a reference-writing decision the vault made for the
   model; the bench's references must take a position (decision 15).
5. **Full-sentence negatives.** User evidence puts fragments and single words
   among the damaging failures; the vault's negatives are full sentences and
   the engine's guard assumes sentence shape (decision 17).
6. **Discard, never repair** carries over to the benchmark as "retire, never
   edit", with a published discard log at generation time and an erratum file
   after release. No conflict; the rule is widened (`03` R3, `04`).

## What could not be found out

Retried 2026-10-27 (Part 1b; details in the "Addendum 2026-10-27" sections
of files 03, 04, 05 and 06): Reddit was reached through two archive mirrors
(pullpush, arctic-shift) and not through reddit.com itself; the r/WisprFlow
and r/superwhisper material confirms the four highest-weighted pains and adds
none for `correction-interrogative`, so the weighting in file 06 stands.
VoiceInk Refine's LICENSE.md was read: use is limited to the VoiceInk
application and use in other software is forbidden without permission, which
settles decision 13 as (b). Wispr Flow's official API exists but is a
read-only meetings API; no vendor names its cleanup model, except that
Typeless names Microsoft and Google as cloud AI providers. OpenAI's SWE-bench
Verified post was read from the Wayback Machine and confirms the figures
cited second-hand. Kaggle's leaderboard text was read through a third-party
rendering of the official page; it states the split without a percentage.
Consent-form elements were sourced from an LMU Munich speaker template,
Common Voice's contributor strings, the Data Statements guide and the
Montreal Data License, but no template written for releasing one's own
dictations exists. The list that remains:

- Any English dataset of real dictation with cleaned references (`01` §8).
- A published over-correction, fabrication or omission rate for ASR
  post-editing; a human-ceiling study for cleanup; any judge-bias study on
  this task (`02` §4, §7).
- Any generator for cross-sentence or interrogative-phrase corrections (`03`
  §2).
- Reddit through reddit.com itself (mirrors only, with most r/WisprFlow post
  bodies removed); the Monologue feedback board, offline; the New York Times
  essay on Wispr Flow; G2, TrustRadius and Product Hunt reviews (`06` source
  table and addendum).
- Kaggle's page through Kaggle's own servers or the Wayback Machine (both
  serve a JavaScript shell); the percentage of test data on the public board,
  which the page does not state (`03` addendum).
- Shriberg's 1994 thesis text; an LDC word count for the Switchboard
  disfluency subset; a license statement for the IWSLT punctuation data
  (`01`).
- HyPoradise's effective license: MIT in the paper, repo LICENSE and HF card,
  but a noncommercial no-derivatives agreement ships in the same repository
  (`01` §3). Not reused.
- Which model Willow, Wispr Flow and Aqua use for cleanup (their privacy
  policies name no provider); which of Typeless's two named providers does
  cleanup; what `platform.wisprflow.ai` ("Flow API | Dashboard") offers behind
  its JavaScript shell; current LeMUR documentation (`05` and addendum).
- A consent template written for releasing one's own dictations; LDC's
  consent and licensing pages (HTTP 403/404); the Common Voice terms page
  itself (`03` §4 and addendum).

## Sources

The six research files, all written from pages opened on 2026-10-24, with
addenda dated 2026-10-27 in files 03, 04, 05 and 06 that carry their own
source lists:
`01-existing-benchmarks.md`, `02-metrics.md`, `03-data.md`,
`04-governance.md`, `05-market.md`, `06-user-pain.md`. One page was opened
directly for this file:

- https://huggingface.co/ReFyneLabs/simplewords-dictation-cleanup-v3 and
  https://huggingface.co/abhiram3040/simplewords-dictation-cleanup-v3,
  2026-10-24, both resolve to the same card: license apache-2.0, gated access,
  `system_v2.txt` at the repo root, per-category gates with the `reg_003` miss
  stated.
