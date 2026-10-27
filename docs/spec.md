# Cleanup Bench specification, v1

Status: draft for the owner's review (`docs/CONTINUE.md` Step 3). Every
choice cites the research file and section that supports it and the row in
`docs/decisions.md` (written `D<n>`) that chose it. Rows marked provisional
there are provisional here.

The three laws govern everything below: never lose words; every edit is
accounted for; when unsure, leave it as said (`docs/PROMPT.md`).

## 1. What the bench is and is not

Cleanup Bench measures one text-to-text layer: a raw speech-recognizer
transcript goes in, a cleaned transcript comes out. It does not measure
speech recognition, capture, voice activity detection or latency-critical
paste behaviour; those failures dominate the open-source issue trackers and are
out of scope for a text bench (`06-user-pain.md` §2, summary table). The bench
is English only; non-English tokens inside English speech are in scope as
`negatives` that must pass through unchanged (`06` rec. 9).

It scores cleanup of a given input. Recognizer errors in the input are part of
the item; cleanup is not expected to delete recognizer hallucinations, because
it cannot tell them from speech and the first law forbids the guess (`06`
"pain the appendix does not cover").

Nothing in this repository makes a comparative claim about any system
(`docs/PROMPT.md` house rules). The bench is not named after any model.

## 2. Task definition

### 2.1 Input and output

An item supplies `input` (the transcript), `input_form` (D20), an optional
`vocabulary` list and the references. A system returns:

- `output_text`: the cleaned transcript, raw and un-normalized (`04` run
  manifest: "Raw, un-normalized output is stored").
