# 02. Metrics: how adjacent fields score faithful editing

Status: research, not spec. Access date for every source: 2026-10-24.
Findings and recommendations are under separate headings. No number below
appears unless the cited page states it. Where a page was opened but did not
contain what was looked for, that is said.

The question this file answers: which published metrics, if any, encode the
three laws of cleanup (never lose words; every edit is accounted for; when
unsure, leave it as said), what each one derives from, and what none of them
can catch.

## What was found

### 1. Grammatical error correction (GEC) scoring

GEC is the closest published analogue to cleanup: a source text, a minimally
edited target, and a scorer that compares *edits* rather than whole strings.

**The M2 (MaxMatch) scorer.** Dahlmeier and Ng (2012) frame the problem as
ambiguity of edit extraction: "the set of edits that transforms one string into
another is not necessarily unique, even at the token level", and phrase-level
edits add more ambiguity. Their example: a system inserts the article *a*, the
gold annotation is `word → {a word, words}`, and the earlier HOO scorer marks
the system wrong although its corrected sentence equals the first gold option.
MaxMatch builds a Levenshtein edit lattice between source and hypothesis and
searches for the edit sequence with "the maximum overlap with the gold
standard", then scores that sequence with F1 (as of 2012). A gold edit is a
triple of start offset, end offset and a *set* of acceptable corrections; a
system edit has a single correction. The paper bounds the number of unchanged
words an edit may absorb; the current scorer's README gives
`--max_unchanged_words` a default of 2.
[Source: https://aclanthology.org/N12-1067.pdf, accessed 2026-10-24.]

**Multiple annotators in M2.** The m2scorer README: "The final score for the
sentence will use the set of edits by an annotation set maximizing the score."
Each annotation set is identified by an annotator id, and the beta option
"Set the ratio of recall importance against precision. Default = 0.5."
[Source: https://github.com/nusnlp/m2scorer, accessed 2026-10-24.]

**Why GEC reports F0.5.** The CoNLL-2014 shared task overview states the
change explicitly: "The evaluation metric was changed from F1 to F0.5, to
emphasize precision over recall." The justification: "F0.5 emphasizes
precision twice as much as recall, while F1 weighs precision and recall
equally. When a grammar checker is put into actual use, it is important that
its proposed corrections are highly accurate in order to gain user acceptance.
Neglecting to propose a correction is not as bad as proposing an erroneous
correction." The formulas given are recall R = sum over sentences of
|gold ∩ system| divided by sum of |gold|, precision P = the same numerator
divided by sum of |system|, and F0.5 = (1 + 0.5²) × R × P / (R + 0.5² × P).
The test set was 1,312 sentences and 30,144 word tokens, annotated
independently by two annotators. The top team scored 37.33 F0.5 without
alternative answers and the best team scored 45.57 with them.
[Source: https://aclanthology.org/W14-1701.pdf, accessed 2026-10-24.]

**I-measure and the "do-nothing" problem.** Felice and Briscoe (2015) list
failures of F-score and M2 that matter for a cleanup bench: "a baseline system
that does not propose any correct edits will not produce informative results
(P = 1 by definition, R = 0 and F = 0)"; "It is not possible to discriminate
between a 'do-nothing' baseline system and other systems that only propose
wrong corrections, as they will all yield F = 0"; and "The lack of a true
negative count (i.e. the number of non-errors) precludes the computation of
accuracy". Their remedy is token-level alignment of source, hypothesis and
reference with a true-negative count, and a weighted accuracy with a weight
factor w > 1 so that a system "will have the same accuracy as the
'do-nothing' baseline, in which case we would prefer to keep the original text
and rank the system lower, in accord with the choice of F0.5 for evaluating the
2014 shared task."
[Source: https://aclanthology.org/N15-1060.pdf, accessed 2026-10-24.]

**ERRANT.** Bryant, Felice and Briscoe (2017) extract edits from a parallel
original/corrected pair with a Damerau-Levenshtein alignment whose cost
function includes "part-of-speech and lemma", which they report "proved most
effective at approximating human edits in several datasets (80-85% F1)". Edits
are classified by rules into 25 main error categories, each prefixable as
Missing, Replacement or Unnecessary. Five GEC researchers rated the predicted
types as "Good" or "Acceptable" in "at least 95% of cases" with agreement of
0.724 κ-free. The scorer is deliberately simple: "Any edit with the same span
and correction in both files is hence a true positive (TP), while unmatched
edits in the hypothesis and references are false positives (FP) and false
negatives (FN) respectively." Two points matter for a bench that receives
byte-range edits from an engine. First, the motivation for per-type scoring:
"a system that performs poorly overall may in fact outperform others at
specific error types." Second, reference processing: "a hypothesis edit
[have eating → has eaten] will not match the reference edits [have → has] and
[eating → eaten] because the former is one edit while the latter is two edits,
even though they equate to the same thing", so they re-extract reference edits
with the same tool: "it is especially important that the hypothesis and
references are both processed in the same way."
[Source: https://aclanthology.org/P17-1074.pdf, accessed 2026-10-24.]

The ERRANT README adds the operational details: `errant_compare` evaluates
"span-based correction" by default, "span-based or token-based detection" with
flags, reports "Precision, Recall and F-score (default: F0.5)" with TP/FP/FN
counts, and defines a *noop* edit as "a special kind of edit that explicitly
indicates an annotator/system made no changes", required "whenever at least 1
out of n annotators considered the original sentence" correct.
[Source: https://github.com/chrisjbryant/errant, accessed 2026-10-24.]

**GLEU and the human ranking.** Napoles et al. (2015) ran the first human
evaluation of GEC outputs (three native speakers, 28,146 pairwise judgments
over the CoNLL-2014 systems plus source and reference) and report that M2 and
I-measure rankings "do not correlate well with this ground truth"; they cite a
negative Pearson correlation between M2 and BLEU (r = −0.772) and between M2
and I-measure (r = −0.694). Two of their criticisms of M2 transfer directly to
cleanup. One: "phrase-level edits can be gamed because the lattice treats a
long phrase deletion as one edit", with the footnote that outputting a single
character "X" for every sentence "would be ranked 6/13 systems in the 2014
CoNLL shared task" (P = 0.27, R = 0.29, M2 = 0.28). Two: "the F-score does not
capture the difference between 'no change' and 'wrong edits' made by systems."
GLEU itself modifies BLEU's n-gram precision "to assign extra weight to n-grams
present in the candidate that overlap with the reference but not the source"
and penalises "n-grams in the candidate that are in the source but not the
reference", with a weight λ for incorrectly changed n-grams. The authors note
"there is still room for further work as there is a gap in how well it
correlates with human judgments."
[Source: https://aclanthology.org/P15-2097.pdf, accessed 2026-10-24.]

### 2. Multi-reference handling and annotator agreement

**CoNLL-2014's two annotators and alternative answers.** Agreement between the
two annotators on *which words needed correction* was Cohen's kappa 0.43,
which the organisers call moderate and defend: "the Kappa coefficient does not
take into account the fact that there is often more than one valid way to
correct a sentence." Per-annotator scoring showed large swings: one system's
precision "was 70% for Annotator 2 but only 28% for Annotator 1". Teams were
allowed to "propose alternative answers (gold-standard edits)" within four days
of seeing the annotations, but the organisers then recommend future work "not
use alternative answers, to ensure a fairer evaluation. This is because the
scores of the teams which submitted alternative answers tend to be higher in a
biased way when evaluated with alternative answers."
[Source: https://aclanthology.org/W14-1701.pdf, accessed 2026-10-24.]

**The human ceiling.** Bryant and Ng (2015) collected ten annotators'
corrections of the 50 CoNLL-2014 test essays and conclude that inter-annotator
agreement statistics "are less informative in fields where there may be more
than one correct answer": for one sentence, "not one single annotator agreed
with another exactly." Scoring each human against the other nine gives an upper
bound; the abstract says "even humans are unable to score higher than 75%
F0.5", the conclusion puts the bound at "roughly 73% F0.5", and the top three
CoNLL-2014 systems "perform, on average, between 67-73% as reliably as this
human upper bound." They also report that "both system and human performance
increases as more annotators are used in a gold standard", and propose
reporting system score as a ratio to the human score for the same reference
set.
[Source: https://aclanthology.org/P15-1068.pdf, accessed 2026-10-24.]

**JFLEG's four fluency references.** JFLEG re-annotated 1,511 sentences with
"four human-written corrections which contain holistic fluency rewrites instead
of just minimal edits", collected on Amazon Mechanical Turk from 50 qualified
participants. The paper's own statistics table shows that 86% of JFLEG
sentences were changed, with a mean Levenshtein distance of 13, against 38% and
6 for NUCLE. The explicit goal was to move GEC "beyond minimal error
corrections." This is the opposite of the cleanup laws, and it is the only GEC
benchmark that rewards rewriting; it is listed here as the model of what
*not* to copy.
[Source: https://aclanthology.org/E17-2037.pdf, accessed 2026-10-24.]

### 3. WER and its normalizers

**Definition.** The Hugging Face `evaluate` metric card gives
WER = (S + D + I) / N = (S + D + I) / (S + D + C), where S, D, I are
substitutions, deletions and insertions, C the correct words, and N the
reference length, with 0 as the perfect score.
[Source: https://github.com/huggingface/evaluate/blob/main/metrics/wer/README.md,
accessed 2026-10-24.] The jiwer library exposes the decomposition directly:
`WordOutput` carries `hits`, `substitutions`, `deletions`, `insertions` and the
alignments, alongside WER, MER, WIL and WIP.
[Source: https://jitsi.github.io/jiwer/reference/process/, accessed
2026-10-24; the usage page https://jitsi.github.io/jiwer/usage/ and the README
https://github.com/jitsi/jiwer were also opened and contain no formula.]

**Whisper's English normalizer.** The Whisper paper justifies normalisation as
"a best-effort attempt to penalize only when a word error is caused by actually
mistranscribing a word, and not by formatting or punctuation differences." The
twelve steps include: remove phrases in brackets and parentheses; "Remove any
of the following words: hmm, mm, mhm, mmm, uh, um"; expand contractions;
"Remove periods (.) not followed by numbers"; remove symbols and diacritics in
Unicode categories M, S or P except period, percent and currency; convert
numeric expressions to digits ("Ten thousand dollars" → "$10000"); American
spellings; collapse whitespace. The authors observe "WER drops of up to 50
percent usually due to a quirk such as a dataset's reference transcripts
seperating contractions from words with whitespace", and "caution this
development procedure comes at a risk of overfitting to the transcription style
of Whisper models", which they test in Section 4.4 against the FairSpeech
normalizer. They add: "We do not claim that the text format resulting from the
above is more 'correct' in any measure."
[Source: https://arxiv.org/pdf/2212.04356, accessed 2026-10-24.] The code
confirms the filler regex `\b(hmm|mm|mhm|mmm|uh|um)\b`, lowercasing first, and
the period and symbol handling.
[Source: https://github.com/openai/whisper/blob/main/whisper/normalizers/english.py,
accessed 2026-10-24.]

**The Open ASR Leaderboard's normalizer.** Its paper says the pipeline
"applies an English text normalization pipeline closely following that of
Whisper", because "Not all models produce transcripts with punctuation, casing,
or disfluencies", so they "normalize all text prior to computing WER"; the
normalisation "removes punctuation and casing" plus fillers, numbers and
spellings. Section 4 notes that "models vary in how they handle disfluencies".
RTFx is defined as total audio duration divided by transcription time. The
leaderboard covers 86 systems across 12 datasets.
[Source: https://arxiv.org/html/2510.06961 and https://arxiv.org/abs/2510.06961,
accessed 2026-10-24.] The normalizer source is headed "Most of the code is copy
pasted from the original whisper repository", Apache-2.0, and *extends* the
filler list with patterns such as `a+h+m*`, `u+m+h*`, "ahem", "mmkay", "hum",
"hunh", "mhum".
[Source: https://raw.githubusercontent.com/huggingface/open_asr_leaderboard/main/normalizer/normalizer.py,
accessed 2026-10-24. The repository README
https://github.com/huggingface/open_asr_leaderboard and the Space pages were
also opened; neither states the normalizer rationale.]

What this means for cleanup: the standard ASR normalizer deletes fillers,
casing and punctuation before scoring. Those are three of the eleven
hypothesised cleanup categories. A normalized WER between a cleanup output and
a reference is blind to exactly the work being measured, and an unnormalized
WER penalises every legitimate punctuation variant. The GenSEC organisers hit
the same wall and report both: "normalized and unnormalized (punctuation and
capitalization) WER" (see §4).

### 4. Hallucination and omission in ASR and ASR post-editing

**ASR hallucination.** Koenecke et al. (2024) found that "roughly 1% of audio
transcriptions contained entire hallucinated phrases or sentences" from
Whisper, that "38% of hallucinations include explicit harms such as
perpetuating violence, making up inaccurate associations, or implying false
authority", and that hallucinations "disproportionately occur for individuals
who speak with longer shares of non-vocal durations" (speakers with aphasia
versus a control group). The method was thematic analysis of hallucinated
content against ground truth, not a reusable metric.
[Source: https://arxiv.org/abs/2402.08021, accessed 2026-10-24; the ACM DL page
https://dl.acm.org/doi/10.1145/3630106.3658996 returned HTTP 403.]

**LLM-based ASR error correction.** HyPoradise provides "more than 334,000
pairs of N-best hypotheses and corresponding accurate transcriptions", scores
by WER, and reports that an LLM "can even correct those tokens that are missing
in N-best list", which is the generative capability that cleanup must bound.
[Source: https://arxiv.org/abs/2309.15701, accessed 2026-10-24.] The GenSEC
challenge's Task 1 uses the same corpus (316,881 training and 17,383 test
pairs, to be released under MIT), evaluates with WER ("The WER of the corrected
hypotheses is used for evaluation"), reports normalized and unnormalized WER,
and warns in general terms that "LLMs could produce enriched text that diverges
from the intended meaning or introduces new types of errors", calling for
"novel error analysis methodologies" without defining one.
[Source: https://arxiv.org/html/2409.09785, accessed 2026-10-24.]

Min and Wang (2023) report that LLM corrections of ASR output "frequently
resulted in higher Word Error Rates (WER)".
[Source: https://arxiv.org/abs/2307.06530, accessed 2026-10-24.] Fang et al.
(2025) define hallucination as responses that "while grammatically correct,
fluent, and plausible, deviate from the input or contradict factual
information", note that "general LLMs often generate hallucinations, producing
more errors than corrections", and give a qualitative taxonomy of faithful
versus factual hallucinations (instruction violation, redundant output,
continued writing, blank output, repetition, unrequested grammar correction).
They report no hallucination rate; the closest quantitative statement is that
on one test set "383 erroneous sentences were corrected, whereas 98 originally
correct sentences were mistakenly altered to erroneous forms." Their
verification stage checks format conformance and reasoning completeness, and
keeps the original input otherwise.
[Source: https://arxiv.org/html/2505.24347v3, accessed 2026-10-24.] Yamamoto
et al. (2025) attribute "over-correction" to text-only correction "neglecting
phonetic cues".
[Source: https://arxiv.org/abs/2505.17410, accessed 2026-10-24.]

**Not found:** a published, named "over-correction rate", "fabrication rate"
or "omission rate" for ASR post-editing. Searches run: "LLM generative error
correction ASR over-correction hallucination rate metric paper"; "LLM-as-a-judge
fluency bias prefers fluent text over faithful text evaluation paper". The
literature measures these effects through WER and through counts of
originally-correct sentences made wrong.

### 5. Meaning-preservation checks and their documented biases

**NLI-based.** Maynez et al. (2020) found "substantial amounts of hallucinated
content in all model generated summaries" and that "textual entailment measures
better correlate with faithfulness than standard metrics".
[Source: https://arxiv.org/abs/2005.00661, accessed 2026-10-24.] SummaC
attributes earlier NLI failures to "a mismatch in input granularity between NLI
datasets (sentence-level), and inconsistency detection (document level)" and
fixes it by "segmenting documents into sentence units and aggregating scores
between pairs of sentences", reaching balanced accuracy of 74.4% on its
benchmark.
[Source: https://aclanthology.org/2022.tacl-1.10/, accessed 2026-10-24.]

**Embedding-based.** BERTScore "computes a similarity score for each token in
the candidate sentence with each token in the reference sentence" using
contextual embeddings.
[Source: https://arxiv.org/abs/1904.09675, accessed 2026-10-24.] Hanna and
Bojar (2021) find it "can detect when a candidate differs from a reference in
important content words" but "is less sensitive to smaller errors, especially
if the candidate is lexically or stylistically similar to the reference", which
describes the cleanup case (a one-token meaning flip inside an otherwise
identical sentence) exactly.
[Source: https://aclanthology.org/2021.wmt-1.59/, accessed 2026-10-24.]

**LLM-as-judge.** Zheng et al. (2023) name "position, verbosity, and
self-enhancement biases" and "limited reasoning ability", while reporting that
strong judges reach "over 80% agreement, the same level of agreement between
humans".
[Source: https://arxiv.org/abs/2306.05685, accessed 2026-10-24.] Wang et al.
(2023) show the ranking "can be easily hacked by simply altering their order of
appearance in the context": "Vicuna-13B could beat ChatGPT on 66 over 80 tested
queries with ChatGPT as an evaluator", and propose multiple-evidence and
balanced-position calibration.
[Source: https://arxiv.org/abs/2305.17926, accessed 2026-10-24.] Saito et al.
(2023) define verbosity bias as LLMs that "prefer more verbose answers even if
they have similar qualities" and find "GPT-4 prefers longer answers more than
humans".
[Source: https://arxiv.org/abs/2310.10076, accessed 2026-10-24.] Panickssery
et al. (2024) document self-preference, "where an LLM evaluator scores its own
outputs higher than others'", and "a linear correlation between
self-recognition capability and the strength of self-preference bias".
[Source: https://arxiv.org/abs/2404.13076, accessed 2026-10-24.] Zhou et al.
(2024) state that "existing judges are proven to be biased, namely they would
favor answers which present better superficial quality (such as verbosity,
fluency) while ignoring the instruction following ability", and propose
calibration for closed judges and contrastive training for open ones.
[Source: https://aclanthology.org/2024.ccl-1.101/, accessed 2026-10-24.] Chen
et al. (2024) add misinformation-oversight, gender, authority and beauty biases
and find "human and LLM judges are vulnerable to perturbations to various
degrees."
[Source: https://arxiv.org/abs/2402.10669, accessed 2026-10-24.] G-Eval's
authors themselves "highlight the potential issue of LLM-based evaluators
having a bias towards the LLM-generated texts."
[Source: https://arxiv.org/abs/2303.16634, accessed 2026-10-24.]

The fluency-preference finding (Zhou et al.) is the one that matters most
here: a cleanup judge that prefers fluent output rewards the exact failure the
bench exists to expose.

### 6. Metrics borrowable from neighbouring tasks

**SARI (text simplification).** SARI "principally compares system output
against references and against the input sentence. It explicitly measures the
goodness of words that are added, deleted and kept by the systems." Its Venn
diagram partitions output n-grams into: input unchanged by the system and not
in the reference; input retained in references but deleted by the system;
overlap of all three; input correctly deleted and replaced by reference
content; and "potentially incorrect system output" (in the output but in
neither input nor reference). The paper argues BLEU "does not take into
account anything about the differences between the input and the references"
and "gives too much latitude for matching the input"; SARI was evaluated with
eight references and the authors report significant sentence-level correlation
with human ratings on all three of their criteria (grammaticality, meaning
preservation, simplicity), while BLEU "fail[s] to measure the most important
aspect of simplification – simplicity."
[Source: https://aclanthology.org/Q16-1029.pdf, accessed 2026-10-24.] The
regions "input retained in the references but deleted by the system" and
"output in neither input nor reference" are the two cleanup laws (never lose
words; never invent) expressed as sets. SARI itself rewards additions, which
cleanup must not; only its partition is reusable.

**Disfluency detection F-score (Switchboard).** The standard metric is
precision, recall and F-score over disfluent (EDITED, i.e. reparandum) words
on Penn Treebank-3 Switchboard, with "partial words, 'XX' tags, and
punctuation" removed; filled pauses and discourse markers are INTJ and PRN
nodes. Jamshid Lou and Johnson (2020) report EDITED-word F of 90.6 for an
ensemble and 89.2 for a single model. This is a *detection* metric: it asks
which input tokens should be removed and never looks at what replaces them.
[Source: https://arxiv.org/html/2004.05323v2 and https://arxiv.org/abs/2004.05323,
accessed 2026-10-24.]

### 7. Not found

- A published metric for "every edit is accounted for" (edits returned as
  ranges that reconstruct the output). This is a software contract, not a
  scoring tradition; nothing comparable was found in GEC, ASR or simplification
  evaluation. Searches: the GEC and ASR sources above, plus the two searches in
  §4.
- A human-ceiling study for dictation cleanup or disfluency *removal* (as
  opposed to detection). Bryant and Ng (2015) is the only ceiling study found,
  and it is for GEC.
- Any LLM-as-judge bias study specific to ASR post-editing or disfluency
  removal. All judge-bias sources found are on general chat or summarisation.

## What is recommended

### Does the F0.5 logic transfer to "under-clean rather than over-clean"?

Yes, and for the same reason the CoNLL organisers gave: "Neglecting to propose
a correction is not as bad as proposing an erroneous correction." In cleanup a
false-positive edit is a word lost, a word invented or a meaning changed; a
false-negative edit is a filler left in. The third law ("when unsure, leave it
as said") is the dictation restatement of that sentence, so β = 0.5 is the
published precedent, not an invention. Two refinements from the literature:

1. Precision and recall must be published as separate columns, never only the
   F. CoNLL-2014's per-annotator table shows precision swinging from 28% to
   70% for one system across annotators; a single F hides whether a system is
   under- or over-cleaning, which is the one thing a reader of this bench needs
   to know.
2. F0.5 alone cannot separate identity from a system that only makes wrong
   edits (both F = 0, per Felice and Briscoe and per Napoles et al.). The bench
   therefore needs the hard-constraint rates below *alongside* F, exactly as
   I-measure added a true-negative count. The identity baseline row makes this
   visible: it has F = 0 and zero word loss, and any row with F = 0 and
   non-zero word loss is worse than doing nothing.

### Recommended metric set

All metrics are computed per category and never pooled (confirmed by ERRANT's
motivation that a system "that performs poorly overall may in fact outperform
others at specific error types", and by the vault's finding that an aggregate
hid a category scored 0/5). Where an item has several references, each metric
takes the per-item best reference, which is the M2 rule ("the set of edits by
an annotation set maximizing the score"). Tokenisation and the normaliser used
for each metric are part of the metric's definition and must be pinned in the
scorer.

| # | Metric | Formula in words | Published parent | Law it encodes | What it cannot catch |
|---|---|---|---|---|---|
| 1 | **Edit precision, recall, F0.5** (headline per category) | Extract token-level edits from (input, output) and from (input, each reference) with the *same* aligner; an output edit is a TP when its span and replacement match a reference edit; P = TP/(TP+FP), R = TP/(TP+FN), F0.5 per the CoNLL-2014 formula; best reference per item. | M2 (Dahlmeier and Ng 2012) and ERRANT (Bryant et al. 2017), with CoNLL-2014's β. | Law 3 (precision weighted) | Legitimate edits absent from every reference (Bryant and Ng); a long deletion counted as one edit (Napoles et al.), which is why metric 3 exists. |
| 2 | **Normalized exact match** (secondary) | Output equals any reference after a fixed normaliser (whitespace, Unicode form; *not* the Whisper normaliser, which deletes the work). | Sentence-level accuracy as used in GEC reporting; the normaliser idea from Whisper's Appendix C. | All three, coarsely | Everything about *how* an item failed; harsh under legitimate variation, hence secondary. |
| 3 | **Word-loss rate** (hard constraint) | Content tokens present in the best reference but absent from the output, divided by reference content tokens, computed after an ASR-style normaliser so casing and punctuation do not count. Equivalent to the deletion component D of WER(output vs reference) restricted to content tokens. | WER's D term (jiwer `deletions`; HF `evaluate` formula); SARI's region "input retained in the references but deleted by the system". | Law 1 | A word *replaced* by a wrong word of the same length (that is a substitution, caught by metric 1 and 4). |
| 4 | **Insertion rate** (hard constraint) | Output content tokens present in neither the input nor any reference, divided by output content tokens. | WER's I term; SARI's region "potentially incorrect system output"; HyPoradise's "tokens that are missing in N-best list" named as the risk. | Law 1 (never invent) and Law 3 | Insertions that happen to be in the input elsewhere (a duplicated word), which metric 1 catches as an FP edit. |
| 5 | **Slot failure rate** | Fraction of items where a `must_contain` phrase is missing or a `must_not_contain` phrase is present in the normalised output. | No published parent found; closest is ERRANT's detection scoring (did the system act on the right span) without a correction string. | Laws 1 and 3 | Anything outside the slots; trivially satisfiable by an output that is only the `must_contain` words, so it must never be the only metric (metric 3 and 1 close that hole). |
| 6 | **Over-clean rate on negatives** | On items whose reference equals the input (ERRANT's *noop* convention), fraction whose normalised output differs from the normalised input in content tokens. | I-measure's true-negative argument; ERRANT noop edits. | Law 3 | Over-cleaning on positive items (that is a precision loss in metric 1). |
| 7 | **Fallback rate, unchanged rate** (status columns, not scores) | Fraction of items returning `.fallback(reason)` and `.unchanged` from the engine contract, or output == input for adapters without outcomes. | No published parent; the engine's outcome contract. | Law 3 (a fallback is "leave it as said") | Whether the fallback was warranted; read together with metrics 1 and 3. |
| 8 | **Edit accountability** (validity gate, pass/fail) | When a system returns edits, applying them to the input's UTF-8 bytes must reproduce the output byte for byte, with ordered, non-overlapping, scalar-boundary ranges; a failure invalidates the row for that item. | No published parent; the engine's `docs/contract.md` and `docs/cloud.md` requirement of "exact byte reconstruction". | Law 2 | Whether the edits are *minimal* or editorially meaningful; the engine itself emits one contiguous replacement, so metric 1 must re-extract token edits rather than trust returned spans (ERRANT's "processed in the same way" rule). |
| 9 | **Human-ceiling row** (context, where ≥2 references exist) | Score reference 2 as if it were a system against reference 1 on metrics 1 to 4. | Bryant and Ng (2015) human-versus-human F0.5. | None; it bounds the others | Items with one reference. |

Latency stays off the leaderboard in a per-run table with hardware named; the
Open ASR Leaderboard's RTFx (audio duration over processing time) is the
precedent for reporting speed next to, not inside, the quality score.

### Meaning-preservation checks: diagnostic, not scored

- **NLI** is asymmetric: a cleaned text that silently drops a clause is still
  entailed by its input, so entailment cannot see omission (law 1). It can see
  contradiction, which is the self-correction case where the superseded value
  survives. Recommended use: a *bidirectional* sentence-level entailment check
  (SummaC's granularity finding) run as a diagnostic that flags items for human
  review, never as a leaderboard column.
- **Embedding similarity** is documented as insensitive to small errors when
  the candidate is lexically similar to the reference (Hanna and Bojar), which
  is every cleanup failure worth catching. Not recommended.
- **LLM-as-judge** carries position, verbosity, self-preference and fluency
  biases with published magnitudes (Wang et al.; Saito et al.; Panickssery et
  al.; Zhou et al.). The fluency bias is directly adversarial to this bench.
  Recommended: no judge in the scorer. If a judge is used anywhere, it is in
  item *generation* gates (file 03), with balanced-position calibration, and
  never from the same model family as a system on the board.

### The appendix hypothesis, metric by metric

| Hypothesis | Verdict | Why |
|---|---|---|
| Normalized exact match | Refine | Keep as secondary; define the normaliser in the spec and make it *not* strip casing or punctuation (the Whisper normaliser would erase the task). |
| Token-edit precision, recall and F-score against reference-implied edits | Confirm and sharpen | This is M2/ERRANT scoring. Fix β = 0.5 with the CoNLL-2014 justification; re-extract edits for output and reference with one aligner; publish P and R as columns. |
| Word-loss rate | Confirm | Derives from WER's D term and SARI's deleted-but-retained region; compute against the reference, not the input, so that reference-sanctioned deletions (fillers) are not losses. |
| Insertion rate | Confirm | WER's I term restricted to tokens absent from input and references. |
| Slot failure rate | Confirm as a gate, reject as a headline | No published parent; gameable in isolation. |
| Over-clean rate on negatives | Confirm | ERRANT noop convention plus I-measure's true-negative argument. |
| Fallback and unchanged rates | Confirm as status columns | Needed so identity and always-fallback rows are legible (Felice and Briscoe). |
| Latency off the leaderboard | Confirm | Open ASR Leaderboard reports RTFx separately. |
| Metrics per category, never pooled | Confirm | ERRANT's motivation and the vault's own 0/5 finding. |
| (not in the appendix) Edit accountability | Add | Law 2 has no metric in the hypothesis; the engine contract supplies one. |
| (not in the appendix) Human-ceiling row | Add | Without it, the F0.5 numbers have no scale (Bryant and Ng). |

### What none of these can catch

- A meaning change that keeps every token: reordering, or moving a negation
  across a clause boundary. Metric 1 sees an edit, but whether it is a TP
  depends on the references containing the same reordering.
- A correct output that none of the references anticipated. Bryant and Ng show
  that ten humans did not agree exactly on a single sentence; with one to three
  references, some correct outputs will score as FP edits. The human-ceiling
  row bounds this but does not remove it.
- Register and tone changes that preserve content tokens (contractions
  expanded, "gonna" to "going to"). Whether these are edits or violations is
  a reference-writing decision, not a scorer decision.
- Whether a fallback was the *right* call. The status columns count it; nothing
  scores it.
- Everything that happens before the raw transcript. The bench scores cleanup
  of a given input; recognizer errors in the input are part of the item.

### Conflicts with the vault's reasoning, stated for decision

1. **Slot checks as the pass criterion.** The vault's eval and the app's
   `eval_cleanup_v2.py` score an item as pass/fail on `must_contain`,
   `must_not_contain` and a guard. The GEC literature scores edits against
   references with P, R and F0.5 and shows that pass/fail against one
   annotator's view understates systems (Bryant and Ng) and that annotators
   disagree on what needs correcting (kappa 0.43). Slot-only scoring is also
   trivially gameable by an output containing only the required words. The
   recommendation keeps slots as a gate and adds reference-based edit scoring
   as the headline. This changes what "100% on eight categories" means and the
   owner should decide whether the public bench inherits the slot criterion,
   the reference criterion, or both.
2. **The length-ratio guard.** The vault records that a flat 0.30 length floor
   rejected a correct self-correction at ratio 0.277 and admitted the wrong
   output at 0.308. A guard is a production safety device, not a metric; the
   recommendation is that the scorer never applies any guard, and that the
   Pomvox LocalServer adapter's guard rejections surface as `.fallback` in the
   status columns so the cost of the guard is visible rather than hidden.
3. **Homophone policy.** The vault states that unambiguous homophones are fixed
   on purpose ("their were" → "There were"), overriding the app's original
   rule. Under metric 1 this is a TP only if the references fix it too; under
   metric 3 it is not a word loss because word loss is measured against the
   reference. The reference-writing guideline must take a position, and that is
   an owner decision (file 03 and the spec).
4. **Violations discarded, not repaired.** The vault applies this to corpus
   generation. The scorer analogue is metric 8: an item whose returned edits do
   not reconstruct the output is invalid for that row, not patched. No
   conflict; stated for completeness.
5. **Per-category scoring.** No conflict; the GEC literature independently
   motivates it.

## Sources

Every page below was opened on 2026-10-24.

- https://aclanthology.org/N12-1067.pdf — Dahlmeier and Ng 2012, the M2 scorer: edit lattice, gold edit as a set of corrections, F1 at the time.
- https://github.com/nusnlp/m2scorer — m2scorer README: per-sentence best annotation set, beta default 0.5, max_unchanged_words default 2, M2 file format.
- https://aclanthology.org/W14-1701.pdf — CoNLL-2014 overview: F0.5 rationale and formula, two annotators, kappa 0.43, alternative answers and the recommendation against them, test set size, per-annotator precision swing.
- https://aclanthology.org/W14-1701/ — CoNLL-2014 landing page; abstract not rendered, used only to reach the PDF.
- https://aclanthology.org/N15-1060.pdf — Felice and Briscoe 2015, I-measure: do-nothing baseline indistinguishable at F = 0, true negatives, weighted accuracy with w > 1.
- https://aclanthology.org/N15-1060/ — I-measure landing page; abstract not rendered, used only to reach the PDF.
- https://aclanthology.org/P17-1074.pdf — Bryant, Felice and Briscoe 2017, ERRANT: alignment with POS and lemma costs, 25 types, rater agreement, TP/FP/FN scorer, re-processing references with the same tool.
- https://github.com/chrisjbryant/errant — ERRANT README: errant_compare modes, default F0.5, noop edits, M2 format fields.
- https://aclanthology.org/P15-2097.pdf — Napoles et al. 2015, GLEU: human ranking of CoNLL-2014 systems, M2 gaming footnote, no-change versus wrong-edit criticism, GLEU formula.
- https://aclanthology.org/P15-1068.pdf — Bryant and Ng 2015: ten annotators, human ceiling of roughly 73% F0.5, scores rise with more references, ratio-to-human proposal.
- https://aclanthology.org/E17-2037.pdf — JFLEG: 1,511 sentences, four fluency references each, Mechanical Turk, 86% of sentences changed.
- https://aclanthology.org/E17-2037/ — JFLEG landing page; abstract only.
- https://github.com/huggingface/evaluate/blob/main/metrics/wer/README.md — WER formula and term definitions.
- https://jitsi.github.io/jiwer/reference/process/ — jiwer WordOutput attributes (hits, substitutions, deletions, insertions).
- https://jitsi.github.io/jiwer/usage/ — jiwer usage; no formula, confirms transforms exist.
- https://github.com/jitsi/jiwer — jiwer README; names measures, points to Morris et al. 2004, no formula.
- https://www.isca-archive.org/interspeech_2004/morris04_interspeech.html — Morris, Maier and Green 2004 abstract: WER as cost of restoring the output to the input; MER and WIL definitions in prose.
- https://arxiv.org/pdf/2212.04356 — Whisper paper: Section 3 normalisation rationale, Section 4.4 overfitting caution, Appendix C step list and filler words.
- https://github.com/openai/whisper/blob/main/whisper/normalizers/english.py — Whisper EnglishTextNormalizer code: filler regex, contraction expansion, period and symbol handling.
- https://arxiv.org/abs/2510.06961 — Open ASR Leaderboard paper abstract: 86 systems, 12 datasets, WER and RTFx standardised.
- https://arxiv.org/html/2510.06961 — Open ASR Leaderboard paper body: normalisation "closely following that of Whisper", reason, what it removes, RTFx definition, disfluency caveat.
- https://github.com/huggingface/open_asr_leaderboard — leaderboard repository README: HF Jobs reproducibility, private sets; no normaliser rationale.
- https://github.com/huggingface/open_asr_leaderboard/tree/main/normalizer — normaliser directory listing.
- https://raw.githubusercontent.com/huggingface/open_asr_leaderboard/main/normalizer/normalizer.py — normaliser source: copied from Whisper, Apache-2.0, extended filler list.
- https://huggingface.co/spaces/hf-audio/open_asr_leaderboard — leaderboard Space; JS-rendered, no metric text retrievable.
- https://huggingface.co/spaces/hf-audio/open_asr_leaderboard/blob/main/README.md — Space README; metadata and citation only.
- https://arxiv.org/abs/2402.08021 — Koenecke et al. 2024, Careless Whisper: roughly 1% hallucinated transcriptions, 38% harmful, aphasia population.
- https://dl.acm.org/doi/10.1145/3630106.3658996 — Careless Whisper at ACM DL; HTTP 403, not readable.
- https://arxiv.org/abs/2309.15701 — HyPoradise: 334,000+ N-best pairs, WER, LLMs correct tokens missing from N-best.
- https://arxiv.org/html/2409.09785 — GenSEC challenge: Task 1 WER, normalized and unnormalized, HyPoradise sizes and MIT licence, "diverges from the intended meaning" warning.
- https://arxiv.org/abs/2307.06530 — Min and Wang 2023: LLM corrections frequently raised WER.
- https://arxiv.org/html/2505.24347v3 — Fang et al. 2025: hallucination definition and taxonomy, 98 correct sentences made wrong, verification stage, no hallucination rate.
- https://arxiv.org/abs/2505.17410 — Yamamoto et al. 2025: over-correction from neglecting phonetic cues.
- https://arxiv.org/abs/2104.00102 — opened by mistake while looking for Raunak et al. 2021; it is an economics paper and contributed nothing.
- https://arxiv.org/abs/2005.00661 — Maynez et al. 2020: hallucination in summaries, entailment correlates with faithfulness.
- https://aclanthology.org/2022.tacl-1.10/ — SummaC: sentence-level NLI granularity, 74.4% balanced accuracy.
- https://arxiv.org/abs/1904.09675 — BERTScore abstract: token similarity with contextual embeddings.
- https://aclanthology.org/2021.wmt-1.59/ — Hanna and Bojar 2021: BERTScore insensitive to small errors when candidate is lexically similar.
- https://arxiv.org/abs/2306.05685 — Zheng et al. 2023: position, verbosity, self-enhancement biases; over 80% agreement.
- https://arxiv.org/abs/2305.17926 — Wang et al. 2023: position bias magnitude (66 of 80), calibration methods.
- https://arxiv.org/abs/2310.10076 — Saito et al. 2023: verbosity bias definition, GPT-4 prefers longer answers more than humans.
- https://arxiv.org/abs/2404.13076 — Panickssery et al. 2024: self-preference and its link to self-recognition.
- https://aclanthology.org/2024.ccl-1.101/ — Zhou et al. 2024: judges favour verbosity and fluency over instruction following; calibration and contrastive training.
- https://arxiv.org/abs/2402.10669 — Chen et al. 2024: misinformation-oversight, gender, authority, beauty biases.
- https://arxiv.org/abs/2303.16634 — G-Eval: Spearman 0.514 on summarisation, bias toward LLM-generated text.
- https://aclanthology.org/Q16-1029.pdf — Xu et al. 2016, SARI: compares against input and references, add/keep/delete partition, eight references, BLEU's latitude for matching the input.
- https://aclanthology.org/Q16-1029/ — SARI landing page; abstract only.
- https://arxiv.org/html/2004.05323v2 — Jamshid Lou and Johnson 2020 body: Switchboard EDITED-word P/R/F, preprocessing, F 90.6 and 89.2.
- https://arxiv.org/abs/2004.05323 — same paper, abstract only.
