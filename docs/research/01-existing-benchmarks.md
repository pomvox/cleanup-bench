# 01 · Existing benchmarks and datasets near dictation cleanup

Scope: everything found that measures something close to cleanup, the job of
turning raw recognizer output into what the speaker meant. Each item is held
against the three laws (never lose words; every edit accounted for; when
unsure, leave it as said). Findings and recommendations are under separate
headings. Every claim carries the URL that was opened and the access date; all
pages were opened on 2026-10-24. Where a page did not state a number, no
number is given.

---

## What was found

### 1. Switchboard disfluency annotation and the detection literature

**What it is.** The Switchboard-1 Release 2 corpus (LDC97S62) "consists of
approximately 260 hours of conversational telephone speech" in "around 2,400
two-sided telephone conversations among 543 speakers" ([LDC97S62](https://catalog.ldc.upenn.edu/LDC97S62)).
A subset was annotated for disfluencies under the Penn Treebank project and is
distributed in Treebank-3 (LDC99T42), which lists "Switchboard tagged,
dysfluency-annotated, and parsed text" among its contents
([LDC99T42](https://catalog.ldc.upenn.edu/LDC99T42)). Jamshid Lou and
Johnson (2020) describe this subset as "1,126 conversations were hand-annotated
with disfluencies as part of the Penn Treebank Release 3 dataset"
([arXiv 2009.10298 PDF](https://arxiv.org/pdf/2009.10298)); the NXT Switchboard
project describes it as "A subset of one million words from this corpus was
annotated for syntactic structure and disfluencies"
([NXT overview](https://groups.inf.ed.ac.uk/switchboard/overview.html)). The
LDC catalog page itself states neither conversation nor word count.

**Annotation scheme.** The Meteer et al. stylebook (February 1995, revised June
1995) defines the markup. Its introduction states the goal: "When sentences are
separated, the restarts folded and the non-sentence elements removed, what
remains should be reasonably grammatical sentences." It defines three
non-sentence element classes and a restart structure:

- Filled pauses `{F ...}`: "Filled pauses have unrestricted distribution and
  no semantic content. A few common examples are uh, um, huh."
- Explicit editing terms `{E ...}`: "have some semantic content (e.g. I mean,
  sorry, excuse me) and usually occur between the restart and the repair."
- Discourse markers `{D ...}`: "have a wider distribution than explicit
  editing phrases but have more semantic content than fillers"; "the two most
  common and easily recognized discourse markers are well and you know"; the
  guide notes that "Like can be a preposition or a discourse marker.
  Unfortunately distinguishing the two can be difficult."
- Restarts `[RM + {..} RR]`: reparandum, interruption point `+`, optional
  interregnum, repair; with sub-types "restarts with repair", "restarts w/o
  repair" (`[RM+]`) and "complex restarts".

([Meteer et al. stylebook, Brandeis copy](https://www.cs.brandeis.edu/~cs140b/CS140b_docs/DyfluencyGuide.pdf)).
The stylebook also says of its own cleaned example: "the cleaning of the
annotated example is just an indication of what could be done and not
necessarily what will be done", i.e. the corpus annotates structure, it does
not ship a canonical cleaned reference.

The reparandum / interruption point / interregnum / repair terminology is
credited to Shriberg (1994); the thesis itself was not found online (see "Not
found"). Zayats, Ostendorf and Hajishirzi (2016) restate it as
"[reparandum + {interregnum} repair]" and categorize disfluencies by "whether
the repair is empty, the same as the reparandum or" different
([arXiv 1604.03209 PDF](https://arxiv.org/pdf/1604.03209)).

**Standard split and metric.** Charniak and Johnson (2001) fixed the split
still used today: "The training subcorpus consists of all files in the
directories 2 and 3 of the parsed/merged Switchboard corpus. Directory 4 is
split into three approximately equal-size sections ... The first of these
(files sw4004.mrg to sw4153.mrg) is the testing corpus ... The files
sw4154.mrg to sw4483.mrg are reserved for future use. The files sw4519.mrg to
sw4936.mrg are the development corpus"
([ACL Anthology N01-1016 PDF](https://aclanthology.org/N01-1016.pdf)).
Jamshid Lou and Johnson (2020) restate it as "training data consists of the
sw[23]*.mrg files, dev data consists of the sw4[5-9]*.mrg files and test data
consists of the sw4[0-1]*.mrg files", give the gold training size as "SWB gold
98k [sentences] 733k [words]", and note that "All partial words and
punctuations are removed from the data, as they are not available in realistic
ASR applications" ([arXiv 2004.05323 PDF](https://arxiv.org/pdf/2004.05323)).
The metric is word-level: Zayats et al. (2016) write "performance is measured
using precision/recall of words in edit regions"; Jamshid Lou and Johnson
(2020) "report precision (P), recall (R) and f-score (F) for both constituent
spans (S) and word positions (W)", with the EDITED-word set W_E as the headline.
Charniak and Johnson (2001) report "a misclassification rate on edited words
of 2.2%" against a 5.9% baseline that marks nothing as edited.

**Form.** Input: transcribed conversational speech with partial words and
punctuation stripped. Output: a per-word label (edited / not), from which the
fluent string is derived by deletion. One reference per item (the Treebank
annotation). Interregna are annotated separately from reparanda; Charniak and
Johnson note they "approximate the Switchboard annotation convention of
annotating interregna as EDITED if they appear in iterated edits".

**License.** LDC: "LDC User Agreement for Non-Members", fee shown only after
login ([LDC99T42](https://catalog.ldc.upenn.edu/LDC99T42),
[LDC97S62](https://catalog.ldc.upenn.edu/LDC97S62)). The NXT Switchboard
Annotations (LDC2009T26) are "made available to LDC not-for-profit members and
all nonmembers under the Creative Commons Attribution-Noncommercial Share Alike
3.0 license" ([LDC2009T26](https://catalog.ldc.upenn.edu/LDC2009T26)); that
release "couples reparanda and repairs into disfluencies by pointing to the
appropriate nonterminals using named roles".

**What it cannot see.** The task is deletion-only labeling: no casing, no
punctuation (stripped), no spoken-form conversion, no insertions, no
reordering. Because it is deletion-only, "never lose words" and "every edit
accounted for" are trivially satisfied by construction and are therefore not
measured. Partial words are removed before scoring, so the recognizer-side
noise a dictation system actually sees is absent. The register is two-party
telephone conversation, not dictation.

### 2. Disfl-QA (Gupta et al., 2021)

**What it is.** "a targeted dataset for contextual disfluencies in an
information seeking setting, namely question answering over Wikipedia
passages", built on SQuAD-v2 ([GitHub README](https://github.com/google-research-datasets/Disfl-QA)).
Paper: "Disfl-QA: A Benchmark Dataset for Understanding Disfluencies in
Question Answering", Findings of ACL-IJCNLP 2021, pages 3309–3319
([ACL Anthology 2021.findings-acl.293](https://aclanthology.org/2021.findings-acl.293/)).

**How references were made.** From the paper: "Each question associated with
the paragraph is sent for a human annotation task to add a contextual
disfluency using the paragraph as a source of distractors." "Expert raters were
shown the passage along with all the associated questions and their answers
... The raters were linguistic experts, and were trained for the task with 2
rounds of pilot annotation." Constraints: the disfluent version "(a) is
semantically equivalent to the original question (b) is natural". Explicit
exclusion: "we instructed raters not to include partial words or filled pauses
(e.g., 'um', 'uh', 'ah' etc.), as they can be detected relatively easily".
"On average, raters spent 2.5 minutes per question. Introduction of a
disfluency increased the mean length of a question from 10.3 to 14.6 words."
Quality pass: a second rater pool judged consistency and naturalness; "the
second pool of raters found the disfluent questions to be consistent and
natural 96.0% and 88.5% of the time, with an inter-annotator agreement of 97.0%
and 93.0%, respectively", footnoted "Cohen's κ = 0.55, indicating moderate
agreement"; flagged items went through "a second round of re-annotation with
updated guidelines" ([arXiv 2106.04016 PDF](https://arxiv.org/pdf/2106.04016)).

**Direction of the pairs.** The fluent SQuAD question is the *source*; the
disfluent version is *written by the annotator*. So the "reference" for a
cleanup task is the original fluent question, one per item, and the disfluent
input is synthetic human-authored text, not speech or ASR output.

**Size and splits.** "We split the 11,825 annotated questions in Disfl-QA into
train/dev/test set containing 7182/1000/3643 questions, respectively" (paper);
the README lists train.json 7,182, dev.json 1,000, test.json 3,643. Each JSON
record maps a SQuAD-v2 id to `original` and `disfluent`
([GitHub README](https://github.com/google-research-datasets/Disfl-QA)). The
Hugging Face mirror shows the same three splits and the fields
`squad_v2_id`, `original question`, `disfluent question`, `title`, `context`
([HF dataset card](https://huggingface.co/datasets/google-research-datasets/disfl_qa)).

**Category distribution** (from a manual sample: "we sampled 500 questions from
the training and development sets"): Table 1 of the paper gives Interrogative
Restart 30%, Entity Correction 25.6%, Adverb/Adj. Correction 20%, Entity Type
Correction 21.1%, Others 3.3%; the paper summarizes "≈30% and >65% of the
disfluencies in Disfl-QA are restarts and corrections respectively" and
"Over 90% of the disfluencies are corrections or restarts". Table 2 contrasts
it with Switchboard: "Disfluencies 20% [Switchboard] / 100% [Disfl-QA]",
"Correction & Restarts <50% / >90%", "Coreferences <1% / ≈10%"
([arXiv 2106.04016 PDF](https://arxiv.org/pdf/2106.04016)).

**License.** The README states CC BY 4.0. There is **no LICENSE file in the
repository**: the GitHub contents API lists only `README.md`, `dev.json`,
`test.json`, `train.json`, and the API's license field is empty (checked with
`gh api repos/google-research-datasets/Disfl-QA/contents` on 2026-10-24;
`https://raw.githubusercontent.com/google-research-datasets/Disfl-QA/main/LICENSE`
returns 404). The Hugging Face card's license field is `cc-by-4.0`
([HF dataset card](https://huggingface.co/datasets/google-research-datasets/disfl_qa)).
The repository "was archived by its owner on Apr 19, 2026, and is now
read-only" ([GitHub README](https://github.com/google-research-datasets/Disfl-QA)).
The ACL Anthology paper is CC BY 4.0 ("Materials published in or after 2016
are licensed on a Creative Commons Attribution 4.0 International License",
[Anthology page](https://aclanthology.org/2021.findings-acl.293/)).

**What it cannot see.** No fillers, no partial words, no casing or
punctuation task (inputs are already cased and punctuated questions), no
spoken-form numbers, no vocabulary, no ASR noise. Every item contains exactly
one disfluency ("Disfluencies 100%"), so a system that always edits is never
penalized for over-cleaning; the dataset has no negatives. One reference per
item. The register is interrogative Wikipedia QA. The 11.8k pairs are entirely
public with the fluent side also present in SQuAD-v2, so contamination of any
LLM baseline is plausible and unmeasured here.

### 3. HyPoradise (Chen et al., 2023) and the GenSEC challenge (SLT 2024)

**What it is.** "HyPoradise: An Open Baseline for Generative Speech
Recognition with Large Language Models", NeurIPS 2023 Datasets and Benchmarks
track ([arXiv 2309.15701 abs](https://arxiv.org/abs/2309.15701)). The task is
"hypotheses-to-transcription (H2T)": an LLM maps an ASR system's N-best list
to the true transcript; the dataset has "more than 334K hypotheses-transcription
pairs ... collected from the various ASR corpus in most common speech domains"
([arXiv 2309.15701 PDF](https://arxiv.org/pdf/2309.15701)). N-best lists were
generated with "WavLM and Whisper".

**Sources and sizes** (paper Table 1, training pairs / test pairs): LibriSpeech
88,200 / 2,620; CHiME4 8,738 / 1,320; WSJ 37,514 / 503; SwitchBoard 36,539 /
2,000; Tedlium-3 47,500 / 2,500; LRS2 42,940 / 2,259; ATIS 3,964 / 809; CORAAL
1,728 / 100 ([arXiv 2309.15701 PDF](https://arxiv.org/pdf/2309.15701)). The
Hugging Face card preview shows records with `input` (a list of hypotheses,
five shown per row), `am_score`, `output`, `id`
([HF PeacefulData/HyPoradise-v0](https://huggingface.co/datasets/PeacefulData/HyPoradise-v0)).

**Metric.** WER of the corrected hypothesis, compared with two oracles: "1) the
lowest WER achievable by picking the best hypothesis from each N-best list" and
the "lower bound using elements" of all tokens in the list
([GenSEC paper, arXiv 2409.09785 PDF](https://arxiv.org/pdf/2409.09785)).

**GenSEC.** "GenSEC Challenge at IEEE SLT 2024: Text-based Generative Speech
Error Correction with LLMs", three tasks; Task 1 is "mapping from n-best
Hypotheses to ground truth speech Transcription (H2T)". Task 1 data: "HyPoradise
training sets (316.8k pairs)", dev "Librispeech-test-clean (2.6k pairs) and
WSJ-dev93 (503 pairs)" plus "a self-recorded unseen dev set (502 pairs)", eval
"Librispeech-test-other (2.9k pairs), WSJ-dev93 (333 pairs)" plus "a
self-recorded test set (503 pairs)"
([GenSEC site](https://sites.google.com/view/gensec-challenge/home)). The
challenge paper states the metric: "The WER of the corrected hypotheses is used
for evaluation" ([arXiv 2409.09785 PDF](https://arxiv.org/pdf/2409.09785)).

**License: contradictory.** The paper says "We will release the HP datasets,
reproducible pipelines, and pre-trained models on Github under MIT licence";
the GenSEC paper repeats "will be made open-source under the MIT license"; the
GitHub repo's `LICENSE` is MIT ("Copyright (c) 2023 Hypotheses-Paradise") and
the GitHub API reports `MIT`; the HF card's license field is `mit`. **But the
same repository ships `HP_dataset_legal agreement.pdf`**, whose text reads:
"you are granted the right to use the HP for noncommercial educational,
informational, and research purposes only ... You agree that you will not
modify, rent, lease, sell any of the decoding text, or create derivative works
using the HP" and "The paper authors and their academic organizations may
terminate any License at any time at their sole discretion"
([Hypo2Trans repo](https://github.com/Hypotheses-Paradise/Hypo2Trans);
agreement PDF fetched from `raw.githubusercontent.com/Hypotheses-Paradise/Hypo2Trans/main/HP_dataset_legal%20agreement.pdf`).
The underlying audio corpora also carry their own terms (LibriSpeech CC BY 4.0,
Switchboard and WSJ via LDC, etc.).

**What it cannot see.** The target is the *verbatim* reference transcript, so
a system that removes a filler or resolves a self-correction is penalized as a
word error. HyPoradise measures the opposite of cleanup: faithfulness to what
was *said*, not to what was *meant*. It has no notion of edits, outcomes or
fallback, and no negatives in the cleanup sense (every item is expected to be
corrected toward the reference).

### 4. The Open ASR Leaderboard, ESB and the Whisper normalizer

**What it is.** "The Open ASR Leaderboard evaluates open-source and proprietary
speech recognition models on English and multiple languages"; metrics are WER
("Word Error Rate is used to measure the accuracy of automatic speech
recognition systems") and RTFx ("Inverse Real Time Factor is a measure of the
latency") ([Space constants.py](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard/raw/main/constants.py)).
English short-form datasets listed there: AMI, Earnings22, GigaSpeech,
LibriSpeech, SPGISpeech, URGENT24, Voice Arena Monsoon, VoxPopuli. The
accompanying paper (arXiv 2510.06961, v4 revised 2026-03-30) compares "86
open-source and proprietary systems across 12 datasets"
([arXiv abs](https://arxiv.org/abs/2510.06961)).

**Normalization.** "we normalize all text prior to computing WER. This
normalization removes punctuation and casing, and applies a pipeline closely
following that of Whisper" ([constants.py](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard/raw/main/constants.py)).
The paper is explicit about what that erases: "For normalized transcriptions,
punctuation and casing is removed, as well as disfluencies such as fillers
(e.g., 'ah', 'uh', 'um'), repetitions, and repairs" and "The pipeline includes
number normalization (e.g., 'zero' to '0'), spelling standardization, and the
removal of filler words" ([arXiv 2510.06961 PDF](https://arxiv.org/pdf/2510.06961)).
The repo's `normalizer/normalizer.py` header reads "Copyright 2022 The OpenAI
team and The HuggingFace Team" and "Most of the code is copy pasted from the
original whisper repository"; its filler list is **wider than Whisper's**,
covering patterns for ah/aah/ahh, aha, eh/ehh/ehm, em, er/err/erm, hah, heh,
huh, hm/hmm, mm, mh/mhm, tsk, ugh, uh/uhh/uhm, uhuh/uhum, um/umm and the
irregular words ahem, eheh, ehehe, ehr, hmmph, hum, hunh, mhum, mmkay
([normalizer.py](https://raw.githubusercontent.com/huggingface/open_asr_leaderboard/main/normalizer/normalizer.py)).
Repo license: Apache-2.0 ([GitHub README](https://github.com/huggingface/open_asr_leaderboard)).

**Submission and who runs it.** "External contributors can add a new model to
the leaderboard by opening a pull request (PR) that includes: 1. A Python
script for evaluation on a specific dataset ... 2. A Bash script ... 3.
Self-reported metrics. We verify these scripts in our environment"; results
were run "on an NVIDIA A100-SXM4-80GB GPU (driver 560.28.03, CUDA 12.6)"
([arXiv 2510.06961 PDF](https://arxiv.org/pdf/2510.06961)). The current README
says contributors launch short-form runs on HF Jobs ("Nvidia H200") while "the
maintainers run the private dataset evaluations"
([GitHub README](https://github.com/huggingface/open_asr_leaderboard)).
(Governance detail is for `04-governance.md`.)

**Whisper's own normalizer.** The Whisper paper's Appendix C lists the English
steps, including "3. Remove any of the following words: hmm, mm, mhm, mmm, uh,
um", "5. Convert standard or informal contracted forms of English into the
original form", "9. Detect any numeric expressions of numbers and currencies
and replace with a form using Arabic numbers", "10. Convert British spellings
into American spellings", and states the design intent: "a best-effort attempt
to penalize only when a word error is caused by actually mistranscribing a
word, and not by formatting or punctuation differences". It also warns: "Our
text normalizer was developed through iterative manual inspection ... We
caution this development procedure comes at a risk of overfitting to the
transcription style of Whisper models" ([arXiv 2212.04356 PDF](https://arxiv.org/pdf/2212.04356)).
Code confirms the step list and adds contraction expansion (`won't`→`will
not`, `gonna`→`going to`, etc.) and `'s`→` is`
([english.py](https://raw.githubusercontent.com/openai/whisper/main/whisper/normalizers/english.py);
[basic.py](https://raw.githubusercontent.com/openai/whisper/main/whisper/normalizers/basic.py)).
Whisper is MIT licensed, "Copyright (c) 2022 OpenAI"
([LICENSE](https://raw.githubusercontent.com/openai/whisper/main/LICENSE)).

**ESB.** The predecessor benchmark argued the opposite of normalizing away
formatting: "Benchmarked systems must use the same data pre- and
post-processing algorithm across datasets" and that transcription artefacts
such as punctuation and casing should be included in evaluation
([arXiv 2210.13352 abs](https://arxiv.org/abs/2210.13352)). The ESB dataset
card records which constituent sets have "Normalised" versus "Punctuated &
Cased" transcripts and their licenses (LibriSpeech CC-BY-4.0, Common Voice
CC0-1.0, VoxPopuli CC0, TED-LIUM CC-BY-NC-ND 3.0, GigaSpeech apache-2.0,
SPGISpeech User Agreement, Earnings-22 CC-BY-SA-4.0, AMI CC-BY-4.0)
([HF esb-datasets-test-only-sorted](https://huggingface.co/datasets/hf-audio/esb-datasets-test-only-sorted)).

**What it cannot see.** By design the leaderboard normalizer deletes exactly
the layer this bench wants to measure: fillers, repetitions, repairs, casing,
punctuation, number formatting and spelling variants are all collapsed before
scoring. Two systems that differ only in cleanup quality score identically.
The normalizer is nonetheless the best-documented *reference* for which
surface differences the ASR community treats as non-semantic.

### 5. Inverse text normalization and spoken-form sets

**NeMo ITN.** "NeMo Inverse Text Normalization: From Development To
Production" introduces "an open-source Python WFST-based library for ITN" and
argues hand-written grammars suit "this task [which] has extremely low tolerance
to unrecoverable errors"; because "a public dataset for ITN is not available,
we adapted the Google Text Normalization dataset for ITN"
([arXiv 2104.05055 PDF](https://arxiv.org/pdf/2104.05055);
[abs](https://arxiv.org/abs/2104.05055)). The library README: "a Python
package for text normalization and inverse text normalization", "under Apache
2.0 license" ([GitHub NeMo-text-processing](https://github.com/NVIDIA/NeMo-text-processing)).
The ITN package directory lists language folders `ar de en es es_en fr he hi
hi_en hy ja ko mr pt ru sv vi zh` (GitHub contents API, 2026-10-24). The
official docs pages tried returned 404 (see "Not found").

**Sproat & Jaitly text normalization challenge.** "RNN Approaches to Text
Normalization: A Challenge" presents "a large corpus of written text aligned to
its normalized spoken form" where "the normalizations were generated using an
existing text normalization component of a text-to-speech system" (Kestrel).
"Our data consists of 1.1 billion words of English text, and 290 million words
of Russian text, from Wikipedia regions that could be decoded as UTF8". The
footnote on release says the data is available "most likely under the Creative
Commons 4.0 license" and "include the training, development and test datasets
with their annotated normalized outputs; and scoring scripts". The paper's
central warning is about *kind* of error, not rate: some RNNs "produce very
good results when measured in terms of overall accuracy" yet "the errors that
are produced are problematic, since they would convey completely the wrong
message if such a system were deployed", and "a simple FST-based filter can
mitigate those errors" ([arXiv 1611.00068 PDF](https://arxiv.org/pdf/1611.00068)).
The companion GitHub repo says only "Links to data used in Sproat & Jaitly ...
experiments, with data for Polish added by request" and "The data is hosted by
Kaggle" ([rwsproat/text-normalization-data](https://github.com/rwsproat/text-normalization-data)).
The Kaggle competition and dataset pages did not render for fetching (see
"Not found"), so the competition's own metric statement could not be quoted
from a primary page.

**Direction matters.** Both resources are *written→spoken* (TN), machine
generated by a TTS front end. For cleanup the needed direction is
*spoken→written* (ITN), and NeMo's own paper says no public ITN set exists;
they invert the TN data. The semiotic-class framing (dates, money, measures,
cardinals, ordinals, etc.) is the reusable idea.

**What it cannot see.** Single-token semiotic classes only; no disfluency, no
casing beyond the token, no context-dependent decisions ("twenty twenty" as a
year versus two numbers), and the references are machine-made, so systematic
Kestrel conventions become ground truth.

### 6. Punctuation restoration benchmarks

**The IWSLT TED set.** The common English benchmark is the TED transcript
data from the IWSLT evaluation campaign. Che et al. (2016, LREC) "test our
models on the IWSLT datasets ... There are both punctuated reference
transcripts and unpunctuated but segmented ASR transcripts provided", classify
three marks, "COMMA, PERIOD and QUESTION. Exclamation marks or semicolons are
classified as PERIOD, while colons or dashes are classified as COMMA", and
give their test sets as 12,626 words (reference: 830 COMMA, 808 PERIOD, 46
QUESTION) and 12,822 words (ASR: 798, 810, 35)
([ACL Anthology L16-1103 PDF](https://aclanthology.org/L16-1103.pdf);
[L16-1103 page](https://aclanthology.org/L16-1103/)). Alam, Khan and Alam
(2020, W-NUT) use "the same train, development, and test splits released by Che
et al." and tabulate the English training set as 2,102,417 tokens (6.3% Period,
7.53% Comma, 0.47% Question, 85.7% O), dev 295,800 tokens, Test (Ref.) 12,626,
Test (ASR) 12,822; they note the dataset "was originally released in the IWSLT
evaluation campaign in 2012"
([ACL Anthology 2020.wnut-1.18 PDF](https://aclanthology.org/2020.wnut-1.18.pdf)).
Other papers label the same test sets "IWSLT2011" (e.g.
[arXiv 2004.00248 PDF](https://arxiv.org/pdf/2004.00248)); the naming is
inconsistent across the literature.

**Metric.** Per-class precision, recall and F1 for COMMA, PERIOD, QUESTION
plus an overall F1 (Alam et al. 2020; Che et al. 2016).

**What it cannot see.** Three punctuation classes only; no casing in the
standard setup; no word changes at all; TED monologue register. The "ASR"
test set is the one place in this survey where recognizer errors are present
in the input with a clean reference, but only for punctuation placement.

### 7. Industry "clean verbatim" style guides

These define cleanup in prose, for human transcribers.

**Rev.** "Clean verbatim transcription means that your audio or video files
have been lightly edited for easy readability." Removed: "Stuttering", "Filler
words like 'um' and 'like'", "'Yeah,' 'uh huh' and other interjections from
other speakers", "Throat clearing and coughs", "Run-on sentences", "False
starts", "Unintentional word repetition", "Background noise and speaking".
Constraint: "There is never any paraphrasing; clean verbatim transcription is
exactly what has been said, but cleaned up for clarity"
([Rev: What does clean verbatim transcription mean](https://www.rev.com/blog/resources/what-does-clean-verbatim-transcription-mean)).
Rev's verbatim page: a verbatim transcript includes "certain non-speech sounds,
interjections or signs of active listening, filler words, false starts,
self-corrections, and stutters"; non-verbatim removes "filler words, stammers,
and anything that takes away from the core message". Its worked pair:
verbatim "And so, um, I guess… I think we should go to the, the m- m- movies
tonight 'cause of the discount (laughs)." → non-verbatim "I think we should go
to the movies tonight because of the discount."
([Rev: verbatim transcription](https://www.rev.com/blog/resources/verbatim-transcription)).
Note that this example expands "'cause" to "because", a word change beyond
deletion. Rev's freelancer "Style Guide References" page returned HTTP 403.

**TranscribeMe.** Filler and crutch words: "we always remove filler words such
as uh, um, mm-hmm, etc." except when "the only response to a direct question";
"the only crutch words we remove are like and you know when they add no
meaning to what is said"; "we DO NOT remove any crutch words/phrases other
than like and you know" (examples kept: sort of, kind of, I mean, I guess);
"like" is kept when a verb or meaning "about"; "you know" is kept when it is a
real question or "truly seeking agreement/understanding"
([TM Library: Filler and Crutch Words](https://tm-library.helpscoutdocs.com/article/177-filler-and-crutch-words)).
False starts: "A false start is the term we use to describe any time a speaker
corrects themselves or changes of direction of their thought." "Our general
rule is that we keep four words or more and remove three or less." If the
speaker self-corrects with "sorry" or "I mean" and adds words, "we do not
remove them or the false start that preceded them"
([TM Library: False Starts](https://tm-library.helpscoutdocs.com/article/179-false-starts)).
The Full Verbatim guide, by contrast, says "capture all filler and crutch words
as said", "you must capture false starts of any length", "All stutters must be
included", and "This style guide IS NOT for use in Clean Verbatim files"
([TM Library: Full Verbatim Style Guide](https://tm-library.helpscoutdocs.com/article/557-team-guides-full-verbatim-style-guide)).
The top-level "TM Clean Verbatim Style Guide" article exposes only a PDF link
that could not be fetched.

**Verbit.** "Full verbatim captures the spoken word exactly as stated,
including fillers words, stutters and false starts." "Clean verbatim corrects
for filler words, repeated words and stutters." Court example: "some court
reporting agencies ... want clean verbatim when transcribing attorney or court
statements. However, they want full verbatim when witnesses or deponents
speak" ([Verbit: Verbatim transcription 101](https://verbit.ai/verbatim-transcription-101-benefits/)).
James Madison University's captioning guide quotes Verbit's definition, "a
style of transcription 'that still captures all speech but removes audio
components that may impede readability'", and lists the removals: "Stutters",
"Filler speech, including 'um,' 'uh,' etc.", "The repetitive use of 'like,'
'actually,' 'sort of,' 'kind of', etc.", "Interjections made by an interviewer,
such as 'yeah' and 'mm-hmm'", "False starts or redirects", "Run-on sentences"
([JMU transcription guidelines](https://www.jmu.edu/accessibility/digital-accessibility/guides/captioning/transcription-guidelines.shtml)).

**GoTranscript.** Clean verbatim excludes speech errors, "False starts, unless
they add information", stutters, "Repetitions, except those that express
emphasis", and fillers ("uh, um, you know, like, I mean, so, kind of, well,
sort of") with the caveat to check context so meaning is not changed. It keeps
emphatic repetition ("No, no, no."), expressions like "Oh my God", and
explicitly: "Do not correct grammatical errors made by the speakers." It also
*rewrites* slang to standard form ("going to" not "gonna", "want to" not
"wanna") and maps "Yeah/yep/yup/mm-hmm" to "yes"
([GoTranscript guidelines](https://gotranscript.com/transcription-guidelines)).

**Where the guides agree and disagree.** All four remove filled pauses,
stutters and unintentional repetition and keep meaning. They disagree on:
discourse-marker scope (TranscribeMe removes only "like" and "you know";
GoTranscript lists nine); false-start length (TranscribeMe's three-word rule;
Rev's "quickly reworded"); slang normalization (GoTranscript and Rev's example
expand "gonna"/"'cause"; TranscribeMe's full-verbatim guide says never change
contractions, and GoTranscript says "Never change spoken contractions" while
still expanding "gonna"); grammar (GoTranscript forbids correcting it; Rev lists
"run-on sentences" as removed). None of the guides addresses how to render a
*self-correction whose repair replaces content* ("Thursday, no wait, Friday"):
they describe false starts as deletions and are silent on choosing the repair
over the reparandum.

### 8. Real dictation with cleaned references

**Not found** for English. Searches run (2026-10-24): "dataset real dictation
transcripts with cleaned written references spoken-to-written parallel corpus
English"; "dictation dataset transcripts cleaned OR edited reference text pairs
voice typing corpus open license huggingface"; "medical dictation corpus
dataset raw transcript edited report pairs public release"; "disfluency
removal OR disfluency correction dataset English parallel disfluent fluent
sentences Fisher Switchboard released corpus license". Nothing surfaced that
pairs real dictation (single speaker, composing text) with an edited target
under an open license. Adjacent resources that were opened:

- **Japanese spoken-to-written corpus** (Ihori, Takashima, Masumura, LREC
  2020): "a parallel corpus of spoken-style text and written-style text" built
  by preparing four types of spoken-style text and using "a crowdsourcing
  service for manually converting them into written-style text"; covers
  "punctuation restoration, disfluency detection, and simplification" plus
  Japanese-specific style unification. The paper's own notice reads "licensed
  under CC-BY-NC"; corpus availability is not stated on the Anthology page
  ([ACL Anthology 2020.lrec-1.779](https://aclanthology.org/2020.lrec-1.779/);
  [PDF](https://aclanthology.org/2020.lrec-1.779.pdf)). Japanese only.
- **DISCO** (Bhat, Jyothi, Bhattacharyya, EMNLP Findings 2023): human-annotated
  disfluent→fluent pairs in English, Hindi, German, French; English 3,479
  sentence pairs, 31,994 words, 18.99% disfluent words. Annotators were "asked
  to only remove disfluent words from utterances without changing word order
  or correcting original words/phrases"; "for every language, only one
  annotator created fluent sentences and disfluency type labels"
  ([arXiv 2310.16749 PDF](https://arxiv.org/pdf/2310.16749)). The GitHub repo
  states no license (README checked; GitHub API license field empty,
  [vineet2104/DISCO](https://github.com/vineet2104/DISCO)). Source utterances
  are human–AI assistant dialogues, not dictation.
- **LARD** (Passali et al., LREC 2022): synthetic injection of "repetitions,
  replacements, and restarts" into fluent text; "95,992 examples of utterances
  with 71,994 artificial inserted disfluencies", splits 57,595 / 19,198 /
  19,199, base text the Schema-Guided Dialogue dataset; README says code is
  "CC BY-NC-SA 4.0" while the dataset badge reads "CC BY-SA 4.0"
  ([GitHub](https://github.com/tatianapassali/artificial-disfluency-generation);
  [arXiv 2201.05041](https://arxiv.org/abs/2201.05041)). Synthetic; detail for
  `03-data.md`.
- **SPACER** (Upadhye, Li, Futrell, 2025): "single-word substitution errors
  from the Switchboard corpus, along with speakers' self-repairs and
  comprehenders' responses"; paper CC BY 4.0; dataset size not on the abstract
  page ([arXiv 2503.16745](https://arxiv.org/abs/2503.16745)). Narrow scope.
- **Rev's Reverb** release: ASR and diarization models "limited to
  non-commercial use" ([arXiv 2410.03930](https://arxiv.org/abs/2410.03930));
  the abstract page does not describe the verbatim / non-verbatim training
  styles. Relevant to `05-market.md`.

### Summary table

| Resource | Measures | Input → output | Size (as stated) | Refs/item | License | References made by | Cannot see |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Switchboard disfluency (Treebank-3) | Edited-word P/R/F | Transcript (partials, punctuation stripped) → per-word EDITED label | 1,126 conversations (per Jamshid Lou & Johnson 2020); ~1M-word Treebank subset (NXT page); SWB gold 98k sents / 733k words | 1 | LDC user agreement; NXT layer CC BY-NC-SA 3.0 | Trained annotators, Meteer stylebook | Casing, punctuation, spoken form, insertions, over-cleaning, dictation register |
| Disfl-QA | QA F1; disfluency correction (BLEU/F1 in paper) | Cased punctuated disfluent question → fluent question | 11,825 (7,182 / 1,000 / 3,643) | 1 | CC BY 4.0 per README and HF card; no LICENSE file; repo archived 2026-04-19 | Expert linguists write disfluency into fluent SQuAD question; second-pool check κ=0.55 | Fillers, partial words, casing, punctuation, numbers, negatives, ASR noise |
| HyPoradise / GenSEC Task 1 | WER vs verbatim reference, with N-best oracles | N-best ASR hypotheses → verbatim transcript | >334K pairs; GenSEC 316.8k train | 1 | MIT (paper, repo LICENSE, HF) **vs** noncommercial no-derivatives legal agreement in same repo | Existing ASR corpus references | Anything that departs from verbatim; penalizes cleanup |
| Open ASR Leaderboard | WER, RTFx after Whisper-style normalization | Audio → text, normalized | 86 systems, 12 datasets (paper) | 1 | Code Apache-2.0; datasets vary (ESB table) | Constituent corpora | Fillers, repetitions, repairs, casing, punctuation, number format (all normalized away) |
| Whisper EnglishTextNormalizer | Equivalence classes for WER | Text → canonical text | n/a | n/a | MIT | OpenAI, by manual inspection of Whisper errors | Meaning; declared risk of overfitting to Whisper style |
| Sproat & Jaitly TN data | Token accuracy by semiotic class | Written token → spoken form | 1.1B words EN, 290M RU | 1 | "most likely" CC 4.0 (paper footnote); Kaggle page unreachable | Kestrel TTS front end (machine) | Spoken→written direction, context, disfluency |
| NeMo ITN | Not a dataset; WFST library | Spoken form → written form | 19 language folders | n/a | Apache-2.0 | Grammars | Evaluated on inverted TN data; no public ITN test set per authors |
| IWSLT TED punctuation (Che 2016 split) | Per-class P/R/F1 for COMMA, PERIOD, QUESTION | Unpunctuated words (ref or ASR) → punctuation labels | Train 2,102,417 tokens; dev 295,800; test 12,626 (ref) / 12,822 (ASR) | 1 | Not stated in the opened pages | TED subtitles | Casing, word changes, dictation register |
| Clean-verbatim style guides | Human editing rules in prose | Speech → readable transcript | n/a | n/a | Company web pages | Transcription vendors | Not a dataset; no agreed handling of repair-replaces-reparandum |
| DISCO (English) | F1 on disfluent-word tagging | Dialogue utterance → fluent utterance | 3,479 pairs, 31,994 words | 1 | None stated | One hired annotator per language | Casing, punctuation, correction choice (deletion only) |
| LARD | Detection / correction on synthetic data | Fluent SGD text → injected disfluency | 95,992 examples | 1 | CC BY-SA 4.0 (dataset badge) / CC BY-NC-SA 4.0 (code) | Rule-based injection | Realism of injected errors (see 03) |
| Real dictation + cleaned references | — | — | — | — | — | — | **Not found** |

---

## What is recommended

1. **Reuse Disfl-QA as the external, held-out probe for cross-sentence and
   interrogative-phrase corrections, with attribution, and say exactly what it
   is.** It is the only public set whose disfluencies are mostly corrections
   and restarts, which matches the vault's finding about interrogative-phrase
   corrections. Attribute as CC BY 4.0 to Gupta, Xu, Upadhyay, Yang and
   Faruqui (Findings of ACL-IJCNLP 2021), cite both the paper and the (now
   archived) repository, and record in the item `notes` that the license is
   asserted in the README only, with no LICENSE file. Lowercase and strip
   punctuation before use so inputs match the dictation shape; keep the
   original cased question as the single reference. Do not treat it as
   representative of dictation: it has no fillers, no negatives, one
   disfluency per item, Wikipedia QA register.

2. **Do not reuse HyPoradise or GenSEC data as items.** The target is verbatim
   text, so it measures the opposite of cleanup. The license is also
   internally contradictory (MIT versus a noncommercial, no-derivatives
   agreement in the same repository). Reuse only the *methodology* idea of
   reporting oracle bounds alongside the system score.

3. **Do not use the Open ASR Leaderboard normalizer as a scoring normalizer.**
   It deletes fillers, repairs, casing, punctuation and number formatting, the
   very layer being measured. Reuse it in two narrower ways: (a) as the
   documented list of *non-semantic* surface variants for a "normalized exact
   match" that is deliberately weaker than it (contractions, British/American
   spelling, whitespace, apostrophe spacing only); (b) as the canonical
   filler inventory when generating or auditing the fillers category. Cite
   Whisper (MIT) and the HF repo (Apache-2.0).

4. **Reuse the Switchboard annotation *taxonomy*, not the data.** The LDC
   license and fee make the corpus unusable for a stranger's one-command
   replay. Adopt Meteer's categories (filled pause, explicit editing term,
   discourse marker; restart with repair, restart without repair, complex
   restart) as the vocabulary for item `notes` and for the per-edit audit, and
   adopt the field's word-level precision/recall of edited words as the lineage
   for the bench's edit-level precision and recall (detail in
   `02-metrics.md`).

5. **Borrow the semiotic-class list from text normalization for the
   spoken-form category** (cardinal, ordinal, date, time, money, measure,
   telephone, address, etc.), citing Sproat and Jaitly, and borrow their
   central warning: report *unrecoverable* errors (a changed number) separately
   from surface misses, because "they would convey completely the wrong message".
   That maps onto the third law.

6. **Treat IWSLT TED punctuation as lineage for the punctuation-casing
   category's metric** (per-class precision/recall for period, comma,
   question mark), not as a data source: license was not stated on the pages
   opened and the register is TED monologue.

7. **Write the task definition against the style guides, and name the
   disagreements as item categories.** Clean verbatim's agreed core (fillers,
   stutters, unintentional repetition, false starts, no paraphrase) is the
   bench's "cleanup" definition. The disagreements become explicit decisions
   for Part 2: discourse-marker scope ("like", "you know", "I mean", "sort
   of"), slang expansion ("gonna"), grammar correction (the guides say leave
   it), and emphatic repetition (keep). The guides' silence on repair-selects-
   content corrections confirms that the correction categories need
   first-party references.

8. **Build the dictation items ourselves.** No English dataset of real
   dictation with cleaned references exists in public, so the data plan in
   `03-data.md` has to carry this.

### Conflicts with the vault and the appendix hypothesis

- **Vault claim confirmed with a caveat.** The vault says Disfl-QA is CC BY
  4.0 and held out. The README and the Hugging Face card say CC BY 4.0, but
  there is no LICENSE file in the repository and the repository is archived.
  The attribution statement should say the license is as asserted in the
  README.
- **Vault's "66% of real human disfluency" wording.** Disfl-QA's paper states
  "Over 90% of the disfluencies in Disfl-QA are corrections or restarts" and
  "≈30% and >65% ... are restarts and corrections respectively", about its own
  *constructed* set, and contrasts Switchboard where "Correction & Restarts
  <50%". The vault's phrase "roughly 66% of real human disfluency" should not
  be read as a statement about dictation in the wild; it is a statement about
  Disfl-QA's composition, which annotators were instructed to make
  correction-heavy and filler-free. The bench should weight categories using
  `06-user-pain.md`, not this number.
- **Appendix hypothesis, "normalized exact match".** The obvious normalizer
  (Whisper / Open ASR) removes fillers and repairs, which would score an
  unchanged identity output as correct on a fillers item. The normalizer used
  for exact match must be a reduced one (confirmed as a decision for
  `02-metrics.md`).
- **Appendix hypothesis, "a labelled Disfl-QA subset".** Confirmed as viable,
  but the mapping to categories is partial: Disfl-QA covers
  correction-interrogative and correction-cross (and some intra), nothing else.

### Not found

- Shriberg (1994) thesis text online. Searched: `Shriberg 1994 "Preliminaries
  to a Theory of Speech Disfluencies" thesis reparandum interregnum repair`.
  Only secondary descriptions were returned.
- A word count for the Treebank-3 disfluency-annotated Switchboard subset on
  an LDC page. LDC99T42 lists no counts; NXT pages say "one million words"
  for the Treebank syntax/disfluency subset.
- The Kaggle competition and dataset pages for the Sproat & Jaitly data
  returned only a page title (JavaScript-rendered), so the competition's
  metric and license text could not be quoted from Kaggle.
- Rev's freelancer "Style Guide References" page (HTTP 403) and TranscribeMe's
  "TM Clean Verbatim Style Guide" body (PDF link only).
- NVIDIA NeMo text-processing documentation pages at the two URLs tried
  (both 404); the GitHub repository and the ITN paper were used instead.
- Any English dataset pairing real dictation with cleaned references (searches
  listed in section 8).
- A license statement for the IWSLT TED punctuation split on the pages
  opened.

---

## Sources

All accessed 2026-10-24.

- https://catalog.ldc.upenn.edu/LDC97S62 — Switchboard-1 Release 2 contents and LDC licensing terms.
- https://catalog.ldc.upenn.edu/LDC99T42 — Treebank-3 contents ("dysfluency-annotated" Switchboard) and licensing.
- https://catalog.ldc.upenn.edu/LDC2009T26 — NXT Switchboard Annotations: disfluency layer, CC BY-NC-SA 3.0 for non-profit/nonmembers.
- https://groups.inf.ed.ac.uk/switchboard/overview.html — "one million words" Treebank subset annotated for syntax and disfluencies.
- https://www.cs.brandeis.edu/~cs140b/CS140b_docs/DyfluencyGuide.pdf — Meteer et al. 1995 Switchboard dysfluency annotation stylebook: F/E/D classes, restart notation, cleanup intent.
- https://aclanthology.org/N01-1016.pdf — Charniak & Johnson 2001: standard Switchboard train/dev/test split, edited-word misclassification rate.
- https://arxiv.org/pdf/1604.03209 — Zayats, Ostendorf, Hajishirzi 2016: reparandum/interregnum/repair framing; "precision/recall of words in edit regions".
- https://arxiv.org/pdf/2004.05323 — Jamshid Lou & Johnson 2020: split restated, SWB gold 98k/733k, Fisher silver, partial words removed, P/R/F definitions.
- https://arxiv.org/pdf/2009.10298 and https://arxiv.org/abs/2009.10298 — Jamshid Lou & Johnson 2020 (E2E): "1,126 conversations were hand-annotated with disfluencies".
- https://github.com/google-research-datasets/Disfl-QA — Disfl-QA README: description, splits, JSON format, CC BY 4.0 statement, archived 2026-04-19.
- https://arxiv.org/pdf/2106.04016 — Disfl-QA paper: annotation protocol, rater instructions, sizes, category percentages, agreement.
- https://aclanthology.org/2021.findings-acl.293/ — Disfl-QA Anthology record and CC BY 4.0 paper license.
- https://huggingface.co/datasets/google-research-datasets/disfl_qa — HF mirror: license field cc-by-4.0, splits, fields.
- https://arxiv.org/abs/2309.15701 and https://arxiv.org/pdf/2309.15701 — HyPoradise paper: task, Table 1 sizes, MIT statement.
- https://github.com/Hypotheses-Paradise/Hypo2Trans — HyPoradise repo: MIT LICENSE, HF link, `HP_dataset_legal agreement.pdf` (noncommercial, no derivative works).
- https://huggingface.co/datasets/PeacefulData/HyPoradise-v0 — HF card: license `mit`, record fields.
- https://sites.google.com/view/gensec-challenge/home — GenSEC Task 1 data splits and sizes.
- https://arxiv.org/pdf/2409.09785 — GenSEC challenge paper: WER metric, oracle bounds, MIT statement.
- https://huggingface.co/spaces/hf-audio/open_asr_leaderboard/raw/main/constants.py — Open ASR Leaderboard metric and normalization text, dataset list.
- https://huggingface.co/spaces/hf-audio/open_asr_leaderboard/raw/main/README.md — Space front matter and citation (arXiv 2510.06961).
- https://github.com/huggingface/open_asr_leaderboard — repo README: datasets, submission via PR, HF Jobs hardware, Apache-2.0.
- https://raw.githubusercontent.com/huggingface/open_asr_leaderboard/main/normalizer/normalizer.py — normalizer attribution to Whisper; extended filler list.
- https://arxiv.org/abs/2510.06961 and https://arxiv.org/pdf/2510.06961 — Open ASR Leaderboard paper: what normalization removes, PR process, A100 hardware.
- https://arxiv.org/pdf/2212.04356 — Whisper paper, Appendix C text standardization steps and overfitting caution.
- https://raw.githubusercontent.com/openai/whisper/main/whisper/normalizers/english.py — EnglishTextNormalizer code: filler regex, contraction rules.
- https://raw.githubusercontent.com/openai/whisper/main/whisper/normalizers/basic.py — BasicTextNormalizer code.
- https://raw.githubusercontent.com/openai/whisper/main/LICENSE — Whisper MIT license.
- https://arxiv.org/abs/2210.13352 — ESB abstract: same pre/post-processing across datasets; punctuation and casing should be evaluated.
- https://huggingface.co/datasets/hf-audio/esb-datasets-test-only-sorted — ESB dataset card: per-dataset licenses and "Normalised" vs "Punctuated & Cased".
- https://arxiv.org/pdf/2104.05055 and https://arxiv.org/abs/2104.05055 — NeMo ITN paper: WFST approach, no public ITN set, Google TN data inverted.
- https://github.com/NVIDIA/NeMo-text-processing — README: TN and ITN, Apache 2.0.
- https://arxiv.org/pdf/1611.00068 — Sproat & Jaitly: data size, Kestrel provenance, "most likely" CC 4.0, unrecoverable-error argument.
- https://github.com/rwsproat/text-normalization-data — pointer repo: data hosted on Kaggle.
- https://aclanthology.org/L16-1103.pdf and https://aclanthology.org/L16-1103/ — Che et al. 2016: IWSLT TED punctuation test sets (12,626 / 12,822 words) and class mapping.
- https://aclanthology.org/2020.wnut-1.18.pdf — Alam, Khan, Alam 2020: IWSLT 2012 origin, Che split reuse, Table 1 token counts.
- https://arxiv.org/pdf/2004.00248 — example of the same TED data labelled "IWSLT2011".
- https://www.rev.com/blog/resources/what-does-clean-verbatim-transcription-mean — Rev clean verbatim definition and removal list; "never any paraphrasing".
- https://www.rev.com/blog/resources/verbatim-transcription — Rev verbatim vs non-verbatim definitions and worked example.
- https://tm-library.helpscoutdocs.com/article/177-filler-and-crutch-words — TranscribeMe filler and crutch word rules.
- https://tm-library.helpscoutdocs.com/article/179-false-starts — TranscribeMe false start definition and three-word rule.
- https://tm-library.helpscoutdocs.com/article/557-team-guides-full-verbatim-style-guide — TranscribeMe full verbatim rules (contrast).
- https://tm-library.helpscoutdocs.com/collection/499-clean-verbatim---tm-style and https://tm-library.helpscoutdocs.com/article/469-tm-clean-verbatim-style-guide — collection index; style guide body only as PDF.
- https://verbit.ai/verbatim-transcription-101-benefits/ — Verbit full vs clean verbatim, court example.
- https://www.jmu.edu/accessibility/digital-accessibility/guides/captioning/transcription-guidelines.shtml — Verbit definition quoted with removal list.
- https://gotranscript.com/transcription-guidelines — GoTranscript clean verbatim rules, slang normalization, "Do not correct grammatical errors".
- https://aclanthology.org/2020.lrec-1.779/ and https://aclanthology.org/2020.lrec-1.779.pdf — Ihori et al. 2020 Japanese spoken-to-written corpus, crowdsourced, CC-BY-NC notice.
- https://arxiv.org/abs/2310.16749 and https://arxiv.org/pdf/2310.16749 — DISCO: sizes, single-annotator protocol, deletion-only instruction.
- https://github.com/vineet2104/DISCO — DISCO repo: no license stated.
- https://arxiv.org/abs/2201.05041 and https://github.com/tatianapassali/artificial-disfluency-generation — LARD: method, 95,992 examples, licenses.
- https://arxiv.org/abs/2503.16745 — SPACER abstract: Switchboard single-word substitution repairs.
- https://arxiv.org/abs/2410.03930 — Reverb: Rev's ASR release, non-commercial.
- https://arxiv.org/abs/2104.00034 — opened by mistake (wrong identifier; unrelated knapsack paper). Not used.

Unreachable or unusable pages tried: https://raw.githubusercontent.com/google-research-datasets/Disfl-QA/main/LICENSE (404);
https://support.rev.com/hc/en-us/articles/39516207669517-Style-Guide-References (403);
https://www.kaggle.com/competitions/text-normalization-challenge-english-language and
https://www.kaggle.com/datasets/richardwilliamsproat/text-normalization-for-english-russian-and-polish (title only);
https://docs.nvidia.com/nemo-framework/user-guide/latest/nemo-text-processing/intro.html and
https://docs.nvidia.com/nemo-framework/user-guide/latest/nemotoolkit/nlp/text_normalization/wfst/wfst_inverse_text_normalization.html (404);
https://www.rev.com/resources/verbatim-vs-clean-verbatim-transcription,
https://www.transcribeme.com/clean-verbatim-transcription/,
https://verbit.ai/transcription/what-is-clean-verbatim-transcription/ (404);
https://huggingface.co/spaces/hf-audio/open_asr_leaderboard (app shell only);
https://github.com/huggingface/open_asr_leaderboard/tree/main/normalizer (file list only).