- `outcome`: `cleaned`, `unchanged` or `fallback` with a reason, when the
  adapter exposes one (the engine contract's outcomes); otherwise derived by
  the scorer as `unchanged` when the output equals the input byte for byte and
  `cleaned` otherwise. An empty output is the status `empty` (D14).
- `edits`: optional, ordered, non-overlapping half-open UTF-8 byte ranges with
  replacements that reconstruct `output_text` from `input` (engine
  `docs/contract.md`, "Edits are ordered, non-overlapping scalar-boundary
  ranges measured in original UTF-8 bytes").

### 2.2 What cleanup removes and keeps

The prose definition is the agreed core of the industry clean-verbatim guides
(`01` §7, rec. 7), with the disagreements resolved by D16:

Removed:
- Filled pauses (Meteer's `{F}`: "uh", "um" and the Open ASR normalizer's
  wider inventory used as the audit list, `01` §1, §4).
- Stutters and partial-word false starts ("we should def we should
  definitely").
- Unintentional repetition ("the the").
- False starts and restarts with or without repair, in Meteer's sense: the
  reparandum and interregnum go, the repair stays (`01` §1; `03` §1).
- Self-corrections: when the speaker unambiguously replaces something in the
  same slot ("Thursday, no wait, Friday"), only the revised version stays and
  anything that referred to it is updated; when the second phrase adds or
  narrows rather than replaces, both stay (engine frozen prompt,
  `Sources/CleanupCore/CleanupLogic.swift`; `01` §7 notes the guides are
  silent on this case, which is why the correction categories need
  first-party references).
- The discourse markers "like" and "you know" only when they carry no meaning
  (TranscribeMe, `01` §7; D16). "I mean", "sort of", "kind of", "so",
  "actually", "well" are kept.
- Explicit editing terms inside a correction ("no wait", "I mean", "scratch
  that", "actually" as a correction signal) go with the reparandum; "actually"
  used for emphasis stays (engine prompt).

Kept:
- Every content word not covered above (law 1).
- Emphatic repetition ("no, no, no"; "really really fast") (GoTranscript,
  `01` §7; D16).
- Slang and contractions as said: "gonna" stays "gonna", "dunno" stays
  "dunno" (D16; `06` §5 lists expansion among the unwanted changes).
- Grammar as spoken: no grammar correction (GoTranscript, `01` §7; D16).
- Homophones as said (D15).
- Negation words, always (`06` §1: "never merge" became "merge"; D3
  `negation` slice).
- Non-English words inside English speech, including ones that spell an
  English filler (German "um", Spanish "ha", Portuguese "um") (`06` §1; D3
  `non-english` slice).
- A question stays a question (app guard vectors
  `tests/test_cleanup.py::test_reject_answered_question`; `06` §4).

Added or changed:
- Sentence casing and punctuation restored for sentence-shaped input
  (`01` §6 lineage; `06` §6).
- Fragments and single words: returned as said, first letter upper-cased
  only when the fragment is sentence-initial in form, no forced terminal
  period (D17). "okay" → "Okay"; "go ahead" → "Go ahead"; a lowercase
  fragment that is clearly a continuation ("and the second one") keeps its
  case. The reference decides per item; the rule here is the default.
- Spoken layout commands are in scope: "new line", "new paragraph", "bullet"
  become layout except where a modifier makes the phrase content ("a new line
  of products", "silver bullet") (engine `spokenLayout` transform,
  `docs/contract.md`; `05` input form). Spoken punctuation words ("comma",
  "period") are in scope under `lists-layout` only when the item says so in
  `notes`; the default is that they are content.
- Lists: only when the speaker asks for or announces one; the list is made of
  the speaker's words; an uninvited list is an error (`06` rec. 8; engine
  prompt; D3 unrequested-list slice).
- Spoken numbers: two-sided (`06` rec. 6). The reference decides whether a
  number is written as digits or words; "first thing Monday" and "step one"
  stay words; the task definition does not impose a numeral rule.
- Vocabulary: a supplied term's spelling and casing is honoured when the input
  contains a recognizable form of it; a term is never "corrected" away;
  names not in the vocabulary are left as transcribed (`06` rec. 7).
- The output is the cleaned dictation and nothing else: no answer, no
  commentary, no analysis, no role prefix, no markdown header (`06` §4; app
  and engine guard vectors; D3 `instruction-like`).

### 2.3 Input forms

`input_form` takes one of: `lowercase-unpunctuated` (Parakeet-style, Deepgram
`punctuate=false`), `cased-punctuated` (Whisper, Cohere Transcribe, Apple
SpeechTranscriber), `cased-punctuated-digits`, `lowercase-digits` (`05`
cross-cutting 3). v1 scores only `lowercase-unpunctuated`; items in other
forms may exist in the files with `scored: false` and are excluded by `score`
(D20). Adding a scored form later is a MINOR release (§7.6).

### 2.4 Decoding

Greedy decoding everywhere, one prompt per system fixed across all categories,
no category names, per-item hints or vocabulary beyond what the item supplies
(`04` submission rule 3, 4; Open ASR "same decoding hyper-parameters" and
"identical prompt"). The manifest records it (§9).

## 3. Categories

Twelve categories (D3). Scores are per category and never pooled
(`02` recommendations; ERRANT's motivation; the vault's 0/5 finding).

| Category | What it tests | Slices | Pain evidence (`06`) |
| --- | --- | --- | --- |
| `fillers` | filled pauses, stutters, unintentional repetition removed; everything else kept | — | §8: an expectation, not a pain; baseline category |
| `restarts` | false starts and restarts with and without repair (Meteer) | — | §7 |
| `correction-intra` | same-sentence self-correction replacing a slot (word, name, number, count); chained corrections | — | §7; vault `regression.jsonl` |
| `correction-cross` | correction whose repair is in a later sentence ("Thursday. No wait, Friday.") | — | §7; vault A, B, C, NAMED, G |
| `correction-interrogative` | correction that replaces the interrogative phrase ("where is, or what city has") | — | none found in §7; justified by the vault's out-of-distribution finding only (D4) |
| `punctuation-casing` | sentence casing and punctuation restored; over-punctuation scored as error | `restore`, `no-over-punctuation` | §6, largest single category |
| `spoken-form` | numbers, dates, times, money, measures, spelled emails and URLs; two-sided | by semiotic class (`01` rec. 5) | §9 |
| `names-vocabulary` | honouring supplied vocabulary spelling and casing; not altering names outside it | — | §10 |
| `lists-layout` | invited lists, spoken layout commands, paragraph breaks; uninvited lists kept as prose | `invited`, `spoken-layout`, `unrequested-list` (negative) | §11 |
| `negatives` | input that must come back with its content untouched | `negation`, `filler-lookalike`, `non-english`, `already-clean`, `fragments`, `homophone-correct` | §1, the damaging failures |
| `adversarial-meaning` | inputs where a plausible "clean" rewrite changes meaning (negation scope, "actually" as emphasis, "like a charm", additive "I mean") | — | §1, §5 |
| `instruction-like` | dictated questions, dictated prompts, dictation about the cleanup rules; must come back as cleaned dictation, not an answer or commentary | — | §4 |

### 3.1 Mapping from the vault's private letters

From `10 Architecture/SimpleWords Model and Corpus.md` (read-only; no private
data is copied):

| Vault set | Bench category |
| --- | --- |
| A, B, C, NAMED, G (cross-sentence self-correction gate) | `correction-cross` (NAMED items also carry a `vocabulary`) |
| `regression.jsonl` (intra-sentence, including `reg_003`'s chained triple correction) | `correction-intra` |
| D (negatives, must not correct) | `negatives`, slice `already-clean` |
| F (ordinary speech, zero guard rejections) | `fillers` and `negatives/already-clean` |
| E | not described in the vault note; no mapping is claimed |
| Disfl-QA (held out) | `correction-interrogative` and `correction-cross`, as a `derived` source |

The vault's items themselves are not copied; the mapping says where a
category of its kind lives here.

### 3.2 Weighting

Categories are not weighted into a single number; there is no overall score
(§6.9). The order of the leaderboard columns follows the pain evidence:
`negatives`, `adversarial-meaning`, `instruction-like`, `punctuation-casing`,
the three correction categories, `restarts`, `spoken-form`, `lists-layout`,
`names-vocabulary`, `fillers` (`06` recs 1 to 5; D4).

### 3.3 Why `fillers` is a baseline category

English filler removal is an expectation; the real risk is the false positive,
which lives in `negatives` (`06` rec. 5). The category stays so that the
identity row's F0.5 of zero on it is visible.

### 3.4 Conflicts stated (fragments)

The engine's guard and the vault's negatives assume sentence shape; the
engine's `shortWordOverlap` and length guards admit "Go ahead." for "go
ahead" (`CleanupLogic.swift`; app `test_accept_short_raw_sharing_a_word`).
D17 says a fragment keeps its shape. Where a system period-terminates a
fragment, metric 1 scores a false-positive edit; this is intended. The issue
text for the engine repo is in `docs/issues/engine-fragment-guard.md`.

### 3.5 Conflicts stated (the 66% figure)

The vault's "roughly 66% of real human disfluency" describes Disfl-QA's
constructed composition (`01` §2; `03` §1). The bench keeps
`correction-interrogative` on the strength of the methodological finding (an
outside corpus revealed a missing category) and does not weight it by that
figure (D4).

## 4. Item schema

Items are JSON Lines, one object per line, under `data/items/<category>.jsonl`.
The JSON Schema is `src/cleanupbench/schemas/item.schema.json`;
`cleanupbench validate` enforces it.

```json
{
  "id": "negatives-negation-0001",
  "category": "negatives",
  "slice": "negation",
  "input": "never merge a change like this without a review",
  "input_form": "lowercase-unpunctuated",
  "vocabulary": [],
  "references": ["Never merge a change like this without a review."],
  "slots": {"must_contain": ["never"], "must_not_contain": []},
  "source": {"type": "synthetic", "method": "hand-written", "origin": "cleanup-bench authors", "license": "CC-BY-4.0", "attribution": ""},
  "notes": "negation word must survive; Wispr Flow report of dropped 'never' (06 §1)",
  "taxonomy": [],
  "released": "2026-10-27",
  "status": "active",
  "scored": true
}
```

| Field | Meaning | Provenance |
| --- | --- | --- |
| `id` | `<category>-<slice or 'core'>-<4 digits>`, stable forever | `03` R5 (never edited) |
| `category`, `slice` | §3 | D3 |
| `input`, `input_form` | §2.1, §2.3 | D20 |
| `vocabulary` | terms passed to the system exactly as the engine's request field; at most the engine's limits (64 terms, 128 bytes each, 2,048 bytes combined, no line breaks) | engine `docs/contract.md` |
| `references` | one to three cleaned outputs that each obey the three laws; the appendix's "1 to 3" is kept | `03` R3; `02` metric 9 |
| `slots` | `must_contain`, `must_not_contain`: phrases matched on word boundaries in the normalized output; a gate, never the headline | D1; `02` metric 5 |
| `source.type` | `synthetic`, `derived` or `dictation` | D5; `03` R1 |
| `source.method` | `hand-written`, `generator:<name>@<version>`, `round-trip:<tts>/<asr>`, `corpus` | `03` §2, §3 |
| `source.origin`, `source.license`, `source.attribution` | per-item license and attribution; Disfl-QA items carry D21's wording | `03` R6; `01` §2 |
| `notes` | why the item exists, in Meteer's vocabulary where it applies | `01` rec. 4 |
| `taxonomy` | optional list from `filled-pause`, `explicit-editing-term`, `discourse-marker`, `restart-with-repair`, `restart-without-repair`, `complex-restart`, `repetition`, `substitution`, `deletion` | `01` §1; `03` §1 |
| `released` | the date the item first appeared in a tagged release; used for release-date windows | `03` R4 |
| `status` | `active` or `retired`; a retired item keeps its line, gains `retired_in` and `issue`, and is excluded from scoring | `04` dispute process 3 |
| `scored` | false for items in an unscored `input_form` | D20 |

Every item file begins with a comment line carrying the canary string (§7.5).
The content hash recorded in manifests (`items_sha256`) is over the item files
exactly as committed.

## 5. Reference-writing guideline

References are written by hand or produced by a generator and then reviewed;
they are never edited after release (§7.4). Rules the scorer depends on:

1. A reference obeys the three laws; a reviewer rejects any that does not
   (`03` R3, third question).
2. Contractions, slang and spelling stay as said (D16). A reference does not
   expand "gonna" or Americanize spelling.
3. Homophones stay as said (D15).
4. Sentence-shaped input gets sentence casing and terminal punctuation;
   fragments do not (D17).
5. A second reference is added only when two reviewers produce different,
   law-abiding cleanups (`03` R3 "multiple references"); never to pad.
6. Spoken numbers follow the item's `notes`; where the notes are silent, the
   reference keeps words (`06` rec. 6).
7. The reference for a filler-only input is the empty string (D14).

Where an owner decision changes a rule (for example D15 to (a)), items written
under the old rule are retired, not rewritten (§7.4).

## 6. Metrics

All metrics are computed per category and never pooled (`02`
recommendations). Where an item has several references, each metric takes the
per-item best reference for that metric (D-S2; M2's rule, `02` §1). The
tokenizer and normalizers are part of each metric's definition and are pinned
by unit tests whose expected values are worked by hand (`docs/PROMPT.md` Part
3).

### 6.1 Tokenizer and normalizers

- **Token**: the scorer splits text into tokens: maximal runs of letters,
  digits, apostrophes and internal hyphens form word tokens; each punctuation
  mark is its own token; each line break is a `⏎` token so that layout is
  visible to edit extraction. Whitespace is not a token.
- **Minimal normalizer** (D2): Unicode NFC; `’` `‘` to `'`; `“` `”` to `"`;
  runs of spaces and tabs to one space; leading and trailing whitespace
  removed; line breaks preserved. Nothing else.
- **Content tokens** (for the hard-constraint metrics): word tokens of the
  minimally normalized text, lower-cased, with punctuation and `⏎` tokens
  dropped. Case and punctuation therefore never count as word loss or
  insertion (`02` metric 3).

### 6.2 Metric 1: edit precision, recall, F0.5 (headline)

Edits are extracted from the token sequences of (input, output) and of
(input, reference) with the same procedure (ERRANT's "processed in the same
way", `02` §1; D-S1, D-S6):

1. Tokenize both sides (case-sensitive; punctuation tokens included).
2. Compute a Levenshtein alignment over tokens with cost 0 for an identical
   token, cost 1 for insertion or deletion, and substitution cost 1 except
   that a token pair differing only in case or only in a punctuation
   attachment costs less than 1, so that a casing change aligns to its own
   word rather than to a neighbour. The exact costs are constants in the
   scorer and in the unit tests.
3. Merge maximal runs of non-identical alignment operations into one edit:
   `(start, end, replacement)` in input-token coordinates, where `replacement`
   is the output tokens the run produced (empty for a pure deletion). Unlike
   M2's lattice search, no unchanged tokens are absorbed into an edit.
4. An output edit is a true positive when a reference edit has the same
   `start`, `end` and `replacement` (ERRANT's scorer, `02` §1). Unmatched
   output edits are false positives; unmatched reference edits are false
   negatives.
5. Per category: P = ΣTP / Σ(TP+FP), R = ΣTP / Σ(TP+FN),
   F0.5 = (1 + 0.5²) × P × R / (0.5² × P + R), the CoNLL-2014 formulas with
   β = 0.5 and their justification (`02` §1).
6. Per item the reference maximizing the item's own F0.5 is used (ties:
   the first). When TP+FP = 0 the precision is null; when TP+FN = 0 the recall
   is null; F0.5 is null when either is (D-S3).

What it cannot catch: a legitimate edit absent from every reference; a
meaning change that keeps every token (`02` "what none can catch").

### 6.3 Metric 2: normalized exact match (secondary)

`minimal(output) == minimal(reference)` for any reference. Reported as the
fraction of items. Provenance: GEC sentence-level accuracy with a normalizer
deliberately weaker than Whisper's (`02` metric 2; D2).

### 6.4 Metric 3: word-loss rate (hard constraint)

Let `R` be the multiset intersection of the content tokens of the best
reference with the content tokens of the input (the words the speaker said
that the reference keeps), and `O` the multiset of output content tokens.
Loss = |R − O| / |R| (multiset difference), averaged over items; items with
|R| = 0 contribute 0. The best reference is the one minimizing loss. An empty
output with a non-empty reference has loss 1 (D14). A token the reference
introduces (a digit form, a vocabulary spelling) is scored by metric 1, never
as loss, so the identity row's loss is zero by construction. Provenance:
WER's deletion term restricted to content tokens; SARI's "input retained in
the references but deleted by the system" region (`02` metric 3). Measured
against the reference, not the input, so sanctioned deletions (fillers,
reparanda) are not losses.

What it cannot catch: a word replaced by a wrong word (that is a substitution,
caught by metrics 1 and 4).

### 6.5 Metric 4: insertion rate (hard constraint)

Let `V` be the set of content-token types in the input and in every
reference. Insertion = (number of output content tokens whose type is not in
`V`) / (number of output content tokens), averaged over items; an empty output
contributes 0. Provenance: WER's insertion term; SARI's "output in neither
input nor reference" region; HyPoradise's "tokens missing from the N-best
list" named as the risk (`02` metric 4). A numeral that no reference writes
as digits counts as an insertion by this definition; that is deliberate, since
a form no reference sanctions is content the speaker did not say.

What it cannot catch: a duplicated input word (caught by metric 1 as FP).

### 6.6 Metric 5: slot failure rate (gate)

An item with slots fails when any `must_contain` phrase is absent from, or any
`must_not_contain` phrase is present in, the lower-cased minimally normalized
output, matched on word boundaries. Rate = failing items / items with slots.
No published parent (`02` metric 5). Trivially satisfiable alone, hence a gate
column, never the headline (D1).

### 6.7 Metric 6: over-clean rate on noop items

An item is a *noop item* when, for every reference, the content tokens of the
reference equal the content tokens of the input (ERRANT's noop convention,
`02` metric 6). Over-clean = fraction of noop items whose output content
tokens differ from the input content tokens. Casing and punctuation changes
on a noop item are not over-cleaning here; they are scored by metric 1.
Reported for every category that has noop items, which is at least
`negatives` and the `unrequested-list` slice. Provenance: I-measure's
true-negative argument (`02` §1).

### 6.8 Metric 7: status columns

Fractions of items with outcome `fallback` (with the reason distribution),
`unchanged`, `empty` and `invalid` (metric 8). Not scores. For adapters without
outcomes, `unchanged` means byte-identical output. A Pomvox LocalServer guard
rejection is `fallback` with reason `rejected` and the `rejectedBy:` warning
kept in the output record; the scorer never applies a guard itself (D-S5;
`02` conflicts 2).

### 6.9 Metric 8: edit accountability (validity gate)

When a system returns `edits`, applying them to the input's UTF-8 bytes must
reproduce `output_text` byte for byte, with ranges ordered, non-overlapping,
within bounds and on scalar boundaries (engine `docs/contract.md`,
`docs/cloud.md`: "exact byte reconstruction"). A failure marks the item
`invalid` for that row: it is excluded from every other metric's numerator and
denominator and counted in the `invalid` column. Law 2 has no published
metric; this is the engine contract applied (`02` metric 8).

### 6.10 Metric 9: human-ceiling row

For items with at least two references, reference 2 is scored as if it were a
system against reference 1 on metrics 1 to 4, and reported as a row named
`human-ceiling` with the item count it covers (Bryant and Ng, `02` §2). It
bounds the other rows; it is not a system.

### 6.11 Uncertainty

Beside every per-item-mean metric (2 to 7) the scorer reports n and the
standard error of the mean: for binary per-item scores SE = sqrt(p(1−p)/n),
for per-item rates the sample standard deviation over sqrt(n) (Miller, `03`
§6). For metrics pooled over counts (metric 1) the scorer reports a paired
bootstrap interval over items with a fixed seed; the resample count and seed
are parameters recorded in `scores.json`. Comparisons between two rows use the
paired per-item differences (Miller's recommendation).

### 6.12 No overall score

There is no pooled number across categories. A leaderboard is sorted by the
category the reader chooses; the default order is §3.2.

### 6.13 Latency

Off the leaderboard. Each run folder carries a latency table (p50 and p95 of
`latency_ms` over items, hardware named from the manifest), after the Open ASR
Leaderboard's practice of reporting RTFx next to, not inside, the quality
score (`02` recommendations).

### 6.14 Meaning-preservation checks

No NLI, embedding or LLM judge in the scorer (`02` "diagnostic, not
scored"). A bidirectional sentence-level entailment check may be offered later
as a review-time diagnostic for item authors; it never produces a column.

## 7. Data

### 7.1 Sources per category

Three source types of equal standing with a per-item `source` field (D5;
`03` R1). Per category, the v1 plan follows `03` R1's table:

| Category | v1 sources |
| --- | --- |
| `fillers` | `synthetic` hand-written and generator insertion of the Meteer `{F}`/`{D}`/`{E}` inventory |
| `restarts` | `synthetic` hand-written and LARD-style break-and-append, reviewed |
| `correction-intra` | `derived` Disfl-QA entity/adverb/entity-type corrections; `synthetic` hand-written with the LARD cue inventory |
| `correction-cross` | `synthetic` hand-written only (no public source exists, `03` §2) |
| `correction-interrogative` | `derived` Disfl-QA interrogative-restart subset, labelled here with a published guideline |
| `punctuation-casing` | `derived` public-domain prose lower-cased and de-punctuated; `synthetic` round trip where available |
| `spoken-form` | `synthetic` hand-written per semiotic class; round trip where available |
| `names-vocabulary` | `synthetic` with names from a published list |
| `lists-layout` | `synthetic` hand-written |
| `negatives` | `derived` Disfl-QA `original` questions; fluent public-domain sentences; hand-written slices |
| `adversarial-meaning` | `synthetic` hand-written, with non-adversarial items mixed in (Dynabench caveat, `03` §5) |
| `instruction-like` | `synthetic` hand-written from the shapes in the app and engine guard vectors |
| any | `dictation` only after `data/consent/OWNER_CONSENT.md` exists (D7) |

### 7.2 Sizes

No fixed sizes (D6). The procedure:

1. Pilot: identity plus two cheap baselines (one local generic prompt, one
   cloud generic prompt) on the hand-written draft of every category.
2. `cleanupbench power` estimates per-item variance per category and metric
   from the pilot and prints Miller's paired sample size for a range of
   minimum detectable differences at α = 0.05 and 80% power (`03` §6, R2).
3. The owner picks the minimum detectable difference per metric; the dataset
   card records it and the resulting n per category.
4. Miller's "at least 1,000 questions" is the whole-bench floor to aim at;
   Card et al. is the reason not to ship a category below its computed size
   (`03` §6).

### 7.3 Generation gates and review

Generated items pass gates that discard and log, never repair (vault rule
widened, `03` R3): slot gate (references satisfy their own slots),
no-content-loss gate (reference content tokens ⊆ input content tokens unless
the item's notes name a sanctioned conversion), no-invention gate, format
gate (schema), law gate (a human answer). The discard log is published with
each release.

Review follows Disfl-QA's two-round design with discard instead of repair
(`03` R3): an independent reviewer answers "consistent with the input's
meaning", "natural as speech" and "does the reference obey the three laws";
any "no" discards. Raw agreement and Cohen's κ per category are reported in
the dataset card. A blind re-score of a random sample per category precedes
release (`03` §1 label-noise finding).

### 7.4 Versioning, retirement, errata

Semantic Versioning for the dataset (`03` R5): MAJOR when any released item is
removed or the scoring contract changes; MINOR when items are added; PATCH for
documentation. Item text, references and slots are never changed in place. A
wrong item is retired (`status: retired`, `retired_in`, `issue`) and listed in
`ERRATA.md` with date, issue link and reason (`04` dispute process 3, 5).
Each release is a git tag and `items_sha256` is recorded in every manifest.

### 7.5 Contamination

Fully public (D8): a canary string in every data file, the README and the
site, following the BIG-bench sentence pattern with a GUID generated in this
repository at release time (`03` §5, R4); the manifest's
`attestation.known_overlap` and `attestation.no_training_on_items` fields
(§9); a fresh slice per MINOR release scored separately from the frozen core.
The canary is a request to corpus builders, not a guarantee.

### 7.6 Consent and scrubbing

Owner dictations enter only behind `data/consent/OWNER_CONSENT.md` stating
scope, scrubbing method and revocation (Datasheets questions, `03` §4, R6).
Scrubbing is automated detection plus human review; names and places are
personal data under GDPR Article 4 (`03` §4). A takedown path exists for any
item (People's Speech, `03` §4). Deferred for v1 (D7).

## 8. Baselines

| Row | Adapter | Prompt | Notes |
| --- | --- | --- | --- |
| identity | `identity` | none | the floor; every noop item should be perfect here, which validates the scorer (`05` baselines) |
| SimpleWords v3 via engine | `pomvox-localserver` against `Examples/LocalServer` `POST /v1/clean` | the pack's frozen `system_v2.txt` | outcomes and edits returned; guard rejections surface as fallback |
| SimpleWords v3 via mlx-lm | `mlx-lm` | `system_v2.txt` in one user turn, `enable_thinking=False`, greedy (model card; app `eval_cleanup_v2.py`) | must agree byte for byte with the engine row wherever the engine returns `cleaned`; a disagreement is an issue for the engine repo, not a patch here |
| S1-mini by Superwhisper | `openai-compatible` against `llama-server` on `superwhisper/s1-mini-GGUF:Q4_K_M`, `--temp 0`, thinking off | the card's system prompt plus the control line in D12 | naming clause honoured; empty output on filler-only input handled by D14 |
| generic local | `openai-compatible` against a local server with an open-weight model | `prompts/generic-v1.txt`, versioned | the bench's own fixed prompt (`05` baselines) |
| generic cloud | `anthropic` | `prompts/generic-v1.txt` | hosted table (D10) |
| human-ceiling | scorer | — | §6.10 |

Not runnable in v1 and listed in `SUBMITTING.md` as invited: Wispr Flow,
Willow, Typeless, Aqua Voice cleanup, Superwhisper S1-Language, Monologue
mono-1, Apple dictation (`05` recommendations). VoiceInk Refine is excluded
by its license (D13; `05` Addendum 2026-10-27): the file limits the model to
use with the VoiceInk application and forbids use in other software without
permission.

## 9. Run manifest and outputs

A row is `runs/<system>/<date>/` with `run.json`, `outputs.jsonl` and
`scores.json` (`04` submission rule 1). `score` refuses a manifest missing any
required field (`04` run manifest). The JSON Schema is
`src/cleanupbench/schemas/run.schema.json`.

Required fields (each with its precedent in `04`):

- `schema_version`
- `bench_version`, `items_sha256`
- `system.name`, `system.org`, `system.organizer_row` (true for rows produced
  by the maintainer; SWE-bench's `agent_org`/`model_org` split), `system.model_id`,
  `system.model_revision`, `system.open_weights`, `system.license`,
  `system.params_total` (null allowed with a reason), and either
  `system.weights_sha256` (local) or `system.api_model_id` plus
  `system.api_date` (hosted)
- `adapter.name`, `adapter.version`, `adapter.config` (endpoint without
  secrets, model path, control line, max tokens)
- `prompt.sha256`, `prompt.text` (empty for identity)
- `decoding` (`strategy: greedy`, `temperature`, `max_tokens`,
  `thinking: false` where applicable)
- `vocabulary_policy` (`item` when the item's list is passed, `none` otherwise,
  and how it is rendered)
- `hardware.machine`, `hardware.os`, `hardware.accelerator`, `hardware.ram_gb`
- `software.python`, `software.packages`, `software.bench_commit`
- `run.started_at`, `run.finished_at`
- `determinism.run_a_sha256`, `determinism.run_b_sha256`,
  `determinism.identical`
- `outputs_sha256`
- `attestation.no_training_on_items` (boolean), `attestation.known_overlap`
  (text), `attestation.declared_exposure` (`none`, `possible`, `yes`)
- `hosted` (boolean), `hosted_expiry_flag` (null unless a hosted model is
  withdrawn; set by a later commit that never edits other fields)
- `checked_by`, `checked_date` (null by default; the organizer's re-run mark)

`outputs.jsonl`: one line per item with `id`, `output_text`, `outcome`,
`fallback_reason`, `edits`, `warnings`, `latency_ms`, `raw` (the adapter's
raw response text where that differs from `output_text`, for audit).

Determinism: `run` performs two passes and records both hashes; `score`
refuses `identical: false` except for hosted rows with an explicit flag
(D-S4). Greedy decoding is recorded, not assumed. The determinism hash is
the SHA-256 of the canonical JSON of the output records sorted by id,
restricted to `id`, `output_text`, `outcome`, `fallback_reason` and `edits`,
so that latency never breaks it; `outputs_sha256` is the hash of the stored
file and ties `scores.json` to it. Pass A is stored; pass B exists only to
prove the hash, and the first divergent item id is recorded when they
differ.

## 10. Leaderboard

Generated from `runs/` by `cleanupbench report` and never hand-edited; CI
regenerates and fails on a difference.

Main board, one row per committed non-hosted run, columns per category:
F0.5, P, R, word-loss, insertion, exact-match, slot-fail, over-clean (where
noop items exist), fallback, unchanged, empty, invalid, n, SE or interval.
Row columns: system, org, organizer row, adapter, open weights, license,
checked mark, declared exposure, gated download flag, run date, link to the
run folder.

Hosted table (D10): the same columns plus `api_model_id`, run date, expiry
flag, nondeterministic flag.

Human-ceiling row (§6.10), latency table per run (§6.13), retired-items list
from `ERRATA.md`.

## 11. Governance

`GOVERNANCE.md` at the repo root holds the submission rule, the dispute
process, the conflict-of-interest statement, the retire-never-edit rule and
the external reviewer's name (D18). `SUBMITTING.md` holds the mechanics. The
dispute issue template is `.github/ISSUE_TEMPLATE/item-dispute.yml`; the row
dispute template is `row-dispute.yml` (`04` dispute process). The
generation gates, the review sheets with Cohen's κ, the discard log and the
promotion step live under `cleanupbench data` (`data/review/GUIDELINE.md`),
and `cleanupbench power` implements §7.2.

## 12. Licenses and attribution

- Code: MIT, matching the engine repository (D-S7 in `decisions.md`).
- Items: CC BY 4.0 for the bench's own items, which is compatible with the
  Disfl-QA-derived slice staying CC BY 4.0 (`03` R6).
- Disfl-QA-derived items carry, in `source.attribution`: "Derived from
  Disfl-QA (Gupta, Xu, Upadhyay, Yang and Faruqui, Findings of ACL-IJCNLP
  2021), CC BY 4.0 as asserted in the repository README and Hugging Face
  dataset card; the repository has no LICENSE file and was archived on
  2026-04-19. Inputs lower-cased and de-punctuated by Cleanup Bench; the
  original question is the reference." (D21)
- S1-mini rows print "S1-mini" by "Superwhisper" (Apache 2.0 with a naming
  clause, `05` §2).
- SimpleWords v3 rows: Apache-2.0, `gated-download` flag until D11 is acted
  on.
- The Whisper and Open ASR normalizers are cited as the filler inventory only;
  no code is copied.

## 13. Build plan

`docs/PROMPT.md` Part 3, one phase per PR: scaffold; scorer with pinned tests
and first items; adapters and the SimpleWords rows; dataset v1; site and tag.
The Mac Studio runbook (`docs/MAC_STUDIO_RUNBOOK.md`) carries the commands
for the rows that need a model.

## 14. Open for the owner

1. Every provisional row in `docs/decisions.md`, D15 and D17 first.
2. The external reviewer's name (D18).
3. The minimum detectable difference per metric for §7.2.
4. Whether to act on D11 (ungate) and file the engine issue for D17.
