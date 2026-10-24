# Part 1 research plan

This folder holds the research that precedes the Cleanup Bench spec. Nothing
here is the spec. Each report separates **what was found** from **what is
recommended** under different headings, and ends with a **Sources** section
listing every page that was actually opened (URL, access date, one line on what
it contributed). A search snippet is never a source. Where a question came back
empty the report says "not found" and lists what was searched. No number
appears in any report unless a cited page states it.

Every finding is held against the three laws of cleanup: never lose words;
every edit is accounted for; when unsure, leave it as said. A report that finds
a practice rewarding fluent rewriting over faithful editing says so.

## The reports

| File | Question it answers |
| --- | --- |
| `01-existing-benchmarks.md` | What already measures something close to cleanup (Switchboard disfluency annotation and the detection literature, Disfl-QA, Hyporadise and GenSEC, the Open ASR Leaderboard and its normalizer, ITN and spoken-form test sets, punctuation restoration, the industry's clean-verbatim style guides, any real-dictation dataset with cleaned references)? For each: what it measures, input and output form, size, license, how references were made, references per item, what it cannot see. Which pieces can be reused, under which license, with what attribution? |
| `02-metrics.md` | How do adjacent fields score faithful editing (ERRANT, M2, GLEU, F0.5 in GEC, multi-reference handling, annotator agreement, WER and normalizers, hallucination and omission metrics in ASR post-editing, meaning-preservation checks and their biases)? Which metric set encodes the three laws, what does each derive from, and what can none of them catch? |
| `03-data.md` | How should items be built (how Switchboard and Disfl-QA made references, synthetic disfluency injection and its artifacts, TTS-to-ASR round trips, consent and PII scrubbing norms, contamination defenses: canaries, hidden splits, rolling refreshes, verified subsets)? Which sources, sizes per category, review process and versioning rule? |
| `04-governance.md` | How do respected leaderboards stay credible (Open ASR Leaderboard, MTEB, HELM, SWE-bench and SWE-bench Verified, BIG-bench, Dynabench, Chatbot Arena): submission rules, reproducibility requirements, who runs evaluation, item disputes, the organizer's own system on the board? What should our submission rule, run manifest, dispute process and conflict-of-interest statement be? |
| `05-market.md` | What do the products publish about cleanup (Wispr Flow, Superwhisper and S1-mini, Aqua Voice, Willow, Monologue, Typeless and mono-1, Spokenly, VoiceInk, Handy, Apple SpeechAnalyzer and macOS dictation, and the formatting options of Deepgram, AssemblyAI, Speechmatics, Gladia)? What evidence do they show, which could run on this bench through which adapter, which are open weights and under what license? |
| `06-user-pain.md` | What do dictation users complain about on Hacker News, Reddit, app reviews and the GitHub issues of the open-source tools? Grouped into categories with rough counts and links, so the bench weights categories by real pain rather than by what is easy to generate. |
| `00-summary.md` | Written last. One page: the recommended shape of the bench; a decision table (options, recommendation, supporting file); what to reuse; what contradicts the working hypothesis in the prompt's appendix; what could not be found out. |

## Order of work

1. `01-existing-benchmarks.md`, because every later file depends on knowing
   what data and tasks already exist.
2. `02-metrics.md`, which needs the task definitions and reference formats
   from 01.
3. `03-data.md`, which needs the annotation methods from 01 and the metric
   requirements from 02.
4. `04-governance.md`, independent of the above and researched alongside them.
5. `05-market.md`, independent of the above and researched alongside them.
6. `06-user-pain.md`, independent of the above and researched alongside them.
7. `00-summary.md`, after all six are written and re-read together.

Reports 01 to 03 form one dependency chain; 04 to 06 are independent and are
researched in parallel with it. The summary is written only once all six exist.

## Rules observed while writing

- Open the primary page for every claim; prefer papers, official docs and
  license files over blog summaries.
- Record the access date on every source.
- Separate findings from recommendations under different headings.
- Where a finding conflicts with the vault's reasoning, say so explicitly.
- No benchmark code and no dataset are created in Part 1.
- Private speech data (`~/.pomvox/eval/`, `~/.pomvox/history.db`) is not read.
