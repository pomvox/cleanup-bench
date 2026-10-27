# 06. What dictation users complain about

Purpose: weight the bench's categories by what users actually suffer from, not
by what is easy to generate. Scope: complaints about the *text* that dictation
tools produce, with cleanup-layer failures separated from recognizer and
capture failures wherever the page makes that possible.

All pages were opened on 2026-10-24. Hacker News comment trees were retrieved
through the Algolia HN API (`hn.algolia.com/api/v1/items/<id>`) and are cited
by their `news.ycombinator.com` item URL; GitHub issues were retrieved through
the GitHub API (`gh issue view`) and are cited by their HTML URL. Reddit could
not be opened at all (see "Source classes" below). Every count below is a count
of distinct complaints on pages that were opened, not an estimate of the
population. Quotes are short and users are not named; the link identifies the
page.

## Source classes: what was reachable

| Class | Reachable? | What was opened |
| --- | --- | --- |
| Hacker News | Yes | 20 story threads located through the Algolia API; comment trees read in full for the 11 largest; story text for 4 more. |
| GitHub issues | Yes | Beingpax/VoiceInk (23 issues read), cjpais/Handy (16 issues read), anomalyco/hex (1), plus 16 issues found by a GitHub-wide search across smaller open-source dictation tools. epicenter-so/epicenter (Whispering) returned no issues for the search terms used ("transformation removed words", "hallucin", "filler", "punctuation"). |
| App Store review pages | Yes | Wispr Flow (iOS), Superwhisper (iOS), Spokenly, Monologue, Aqua Voice. Each page shows only ten reviews. The Mac listings for Wispr Flow and Superwhisper do not exist on the App Store; both are distributed directly. |
| Vendor feedback boards | Partly | Superwhisper's board (userjot) opened. Monologue's board (`feedback.monologue.to`) returned a Vercel `DEPLOYMENT_NOT_FOUND` page on every URL tried, including the root, so the two Monologue posts a search surfaced ("dictation accuracy", "mixed-language dictation accuracy") could not be read and are not counted. |
| Vendor documentation | Yes | Wispr Flow help centre (two articles), Superwhisper docs (three), VoiceInk docs (one), OpenWhispr docs (one). Used as vendor admissions of known failure modes, not as user complaints. |
| Apple Support Communities | Partly | Five threads opened. One (`thread/254453112`) redirected to an Apple sign-in page and was not read. The site's own search page returned no results to the fetcher. |
| Reddit | No | `www.reddit.com` and `old.reddit.com` are refused by the fetch tool; direct `curl` to `reddit.com/search.json` returned HTTP 403 for all six queries tried. A Reddit aggregator page (gummysearch.com/r/WisprFlow/) opened but showed only topic-tag counts, no post text, so nothing from it is counted as a complaint. |
| Review aggregators | Mostly no | Trustpilot's Wispr Flow profile has been removed by Trustpilot ("goes against our guidelines"); Trustpilot's Aqua Voice page shows one review about app stability. G2 (two URLs), TrustRadius, Product Hunt reviews, and Alternativeto's Wispr Flow reviews page were HTTP 403 or 404. |
| Press | Partly | Digital Trends on Wispr's "haters" survey opened. The New York Times Magazine essay that an HN thread titled "I hate Wispr Flow so much" links to could not be opened (nytimes.com and archive.is both refused), so it is listed as not read. |
| Academic | Partly | Larson and Mowatt (2003) full text opened as PDF. Karat et al. (1999) and Hong and Findlater (2018) could be confirmed by title, authors, year and venue only (ACM pages returned 403; Semantic Scholar returned no abstract). |

## What was found

The complaint categories below were adjusted from the suggested list after
reading. The important split that emerged is between words lost by **capture
or recognition** (microphone warm-up, voice activity detection, decoder
budgets) and words lost by the **cleanup layer** (filler filters, LLM
rewriting, output guards). The first is not something a text-to-text bench
can measure; the second is exactly what it must measure. They are reported
separately.

### 1. Words lost by the cleanup layer (meaning-changing drops, filler false positives, guard discards)

Count: 11 distinct complaints plus 3 vendor admissions.

- A dictation user with a hand injury reports that Wispr Flow "removes and swaps random words" and regularly drops "not", "never" and "before", giving the example that "never merge a change like this" can come out as "merge a change like this". They say they must reread everything and needed 12 corrections to post one tweet. Relayed by Digg from a post on X: https://digg.com/ai/ve5pkh0s
- Wispr Flow's own help centre states that Smart Formatting "can misinterpret meaningful words as filler or redundancy", which can remove a leading "so" or deliberate repetition. Vendor admission: https://docs.wisprflow.ai/articles/6568835559-why-wispr-flow-sometimes-removes-or-changes-words-on-android-smart-formatting
- Wispr, after inviting critics and receiving more than 700 responses, traced accuracy problems to "an overly aggressive Auto Cleanup setting that changed words users hadn't asked it to touch". Vendor admission reported by Digital Trends: https://www.digitaltrends.com/computing/wispr-flow-asked-its-haters-what-was-wrong-and-more-than-700-people-answered/
- VoiceInk's filler filter removes the German word "um" ("Wir diktieren, um weniger schreiben zu müssen" loses "um"), with AI enhancement off: https://github.com/Beingpax/VoiceInk/issues/990
- VoiceInk's filler filter removed the Spanish word "ha" ("No ha funcionado" became "No funcionado"); the reporter notes "the cause of the problem is hard to diagnose. It looks like the voice model is just broken": https://github.com/Beingpax/VoiceInk/issues/587
- Handy's filler removal removes the German "um": https://github.com/cjpais/Handy/issues/1275
- Handy's filler removal removes the Portuguese article "um": https://github.com/cjpais/Handy/issues/941
- The same Portuguese "um" was reported again months later as "consistently omitted" across every local model, which pointed to the pipeline rather than the recognizer: https://github.com/cjpais/Handy/issues/1718
- A hallucination filter in another open-source tool silently discards dictations consisting of one ordinary word such as "Okay" or "Thanks", because those strings are on its phantom-phrase list: https://github.com/BootBlock/SpectraWrite/issues/38
- An output length guard rejects a correct self-correction ("um so let's meet on tuesday no wait thursday" cleaned to "Let's meet Thursday.") so the raw text is typed instead: https://github.com/BearFlinn/speech-playground/issues/4
- VoiceInk's default enhancement, given a single word, "either returns an empty string, or it says 'okay'": https://github.com/Beingpax/VoiceInk/issues/26
- VoiceInk's word-replacement rule `ERN`→`EAN` fired inside "vergrößern" because the boundary check treated "ß" as a boundary: https://github.com/Beingpax/VoiceInk/issues/756
- OpenWhispr's docs concede that after cleanup "occasionally, the text isn't quite what you said" and suggest turning cleanup off when exact wording matters. Vendor admission: https://docs.openwhispr.com/help/dictation/cleanup.md
- A Superwhisper user reports mid-sentence periods with the next two words merged and lowercased ("and I are all on" became "and I. are allon"), occurring across two speech models and two language models, which they attribute to the LLM rewriting step: https://superwhisper.userjot.com/board/p/premature-sentence-periods-and-merging-of-next-two-words-in

### 2. Words lost by capture or recognition (out of scope for a text bench, reported for weighting)

Count: 23 distinct complaints. These dominate the open-source issue trackers.

- First words dropped after push-to-talk (Bluetooth profile switch, mic warm-up): https://github.com/Beingpax/VoiceInk/issues/996, https://github.com/Beingpax/VoiceInk/issues/385, https://github.com/cjpais/Handy/issues/1283, https://github.com/cjpais/Handy/issues/1879, and an HN commenter whose Handy dictation "cut off the words [I'm using] at the beginning": https://news.ycombinator.com/item?id=47052621
- Last word cut off because recording stops the instant the key is released; the reporter measured that 351 of their 783 dictations ended mid-word: https://github.com/Beingpax/VoiceInk/issues/1025; also https://github.com/cjpais/Handy/issues/1983 and https://github.com/cjpais/Handy/issues/963
- Whole middle sections or most of a long recording missing (VAD, decoder token budgets, streaming decoder stalls): https://github.com/Beingpax/VoiceInk/issues/853 (a 168 s dictation yielded 103 characters with VAD on versus 1,902 with it off), https://github.com/Beingpax/VoiceInk/issues/727, https://github.com/Beingpax/VoiceInk/issues/67, https://github.com/cjpais/Handy/issues/2125, https://github.com/cjpais/Handy/issues/1835, https://github.com/cjpais/Handy/issues/1323, https://github.com/cjpais/Handy/issues/2087
- History correct but pasted output missing fragments: https://github.com/cjpais/Handy/issues/2126
- Whole dictations lost: Superwhisper "No Result" on 5 of a user's last 10 dictations: https://superwhisper.userjot.com/board/p/buggy-app-july-2025; Wispr Flow App Store reviews "it keeps on losing my transcription every time I do something long-form" and "there's an error with the transcription and nothing can be found": https://apps.apple.com/us/app/wispr-flow-ai-voice-keyboard/id6497229487?see-all=reviews; Spokenly review of "a composition that it deleted itself": https://apps.apple.com/us/app/spokenly-whisper-dictation-ai/id6740315592?see-all=reviews
- Aqua Voice "missing words" and losing everything when the wrong key ends a session: https://news.ycombinator.com/item?id=39914355, https://news.ycombinator.com/item?id=43643663
- Apple dictation on iOS 27 "drops large chunks of words": https://discussions.apple.com/thread/256364267

### 3. Invented words and hallucinated content

Count: 13 distinct complaints plus 1 vendor article.

- Superwhisper appends text never dictated: a looping "The world is a world of the world", trailing "You" or "thank you" that appear "very regularly", Chinese words appended to an English architectural dictation, "a sprinkle of gibberish at the end": https://superwhisper.userjot.com/board/p/hallucination-added-to-end-of-output
- The same trailing "thank you", "okay", "I like it" reported alongside the period-merge bug: https://superwhisper.userjot.com/board/p/premature-sentence-periods-and-merging-of-next-two-words-in
- Superwhisper iOS review: "it randomly deletes a word you just typed or inserts a word you never typed": https://apps.apple.com/us/app/superwhisper-ai-dictation/id6471464415?see-all=reviews
- VoiceInk "terrible transcription hallucination sometimes": https://github.com/Beingpax/VoiceInk/issues/151
- VoiceInk repeats phrases ("to test to test the transcription"): https://github.com/Beingpax/VoiceInk/issues/235
- Handy: saying "two two" yields eleven "two"s with Parakeet: https://github.com/cjpais/Handy/issues/649
- Whisper's silence hallucinations ("Thank you for watching!", "Please subscribe") typed into apps: https://github.com/OpenWhispr/openwhispr/issues/462, https://github.com/AshiqIqbal1/Whisperlet/issues/58, https://github.com/saurabhav88/EnviousWispr/issues/3801
- Apple dictation after an iOS update: "I have to correct whole phrases that it seems to have invented" (10 "me too" votes): https://discussions.apple.com/thread/254577562
- Apple dictation briefly writing a commenter's siblings' names for an unrelated word, and the "racist" to "Trump" substitution thread: https://news.ycombinator.com/item?id=43172472, https://news.ycombinator.com/item?id=43172037
- An Aqua Voice launch commenter asks to turn off or clearly mark the feature "Forgot a name, word, fact, or number? Just ask Aqua to fill it in for you", because content the user did not say gets inserted: https://news.ycombinator.com/item?id=39831259
- Superwhisper's docs describe hallucinations as "Words you never said, repeated phrases, or content the AI added on its own" and separate the transcription stage from the AI-processing stage: https://superwhisper.com/docs/common-issues/hallucinations

### 4. The model answers or comments instead of cleaning (assistant-mode breakout)

Count: 6 distinct complaints plus 1 vendor article. This category is not in the appendix's list.

- Handy pasted "I have cleaned the provided transcript. This involved correcting spelling..." instead of the transcript: https://github.com/cjpais/Handy/issues/1201
- Handy sends the transcript as a bare user message "so some models treat it as an instruction": https://github.com/cjpais/Handy/issues/2269
- Spokenly review: "sometimes instead of transcribing what i'm dictating it gives me a response to what i've said": https://apps.apple.com/us/app/spokenly-whisper-dictation-ai/id6740315592?see-all=reviews
- Whispering user: "despite an extreme amount of prompt engineering, I can't seem to stop the transformation model occasionally responding to my message rather than just transforming it"; the maintainer replies that when formatting a dictated prompt, "Instead of formatting, it executes the prompt": https://news.ycombinator.com/item?id=44950090, https://news.ycombinator.com/item?id=44963448
- Voicebox: "the app currently interprets my speech as a query and attempts to provide a generated 'answer'": https://github.com/jamiepine/voicebox/issues/845
- VoiceInk: a trivial custom prompt is followed only sometimes ("I told him hello" becomes "I told him goodbye.", but "hello" alone does not): https://github.com/Beingpax/VoiceInk/issues/976
- Superwhisper docs list "The AI answers a question you didn't ask" and "Comments or content appear that weren't part of your dictation" as known AI-stage failures: https://superwhisper.com/docs/common-issues/hallucinations

### 5. Over-rewriting, wording changed, unwanted "polish"

Count: 8 distinct complaints plus 2 vendor admissions (the two Wispr admissions in section 1 also belong here).

- Users ask for a cleanup intensity control, citing Wispr Flow's None / Light / Medium levels, to limit "how much the AI Formatter is allowed to change the original wording": https://github.com/moona3k/macparakeet/issues/1213
- A TypeWhisper request wants fillers and self-corrections removed "while preserving names, facts, intended meaning, personal tone, and important wording": https://github.com/TypeWhisper/typewhisper-mac/issues/1350
- A Talon user prefers commands to "guessing and constructing a human language vague sentence and hope that an llm will work it out": https://news.ycombinator.com/item?id=43637965
- Text revised after the user has reviewed it: an Apple Community poster criticizes dictation "revising text after the user has reviewed it" (https://discussions.apple.com/thread/255282714); an Aqua user sees "one set of words, blink, and then it's replaced with a new recognition result" (https://news.ycombinator.com/item?id=43643663); an HN commenter notes Apple "shows it and then changes it" (https://news.ycombinator.com/item?id=43172551)
- AI Polish translated German dictation into English instead of correcting it: https://github.com/ynkjohn/JasperVoice/issues/3
- A Handy user wants the opposite, grammar cleanup, and notes "it just records your words exactly as is": https://news.ycombinator.com/item?id=49810584
- Superwhisper's docs: with language set to Automatic, "non-English dictation sometimes comes out as English text": https://superwhisper.com/docs/common-issues/language-detection.md
- Wispr Flow's docs list what Smart Formatting changes without asking: expands "gonna", favours one-word compounds, converts spoken numbers to digits, creates "implied lists" and removes spoken markers like "first" and "finally": https://docs.wisprflow.ai/articles/6568835559-why-wispr-flow-sometimes-removes-or-changes-words-on-android-smart-formatting

### 6. Punctuation and casing

Count: 14 distinct complaints. This is the largest single category on Apple's forums, where a single thread about random commas accumulated 172 replies.

- Apple dictation inserting random commas after iOS 16 (172 replies; fix was to disable Auto-Punctuation and Smart Punctuation): https://discussions.apple.com/thread/254440812
- "The dictation feature is driving me nuts by inserting commas all over the place" and the toggle to stop it is missing (14 "me too"): https://discussions.apple.com/thread/254860290
- Unwanted commas and periods on macOS after updates: https://discussions.apple.com/thread/255282714
- Random punctuation plus invented phrases; "Turning off auto punctuation made dictation usable again": https://discussions.apple.com/thread/254577562
- iOS 27 inserts commas "every other word" even with Auto-Punctuation off; no confirmed fix: https://discussions.apple.com/thread/256364267
- Superwhisper iOS review: "It insists on supplying all of its own punctuation" and it cannot be turned off: https://apps.apple.com/us/app/superwhisper-ai-dictation/id6471464415?see-all=reviews
- Superwhisper deprecated literal punctuation; a long-time Dragon user says "Literal punctuation and custom vocabulary are the only requirements" to switch, and the maintainer answers that the model "does a lot of punctuation replacement" so a literal mode cannot be made dependable (22 votes): https://superwhisper.userjot.com/board/p/preserve-and-improve-literal-punctuation
- Mid-sentence period with following words merged and lowercased: https://superwhisper.userjot.com/board/p/premature-sentence-periods-and-merging-of-next-two-words-in
- VoiceInk adds a period after ">" and "-" despite prompt rules: https://github.com/Beingpax/VoiceInk/issues/666
- VoiceInk always capitalizes and adds a trailing period, which is wrong when inserting "a short phrase, half a sentence or a single word": https://github.com/Beingpax/VoiceInk/issues/378
- VoiceInk: "sometimes the first letter is not capitalized" and no line breaks: https://github.com/Beingpax/VoiceInk/issues/320
- On-device models "don't handle punctuation commands on their own": https://news.ycombinator.com/item?id=49811276
- Saying "parentheses word parentheses" or "strike that" just gets written out: https://news.ycombinator.com/item?id=43640654
- Windows voice typing output with no punctuation and "1" for "when", "ridden" for "written": https://news.ycombinator.com/item?id=43640084

### 7. Self-corrections and restarts not resolved

Count: 5 user complaints plus 5 developer issues that treat it as a known gap.

- "the models can't properly filter out the pauses, 'uuuuhmms', and much less so handle on the fly corrections to what I've been saying, like going back and repeating something with a slight variation": https://news.ycombinator.com/item?id=44946603
- "strike that" is written out literally: https://news.ycombinator.com/item?id=43640654
- Siri dictation, told to go back and delete something, "will just write out 'go back and delete something'": https://news.ycombinator.com/item?id=43638349
- A decade-old gripe restated on the Superwhisper launch thread: "It says a word wrong. Scratch that. I say the whole line again": https://news.ycombinator.com/item?id=37211863
- A user with vocal strain and RSI asks Superwhisper for spoken self-correction commands because highlighting text is "very hand-intensive": https://superwhisper.userjot.com/board/p/editing-in-superwhisper
- Developer issues implementing it: "meet at three, no, four" becomes "meet at four" (https://github.com/marknutter/codictate/issues/13); "no wait", "I mean", "scratch that", "actually" detection, citing "a category-wide friction analysis of Handy, VoiceInk, Superwhisper, Wispr Flow, and whispering issue trackers" (https://github.com/jamditis/audiobud/issues/192); streaming-aware "scratch that" (https://github.com/peteonrails/voxtype/issues/902); correction by restatement without a trigger word, "as a gift, as a present" (https://github.com/uttrflow/uttrflow-swift/issues/3632); a length guard rejecting a valid correction (https://github.com/BearFlinn/speech-playground/issues/4)
- No opened page contained a user complaint specifically about corrections that replace the interrogative phrase ("where is… or what city has…"). The vault's finding on that category is neither confirmed nor contradicted by this evidence.

### 8. Fillers

Count: 5 complaints or requests. In English this reads as a solved expectation rather than an active pain; the active pain is the false positives in section 1.

- Requests to add deterministic filler removal: https://github.com/Starmel/OpenSuperWhisper/issues/161 (which deliberately excludes "er", "ah", "hmm" because they "have common legitimate uses"), https://github.com/anomalyco/hex/issues/97
- Filler removal on iOS only works when AI enhancement is on: https://github.com/Beingpax/VoiceInk/issues/821
- Users wanting an LLM "to remove all 'umm' and similar nonsense": https://news.ycombinator.com/item?id=44949860; and praising Whisper because "there's going to be no ums, there's going to be no ahs": https://news.ycombinator.com/item?id=45931364
- VoiceInk's own docs warn against adding "like", "right", "okay" to the filler list because they "often carry real meaning": https://tryvoiceink.com/docs/filler-words

### 9. Numbers and spoken forms

Count: 5 complaints. The pain runs in both directions.

- Over-normalization: "I scheduled it to post first thing Monday morning" became "1st thing"; "could save you thousands" became "1000s": https://github.com/Beingpax/VoiceInk/issues/428
- A hard-coded `numerals=true` turned "step one" into "step 1" against the user's wish: https://github.com/Beingpax/VoiceInk/issues/895
- Under-normalization: a request to convert spoken numbers to digits, with the maintainer noting "this is sometimes called inverse text normalization": https://github.com/cjpais/Handy/issues/611
- "1" for "when": https://news.ycombinator.com/item?id=43640084
- "two two" collapsing into a repetition loop: https://github.com/cjpais/Handy/issues/649

### 10. Names, jargon and vocabulary

Count: 12 complaints. Mostly a recognizer problem, but the cleanup layer is where several products try to fix it.

- "'malloc,' 'memcpy,' 'Axum,' 'Tauri'… these always had to be edited" with macOS dictation: https://news.ycombinator.com/item?id=42460676
- "JSON becomes Jason": https://news.ycombinator.com/item?id=45932213
- "It's Erin with an E. Oh for **s sake, Erin. ERIN!": https://news.ycombinator.com/item?id=39830024
- "extreme acronym rich lingo" with thousands of acronyms: https://news.ycombinator.com/item?id=39830884
- iOS dictation "not as accurate with bespoke technical words / acronyms": https://news.ycombinator.com/item?id=44948163
- Post-processing exists "to have correctly spelled names when replying to emails", at the cost of a 5 to 10 second pipeline: https://news.ycombinator.com/item?id=47040867, https://news.ycombinator.com/item?id=47041361
- Dictionaries that do not stick: "have to build a dictionary over time" (Wispr Flow review, https://apps.apple.com/us/app/wispr-flow-ai-voice-keyboard/id6497229487?see-all=reviews); custom dictionary words "save temporarily and then they go away" (Monologue review, https://apps.apple.com/us/app/monologue-smart-dictation/id6755956193?see-all=reviews)
- Casing fixes rejected: "iphone → iPhone" treated as a loop: https://github.com/Beingpax/VoiceInk/issues/961
- Vocabulary should reach the LLM so spellings are corrected even when the recognizer cannot take a vocabulary: https://github.com/Beingpax/VoiceInk/issues/250
- Replacement rules that never match CJK text: https://github.com/anomalyco/hex/issues/177
- Wispr Flow's support form has dedicated report types "Important word transcribed incorrectly" and "Name transcribed incorrectly": https://docs.wisprflow.ai/articles/7837779518-getting-help-with-wispr-flow-reporting-flagging-and-contacting-support

### 11. Lists, line breaks and layout

Count: 4 complaints plus 1 vendor behaviour.

- "it cannot break lines and also bullet points like some of your competitors do. So it generates long text very annoying like this one": https://github.com/Beingpax/VoiceInk/issues/320
- Handy "doesn't enter paragraph breaks": https://news.ycombinator.com/item?id=47052621
- Aqua turned a list into a table on request, then "converted back into a list when I asked it to turn the text into an email": https://news.ycombinator.com/item?id=39834197
- A user configures Aqua with "Use lowercase in Slack and iMessage" and paragraph-length rules, showing layout is a per-app preference: https://news.ycombinator.com/item?id=43638122
- Wispr Flow "creates implied lists" and removes "first" and "finally" without being asked: https://docs.wisprflow.ai/articles/6568835559-why-wispr-flow-sometimes-removes-or-changes-words-on-android-smart-formatting

### 12. Wrong language, English-only cleanup

Count: 4 new complaints, plus items already counted in sections 1 and 5. Not in the appendix's list.

- Cleanup models that are English-only leave Spanish fillers and corrections untouched, with nothing in the UI saying so: https://github.com/Muesli-HQ/muesli/issues/463
- Polish spoken to Voxtral came out as Russian: https://news.ycombinator.com/item?id=49081002
- German translated to English by an AI polish step: https://github.com/ynkjohn/JasperVoice/issues/3
- Superwhisper's most-voted board post asks the AI stage to follow the detected language (the page shows 124 votes): https://superwhisper.userjot.com/board/p/auto-language-detection
- Superwhisper's language-detection article (section 5) and the four filler false positives in German, Spanish and Portuguese (section 1) are the same pain seen from the vendor side.

### 13. Accent and speaker variation (recognizer, not cleanup)

Count: 3. "every time I said 'test' it would write 'taste'" (https://news.ycombinator.com/item?id=39829688); "All 'normal' voice programs struggle with us non-native speakers" (https://news.ycombinator.com/item?id=39834269); a full-time voice user with a "kiwi accent" (https://news.ycombinator.com/item?id=43641249).

### 14. Latency, privacy, pricing (noted, not weighted)

Latency: a post-processing pipeline taking "5-10 seconds per transcription" (https://news.ycombinator.com/item?id=47040867) and 25 seconds for a long ramble on a laptop CPU (https://news.ycombinator.com/item?id=47052621). Privacy: refusal to use a cloud input method (https://news.ycombinator.com/item?id=43637679), confusion when a "local-first" app's demo starts with API keys (https://news.ycombinator.com/item?id=44945712), and Apple's disclosure that dictation "sends information like your voice input, contacts, and location to Apple" (https://news.ycombinator.com/item?id=49079055). These shape the adapter list and the latency table, not the item categories.

### 15. The cross-cutting cost: proofreading and trust

- Larson and Mowatt (2003), full text: "Users spend much more time correcting errors than they spend dictating new text" and "Participants still spend approximately 10 times longer correcting ASR errors than they are entering new text." They also report that "32% of corrections are necessitated by the need to correct new problems created during an earlier correction attempt" in the Karat et al. (1999) study they build on. https://www.microsoft.com/en-us/research/uploads/prod/2021/06/Larson-Mowatt-2003-speech-error-correction-the-story-of-the-alternates-list.pdf
- A full-time voice user: "It's also critically important (and after 3-4 years of this I still regularly fail at this) to actually read what you've written, and edit it before send": https://news.ycombinator.com/item?id=43641249
- The Wispr Flow user above: they must reread everything, "voice errors can change meaning and cause real damage": https://digg.com/ai/ve5pkh0s
- Karat, Halverson, Horn and Karat (1999), CHI, and Hong and Findlater (2018), CHI, were confirmed by title, authors and venue only (ACM returned 403; Semantic Scholar had no abstract). Their findings are not quoted here.

### Summary table (counts are of opened pages)

| Category | Distinct complaints opened | Cleanup layer can cause it? | Text bench can measure it? |
| --- | --- | --- | --- |
| 1. Words lost by cleanup (meaning drops, filler false positives, guard discards) | 11 (+3 vendor admissions) | Yes | Yes |
| 2. Words lost by capture or recognition | 23 | No | No |
| 3. Invented or hallucinated content | 13 (+1 vendor) | Partly (AI stage) | Yes, for the AI stage |
| 4. Answers or comments instead of cleaning | 6 (+1 vendor) | Yes | Yes |
| 5. Over-rewriting, wording changed | 8 (+2 vendor) | Yes | Yes |
| 6. Punctuation and casing | 14 | Yes | Yes |
| 7. Self-corrections and restarts | 5 (+5 developer issues) | Yes | Yes |
| 8. Fillers | 5 | Yes | Yes |
| 9. Numbers and spoken forms | 5 | Yes | Yes |
| 10. Names, jargon, vocabulary | 12 | Partly | Partly (spelling and casing given a vocabulary) |
| 11. Lists, line breaks, layout | 4 (+1 vendor) | Yes | Yes |
| 12. Wrong language, English-only cleanup | 4 (+ overlaps with 1 and 5) | Yes | Partly (passthrough of non-English tokens) |
| 13. Accent | 3 | No | No |

Reading: once capture and recognizer failures are set aside, the complaints
that users describe as damaging are the cleanup layer removing or changing a
meaningful word (category 1 and 5), the layer adding content or answering
(3 and 4), and punctuation imposed where it was not wanted (6). Fillers (8)
and self-corrections (7) are what products advertise, and the complaints about
them are mostly that the handling is missing or unreliable, not that it is
dangerous. Names and numbers (9, 10) are frequent but are usually recognizer
errors that cleanup is asked to repair.

## What is recommended

### Weighting the appendix's eleven categories

The appendix proposes: fillers, restarts, correction-intra, correction-cross,
correction-interrogative, punctuation-casing, spoken-form, names-vocabulary,
lists-layout, negatives, adversarial-meaning. Against the evidence above:

1. **Make `negatives` the heaviest category, and split it into named slices.** Category 1 is where users report real harm. The slices the evidence calls for: negation words (`not`, `never`, `before`) that must survive; content words that look like fillers (`like a charm`, `you know what I mean`, leading `so`, deliberate repetition); non-English words inside English speech that match English filler strings (German `um`, Spanish `ha`, Portuguese `um`); already-clean input; and single-word or fragment inputs (`Okay`, `Thanks`, `go ahead`) that must come back as text, not as nothing. The first and last of these are not in the appendix today.
2. **Add a category for instruction-like input** (or widen `adversarial-meaning` into it). Dictating a question, dictating about the cleanup rules, or dictating a prompt must come back as cleaned dictation, not as an answer, a commentary or an echo-with-analysis. Seven complaints and one vendor doc describe exactly this failure. The engine's guard tests already pin several of these shapes; the bench should score them as items.
3. **Keep `punctuation-casing` heavily weighted, and score over-punctuation as an error, not only missing punctuation.** The Apple threads are about commas added, not commas missing. Include fragment inputs where the expected output is *not* sentence-cased and *not* period-terminated, and spoken-command inputs ("parentheses", "new line") whose handling must be stated in the task definition.
4. **Keep the three self-correction categories but do not inflate their weight from the user side.** The user evidence is real but thin (five complaints); the developer evidence shows it is a known gap that several tools are now building. The interrogative-phrase category has no user complaint behind it in the pages opened; its justification remains the vault's out-of-distribution finding, which this file neither confirms nor contradicts.
5. **Lower `fillers` to a baseline category.** English filler removal is an expectation, not a pain. The real risk is the false positive, which belongs in `negatives`.
6. **Give `spoken-form` two-sided items.** Include cases where the reference keeps words ("first thing Monday", "save you thousands", "step one") as well as cases where digits are right. The complaints run both ways.
7. **Scope `names-vocabulary` to what cleanup can do:** honour a supplied vocabulary's spelling and casing (`iPhone`), do not "correct" a vocabulary term, do not alter a name that is not in the vocabulary. Recognizer misspellings of names are out of scope and should be stated as such.
8. **Give `lists-layout` an unrequested-list negative.** The vendor behaviour "creates implied lists" and removes "first"/"finally" is a documented over-clean; the appendix's `lists-layout` should contain inputs where a list is *not* invited and the reference keeps prose.
9. **Add a `wrong-language` note to the task definition rather than a category.** The bench is English. State it, and include the non-English-token passthrough items under `negatives` so an English-only model that deletes or translates a foreign word is caught.

### Pain the appendix does not cover

- Assistant-mode breakout (section 4). Recommend a category.
- Negation preservation (section 1, the Wispr example). Recommend a `negatives` slice with `must_contain` slots on the negation word.
- Fragment and single-word inputs (sections 1 and 6). Recommend a `negatives` slice whose references are unchanged or minimally cased, and a rule in the task definition about sentence-final punctuation on fragments. This may conflict with the engine's guard behaviour and with the vault's "already-clean" negatives, which are full sentences; flag for decision.
- Capture and recognizer truncation, silence hallucinations ("Thank you for watching"), accent, and wrong-language recognition (sections 2, 3 in part, 12, 13). Recommend stating explicitly that these are out of scope for a text-to-text bench, and that cleanup is *not* expected to delete recognizer hallucinations, because it cannot tell them from speech and the first law forbids the guess. Whether to include a small diagnostic slice of inputs with a trailing "Thank you." whose reference keeps it is a decision to put in the summary.
- Text revised after the user has read it (section 5). Not a bench item, but it argues for the leaderboard to report the `unchanged` and `fallback` rates the appendix already lists, since a stable output is itself what users ask for.

### Caveats on this evidence

Reddit, the largest consumer discussion venue for these apps, was unreachable, and the Monologue feedback board is offline, so complaints specific to Monologue and to the consumer Reddit audience are under-represented. App Store pages show ten reviews each. The open-source issue trackers over-represent capture bugs because those are the bugs that get filed against code. The counts are therefore a ranking of what could be read, not a measurement of prevalence.

## Sources

Each entry: URL, access date, what it contributed.

Hacker News (retrieved through hn.algolia.com/api/v1/items/<id>; cited by HN URL)

- https://hn.algolia.com/api/v1/search?query=Wispr%20Flow&tags=story (and the same endpoint for "Superwhisper", "Aqua Voice", "VoiceInk", "Handy dictation", "macOS dictation", "voice dictation", "whisper dictation"), 2026-10-24, located the story threads below.
- https://news.ycombinator.com/item?id=47040375, 2026-10-24, "Free alternative to Wispr Flow, Superwhisper, and Monologue": name-spelling post-processing, latency, cut-off first words, no paragraph breaks.
- https://news.ycombinator.com/item?id=44942731, 2026-10-24, "Whispering": transformation model answering instead of transforming; filler and correction handling wished for; privacy confusion.
- https://news.ycombinator.com/item?id=39828686, 2026-10-24, Aqua Voice launch: accent errors, "fill it in for you" concern, acronyms, "Erin with an E", missing words, list-to-table behaviour.
- https://news.ycombinator.com/item?id=43634005, 2026-10-24, Aqua Voice 2: Talon user on guessing, Siri writing commands out literally, Windows output errors, text replaced after display, "strike that" written out, kiwi accent, proofreading burden.
- https://news.ycombinator.com/item?id=37204722, 2026-10-24, superwhisper launch: "Scratch that. I say the whole line again."
- https://news.ycombinator.com/item?id=49809670, 2026-10-24, non-cloud Wispr alternatives: punctuation commands, "records your words exactly as is", tech jargon.
- https://news.ycombinator.com/item?id=49073834, 2026-10-24, Yap: Apple dictation privacy disclosure; Polish-to-Russian with Voxtral.
- https://news.ycombinator.com/item?id=45930659, 2026-10-24, Chirp: "JSON becomes Jason"; Whisper removing ums.
- https://news.ycombinator.com/item?id=42460676, 2026-10-24, Careless Whisper: "malloc, memcpy, Axum, Tauri" with macOS dictation.
- https://news.ycombinator.com/item?id=43172037, 2026-10-24, Apple dictation "racist" to "Trump": substitution, siblings' names, shows-then-changes.
- https://news.ycombinator.com/item?id=43177774, 2026-10-24, follow-up (Apple fixing the bug); no further complaint content.
- https://news.ycombinator.com/item?id=49475159, 2026-10-24, FnScribe: no cleanup complaints beyond "whisper is pretty outdated vs parakeet".
- https://news.ycombinator.com/item?id=49582352, 2026-10-24, "I hate Wispr Flow so much": links a New York Times Magazine essay that could not be opened.
- https://news.ycombinator.com/item?id=46264158, https://news.ycombinator.com/item?id=48703848, https://news.ycombinator.com/item?id=48897934, https://news.ycombinator.com/item?id=49279064, https://news.ycombinator.com/item?id=49364361, https://news.ycombinator.com/item?id=49375265, https://news.ycombinator.com/item?id=49405912, https://news.ycombinator.com/item?id=34149275, 2026-10-24, opened; no cleanup complaints found in their comments.

GitHub issues (retrieved through the GitHub API; cited by HTML URL)

- https://github.com/Beingpax/VoiceInk/issues/26, 2026-10-24, single words return empty or "okay".
- https://github.com/Beingpax/VoiceInk/issues/45, 2026-10-24, enhancements not applied (configuration); not counted.
- https://github.com/Beingpax/VoiceInk/issues/67, 2026-10-24, empty or heavily trimmed recording.
- https://github.com/Beingpax/VoiceInk/issues/151, 2026-10-24, hallucination.
- https://github.com/Beingpax/VoiceInk/issues/235, 2026-10-24, repeated words or incomplete.
- https://github.com/Beingpax/VoiceInk/issues/250, 2026-10-24, vocabulary via the LLM prompt.
- https://github.com/Beingpax/VoiceInk/issues/320, 2026-10-24, no line breaks or bullets, first letter not capitalized.
- https://github.com/Beingpax/VoiceInk/issues/378, 2026-10-24, forced capitalization and periods on fragments.
- https://github.com/Beingpax/VoiceInk/issues/385, 2026-10-24, first words missing.
- https://github.com/Beingpax/VoiceInk/issues/428, 2026-10-24, "1st thing", "1000s".
- https://github.com/Beingpax/VoiceInk/issues/587, 2026-10-24, Spanish "ha" removed as filler.
- https://github.com/Beingpax/VoiceInk/issues/666, 2026-10-24, period after ">" and "-".
- https://github.com/Beingpax/VoiceInk/issues/727, 2026-10-24, long transcriptions cut in the middle.
- https://github.com/Beingpax/VoiceInk/issues/756, 2026-10-24, replacement rule fires inside words.
- https://github.com/Beingpax/VoiceInk/issues/821, 2026-10-24, iOS filler removal needs AI enhancement.
- https://github.com/Beingpax/VoiceInk/issues/853, 2026-10-24, VAD discards most audio.
- https://github.com/Beingpax/VoiceInk/issues/895, 2026-10-24, forced numerals.
- https://github.com/Beingpax/VoiceInk/issues/961, 2026-10-24, case-only replacements rejected.
- https://github.com/Beingpax/VoiceInk/issues/976, 2026-10-24, flaky custom prompt.
- https://github.com/Beingpax/VoiceInk/issues/990, 2026-10-24, German "um" removed as filler.
- https://github.com/Beingpax/VoiceInk/issues/996, 2026-10-24, push-to-talk late start.
- https://github.com/Beingpax/VoiceInk/issues/1025, 2026-10-24, last word cut off, with measurements.
- https://github.com/cjpais/Handy/issues/611, 2026-10-24, request for digits.
- https://github.com/cjpais/Handy/issues/649, 2026-10-24, "two two" repetition.
- https://github.com/cjpais/Handy/issues/941, 2026-10-24, Portuguese "um" removed.
- https://github.com/cjpais/Handy/issues/963, 2026-10-24, tail cut off.
- https://github.com/cjpais/Handy/issues/1201, 2026-10-24, LLM instructions pasted instead of transcript.
- https://github.com/cjpais/Handy/issues/1275, 2026-10-24, German "um" removed.
- https://github.com/cjpais/Handy/issues/1283, 2026-10-24, mic initialization delay.
- https://github.com/cjpais/Handy/issues/1323, 2026-10-24, Cohere cuts off long text.
- https://github.com/cjpais/Handy/issues/1718, 2026-10-24, Portuguese "um" omitted across models.
- https://github.com/cjpais/Handy/issues/1835, 2026-10-24, Moonshine partial transcription.
- https://github.com/cjpais/Handy/issues/1879, 2026-10-24, first 0.5 to 3 s lost.
- https://github.com/cjpais/Handy/issues/1983, 2026-10-24, last word missing.
- https://github.com/cjpais/Handy/issues/2087, 2026-10-24, 256-token truncation.
- https://github.com/cjpais/Handy/issues/2125, 2026-10-24, streaming decoder drops most of transcript.
- https://github.com/cjpais/Handy/issues/2126, 2026-10-24, pasted output missing parts.
- https://github.com/cjpais/Handy/issues/2269, 2026-10-24, transcript treated as instruction.
- https://github.com/anomalyco/hex/issues/97, 2026-10-24, restore filler removal.
- https://github.com/anomalyco/hex/issues/177, 2026-10-24, replacements never match CJK.
- https://github.com/OpenWhispr/openwhispr/issues/462, 2026-10-24, silence hallucinations.
- https://github.com/AshiqIqbal1/Whisperlet/issues/58, 2026-10-24, silence hallucinations typed into apps.
- https://github.com/saurabhav88/EnviousWispr/issues/3801, 2026-10-24, trailing "Thank you".
- https://github.com/marknutter/codictate/issues/13, 2026-10-24, self-correction cleanup design.
- https://github.com/jamditis/audiobud/issues/192, 2026-10-24, self-correction handling request.
- https://github.com/peteonrails/voxtype/issues/902, 2026-10-24, streaming "scratch that".
- https://github.com/jamiepine/voicebox/issues/845, 2026-10-24, dictation acts as chat.
- https://github.com/moona3k/macparakeet/issues/1213, 2026-10-24, cleanup intensity levels.
- https://github.com/Muesli-HQ/muesli/issues/463, 2026-10-24, English-only cleanup models.
- https://github.com/ynkjohn/JasperVoice/issues/3, 2026-10-24, polish translates German to English.
- https://github.com/BearFlinn/speech-playground/issues/4, 2026-10-24, length guard rejects valid self-correction.
- https://github.com/BootBlock/SpectraWrite/issues/38, 2026-10-24, hallucination filter discards "Okay"/"Thanks".
- https://github.com/Starmel/OpenSuperWhisper/issues/161, 2026-10-24, filler removal request with false-positive reasoning.
- https://github.com/uttrflow/uttrflow-swift/issues/3632, 2026-10-24, correction by restatement.
- https://github.com/TypeWhisper/typewhisper-mac/issues/1350, 2026-10-24, concise mode preserving meaning.
- GitHub-wide searches run: "dictation filler words removed", "dictation hallucination thank you", "dictation self-correction OR scratch that"; epicenter-so/epicenter searches returned nothing for the terms used.

Vendor boards and documentation

- https://superwhisper.userjot.com/board/p/hallucination-added-to-end-of-output, 2026-10-24, appended text never dictated.
- https://superwhisper.userjot.com/board/p/premature-sentence-periods-and-merging-of-next-two-words-in, 2026-10-24, mid-sentence periods, lowercase merges, trailing phrases.
- https://superwhisper.userjot.com/board/p/preserve-and-improve-literal-punctuation, 2026-10-24, literal punctuation deprecated.
- https://superwhisper.userjot.com/board/p/buggy-app-july-2025, 2026-10-24, "No Result" on half of dictations.
- https://superwhisper.userjot.com/board/p/editing-in-superwhisper, 2026-10-24, spoken self-correction commands wanted by a user with RSI.
- https://superwhisper.userjot.com/, https://superwhisper.userjot.com/board/features, https://superwhisper.userjot.com/board/search?q=words, 2026-10-24, board listings; auto-language-detection post vote count.
- https://superwhisper.userjot.com/board/p/auto-language-detection, 2026-10-24, listed on the board pages above (title and vote count only; the post itself was not opened).
- https://superwhisper.com/docs/common-issues, 2026-10-24, vendor's list of known output problems.
- https://superwhisper.com/docs/common-issues/hallucinations, 2026-10-24, two-stage hallucination description.
- https://superwhisper.com/docs/common-issues/language-detection.md, 2026-10-24, non-English comes out as English.
- https://docs.wisprflow.ai/articles/6568835559-why-wispr-flow-sometimes-removes-or-changes-words-on-android-smart-formatting, 2026-10-24, what Smart Formatting changes; meaningful words misread as filler.
- https://docs.wisprflow.ai/articles/7837779518-getting-help-with-wispr-flow-reporting-flagging-and-contacting-support, 2026-10-24, report categories including name and important-word errors.
- https://tryvoiceink.com/docs/filler-words, 2026-10-24, default filler list and warning about meaningful words.
- https://docs.openwhispr.com/help/dictation/cleanup.md, 2026-10-24, "occasionally, the text isn't quite what you said".
- https://feedback.monologue.to/, https://feedback.monologue.to/p/dictation-accuracy, https://feedback.monologue.to/p/mixed-language-dictation-accuracy-needs-improvement, 2026-10-24, all returned Vercel DEPLOYMENT_NOT_FOUND; not read.

App Store review pages

- https://apps.apple.com/us/app/wispr-flow-ai-voice-keyboard/id6497229487?see-all=reviews, 2026-10-24, lost long-form transcriptions, dictionary burden.
- https://apps.apple.com/us/app/superwhisper-ai-dictation/id6471464415?see-all=reviews, 2026-10-24, inserted and deleted words, forced punctuation.
- https://apps.apple.com/us/app/spokenly-whisper-dictation-ai/id6740315592?see-all=reviews, 2026-10-24, LLM responds instead of transcribing; deleted composition.
- https://apps.apple.com/us/app/monologue-smart-dictation/id6755956193?see-all=reviews, 2026-10-24, dictionary entries do not persist.
- https://apps.apple.com/us/app/aqua-voice-ai-voice-keyboard/id6759074969?see-all=reviews, 2026-10-24, ten praise-only reviews.

Apple Support Communities

- https://discussions.apple.com/thread/254440812, 2026-10-24, random commas after iOS 16 (172 replies).
- https://discussions.apple.com/thread/254860290, 2026-10-24, Auto-Punctuation toggle missing, commas everywhere (14 "me too").
- https://discussions.apple.com/thread/255282714, 2026-10-24, unwanted punctuation on macOS; revising text after review.
- https://discussions.apple.com/thread/254577562, 2026-10-24, invented phrases and random punctuation (10 "me too").
- https://discussions.apple.com/thread/256364267, 2026-10-24, iOS 27 over-punctuation and dropped chunks.
- https://discussions.apple.com/thread/254453112, 2026-10-24, redirected to sign-in; not read.
- https://discussions.apple.com/search?q=dictation+punctuation+wrong+words, 2026-10-24, returned no results to the fetcher.

Press, aggregators, other

- https://digg.com/ai/ve5pkh0s, 2026-10-24, relay of a user's X post about Wispr Flow dropping "not", "never", "before".
- https://x.com/theo/status/2102703393043005737, 2026-10-24, the original post; returned HTTP 402 and was not read.
- https://www.digitaltrends.com/computing/wispr-flow-asked-its-haters-what-was-wrong-and-more-than-700-people-answered/, 2026-10-24, Wispr's "overly aggressive Auto Cleanup" admission and the 700-response figure.
- https://releases.sh/wispr-flow, 2026-10-24, Wispr release notes; no Auto Cleanup entry found there.
- https://www.laxis.com/blog/wispr-flow/, 2026-10-24, third-party review citing a Trustpilot score; no text-quality complaints; not counted.
- https://www.trustpilot.com/review/wisprflow.ai, 2026-10-24, profile removed by Trustpilot.
- https://www.trustpilot.com/review/aquavoice.com, 2026-10-24, one review about stability; not counted.
- https://gummysearch.com/r/WisprFlow/, 2026-10-24, subreddit tag counts only; not counted.
- https://www.g2.com/products/wispr-flow/reviews, https://www.g2.com/products/wispr-flow/reviews_and_filters, https://www.trustradius.com/products/wispr-flow/reviews, https://www.producthunt.com/products/wispr-flow/reviews, https://alternativeto.net/software/wispr-flow/about/, 2026-10-24, HTTP 403 or 404; not read (the Alternativeto "about" page opened and showed one praise review, not counted).
- https://www.nytimes.com/2026/08/19/magazine/ai-dictation-app-wispr.html and https://archive.is/6mHF7, 2026-10-24, refused by the fetch tool; not read.
- https://old.reddit.com/search?q=wispr+flow+removes+words, https://www.reddit.com/r/macapps/search.json?q=wispr+flow, and six `reddit.com/search.json` queries via curl, 2026-10-24, all refused (fetch tool) or HTTP 403 (curl).

Academic

- https://www.microsoft.com/en-us/research/uploads/prod/2021/06/Larson-Mowatt-2003-speech-error-correction-the-story-of-the-alternates-list.pdf, 2026-10-24, full text; correction time versus dictation time; cascading corrections figure from Karat et al.
- https://www.microsoft.com/en-us/research/publication/speech-error-correction-the-story-of-the-alternates-list/, 2026-10-24, abstract and venue.
- https://api.semanticscholar.org/graph/v1/paper/DOI:10.1145/302979.303160, 2026-10-24, confirms Karat, Halverson, Horn, Karat (1999), CHI; no abstract returned.
- https://api.semanticscholar.org/graph/v1/paper/DOI:10.1145/3173574.3174141, 2026-10-24, confirms Hong and Findlater (2018), CHI; no abstract returned.
- https://dl.acm.org/doi/10.1145/302979.303160 and https://dl.acm.org/doi/10.1145/3173574.3174141, 2026-10-24, HTTP 403; not read.
- https://arxiv.org/abs/2602.22374, 2026-10-24, VoiceAlign (2026); abstract contains no dictation-error figures; not counted.

## Addendum 2026-10-27

Second attempt at Reddit, the venue the Limits section above names as the
largest unread one. Same rules as the rest of this file: a snippet is not a
source, every quote is short, no count is revised from memory.

### Found

**Direct routes are still closed.** With a browser User-Agent and with a
plain one, `www.reddit.com/search.json`, `www.reddit.com/r/<sub>/search.json`,
`www.reddit.com/r/WisprFlow/new.json`, `api.reddit.com/r/WisprFlow/new` and
thread `.json` URLs all returned HTTP 403. `old.reddit.com` returned HTTP 200
on every URL tried (site search, subreddit `.json`, thread `.json`) but served
a "Welcome to Reddit" interstitial with no results or post text. A
`www.reddit.com` thread HTML page returned 200 with the title "Reddit" and no
comment markup.

**Two archive mirrors answered.** `api.pullpush.io` returned HTTP 200 on
keyword searches of submissions (HTTP 429 on some subreddit listings), and
`arctic-shift.photon-reddit.com` returned HTTP 200 for subreddit post
listings, comment searches by subreddit plus body keyword, and post lookups by
id (its keyword search refuses a query without a subreddit or author, HTTP
400). Everything below comes from those mirrors and is cited by the Reddit URL
the mirror records; the live thread could not be opened to confirm any of it.
In the arctic-shift copy of r/WisprFlow the body of most posts reads
"[removed]" (7 of the 100 most recent posts carry a body); a 2025-12-16 post
there says "so they removed my post because it's a support request", so
complaint bodies on that subreddit are under-represented even in the mirror,
while titles and comments survive. r/superwhisper bodies are mostly intact
(87 of 100 most recent).

**Complaints found, mapped to the pains above.**

- *Words changed or meaning flipped by the cleanup layer* (§1). r/WisprFlow,
  "Long-time user, honestly the quality has been going downhill for months"
  (2026-06-08): "I get more word swaps and missed phrases than I used to"; a
  comment in that thread (2026-07-31): "Instead of 'I want' it becomes 'i dont
  want', and vice versa. Very dangerous when prompting". r/superwhisper, "How
  to stop Superwhisper changing what i say into something else - pro member"
  (2026-06-27): "when it changes entire sentences into something else that
  then changes the 'meaning' of what i said". r/superwhisper, "Inaccuracy pro
  member - refund?" (2026-06-27), comment of 2026-06-28: "its changing words,
  things like is to an, and other words and changing the whole meaning of the
  sentence" and "Its leaving out chunks of text". r/superwhisper, "Getting
  frustrated" (2026-05-30): the app "seems to recently take significant
  liberty in shortening/interpreting med-long dictation including taking out
  important pieces of the context". r/WisprFlow comment of 2026-06-22 on the
  vendor's "June 18, 2026 Product Updates" post: "I have to check and recheck
  every transcription for punctuation errors, capitalization errors, incorrect
  words that used to never be a problem".
- *Invented content* (§3). r/superwhisper, "Superwhisper Hallucinations"
  (2026-01-10), with a comment the same day: "With Super Wispr, I've had
  entire paragraphs added to the end of my dictated text"; "Why will
  superwhisper hallucinate and add in tons of random things I never said after
  some of my voice memos?" (2026-01-05); "Is superwhisper leaking the
  transcription text of other users to me?" (2025-07-26): from the third
  paragraph the output "is completely not what I said". r/WisprFlow comment of
  2026-08-18 on "Is accuracy back?": "it suddenly invents words that don't
  exist at all".
- *The model answers instead of cleaning* (§4). r/superwhisper, "Why is
  SuperWhisper answering my dictation rather than just transcribing it?"
  (2026-02-08): dictation "Hey how you doing", output "i'm doing good, how
  about you"; "Getting frustrated" (2026-05-30): "it tries to answer what I'm
  asking"; a comment of 2026-06-02 in that thread: message mode is
  "occasionally hallucinating an 'answer' to something you said as a
  question"; a comment of 2026-06-25 on "NEW: Superwhisper MCP and CLI":
  "there are times when it tries to answer the question instead of 'pasting
  the question.'"
- *Imposed punctuation, casing and layout* (§5, §6). r/WisprFlow, "Feature
  Request: Toggle for Basic vs. Full Auto-Punctuation" (2026-03-21): asks for a
  mode "that only inserts periods, exclamation points, and question marks when
  I explicitly say them"; "How to avoid inserting punctuation?" (2025-11-01):
  "I don't want it to insert a period after the text, such as my to do list or
  time tracker"; "Style preference - for comma separated lists versus bulleted
  lists?" (2025-12-06): a dictated comma-separated clinical list is formatted
  "as a bulleted list"; comment of 2026-10-21 on "Space before paste": "I
  cannot get Wispr to add a period at the end of a single sentence in Discord,
  even when I say 'period'". r/superwhisper, "Issue with Punctuations and
  Formatting" (2026-09-15): on saying "Period" or "New Paragraph" the software
  "will spell out those punctuations and formats instead of actually applying
  them"; "Inaccuracy pro member - refund?" comment: "It's putting in capitals
  where there shouldn't be."
- *Cleanup-level control.* Comment of 2026-06-15 on the vendor's "April 24,
  2026 Product Updates: Insights, Auto Cleanup, and more!": "how the hell is
  there no difference between 'Add punctuation where it's needed' and 'Change
  the actual words I said'? Light should never ever ever ever change my actual
  words, unless they are HOMOPHONES". The vendor's own post "Reliability and
  accuracy update: what happened, what's fixed, what's next" (2026-06-04):
  "The introduction of our new auto-cleanup setting may have affected other
  settings as well, and we're testing a rollback now."
- *Capture-side, out of scope* (§2). r/WisprFlow, "Latency issue cutting off
  the beginning of sentences." (2026-10-19, title only; body removed); the
  2026-07-31 comment above: "The first words are now generally always missed
  or messed up".

**Not found.** No post or comment in the mirrors about an interrogative-phrase
correction being mishandled; no complaint that fillers were left in. The
Reddit material repeats the pattern of the HN, GitHub and App Store sources
rather than adding a new failure class.

### What this changes

Nothing in the weighting. The four pains ranked highest in "Weighting the
appendix's eleven categories" (words changed, invented content, answering
instead of cleaning, imposed punctuation) gain consumer-side instances from
the largest venue that was missing; `correction-interrogative` still has no
user complaint behind it. The counts in §1 to §14 are not revised, because the
mirrors' coverage is unknown and r/WisprFlow bodies are mostly removed; the
material is listed, not tallied. The Limits paragraph should now read: Reddit
was reachable only through archive mirrors, with r/WisprFlow post bodies
mostly removed.

### Sources (2026-10-27)

Blocked or empty (recorded, not cited):

- https://www.reddit.com/search.json?q=wispr+flow+removed+words, https://www.reddit.com/search.json?q=superwhisper+hallucinated, https://www.reddit.com/r/WisprFlow/search.json?q=removes+words&restrict_sr=1, https://www.reddit.com/r/macapps/search.json?q=dictation+cleanup+removed+words&restrict_sr=1, https://www.reddit.com/r/WisprFlow/new.json?limit=50, https://api.reddit.com/r/WisprFlow/new, https://www.reddit.com/r/micro_saas/comments/1x4yd1u.json, https://www.reddit.com/r/superwhisper/comments/1wh8i8o.json, 2026-10-27, HTTP 403 with a browser User-Agent and with a plain one.
- https://old.reddit.com/search?q=wispr+flow+removes+words, https://old.reddit.com/r/WisprFlow/.json, https://old.reddit.com/r/micro_saas/comments/1x4yd1u.json, https://old.reddit.com/r/superwhisper/comments/1wh8i8o.json, 2026-10-27, HTTP 200, "Welcome to Reddit" interstitial, no post text.
- https://www.reddit.com/r/superwhisper/comments/1wh8i8o/issue_with_punctuations_and_formatting/, 2026-10-27, HTTP 200, title "Reddit", no comment markup.
- https://api.pullpush.io/reddit/search/submission/?q=wispr%20flow%20words&size=25 and the same endpoint for "wispr flow changed words", "superwhisper words", "dictation punctuation macos", 2026-10-27, mirror, HTTP 200; results were mostly app announcements and are not cited. The endpoint returned HTTP 429 for subreddit listings of WisprFlow and superwhisper and for "voiceink"; the comment endpoint returned no response.
- https://arctic-shift.photon-reddit.com/api/posts/search?query=wispr%20flow&limit=25, 2026-10-27, mirror, HTTP 400 ("'query' query parameter requires one of: author, subreddit").

Mirror listings used (arctic-shift.photon-reddit.com; all 2026-10-27, HTTP 200):

- https://arctic-shift.photon-reddit.com/api/posts/search?subreddit=WisprFlow&limit=100, plus the same with `before=2026-01-01` and with `after=2026-01-01&before=2026-09-01`, r/WisprFlow post listings; "[removed]" body counts above.
- https://arctic-shift.photon-reddit.com/api/posts/search?subreddit=superwhisper&limit=100, r/superwhisper post listing.
- https://arctic-shift.photon-reddit.com/api/comments/search?subreddit=WisprFlow&body=words&limit=100, https://arctic-shift.photon-reddit.com/api/comments/search?subreddit=superwhisper&body=words&limit=100, https://arctic-shift.photon-reddit.com/api/comments/search?subreddit=WisprFlow&limit=100, comment searches.
- https://arctic-shift.photon-reddit.com/api/posts/ids?ids=... (the ids of the threads below), post records with title, date and body.

Threads and comments cited (Reddit URLs as recorded by the mirror; not opened live):

- https://www.reddit.com/r/WisprFlow/comments/1u0egnx/longtime_user_honestly_the_quality_has_been_going/, 2026-10-27 via mirror, post of 2026-06-08 and comment of 2026-07-31: word swaps, missed phrases, "I want" to "i dont want", first words missed.
- https://www.reddit.com/r/superwhisper/comments/1uh5tey/how_to_stop_superwhisper_changing_what_i_say_into/, 2026-10-27 via mirror, post of 2026-06-27: sentences changed into something else.
- https://www.reddit.com/r/superwhisper/comments/1uh9jg3/inaccuracy_pro_member_refund/, 2026-10-27 via mirror, post of 2026-06-27 and comment of 2026-06-28: words changed, chunks left out, capitals imposed.
- https://www.reddit.com/r/superwhisper/comments/1try2ej/getting_frustrated/, 2026-10-27 via mirror, post of 2026-05-30 and comment of 2026-06-02: shortening, context removed, answering questions.
- https://www.reddit.com/r/WisprFlow/comments/1u9jjhj/june_18_2026_product_updates_reliability_privacy/, 2026-10-27 via mirror, vendor post of 2026-06-18 and comment of 2026-06-22: check and recheck every transcription.
- https://www.reddit.com/r/superwhisper/comments/1q99iif/superwhisper_hallucinations/, 2026-10-27 via mirror, post and comment of 2026-01-10: paragraphs appended.
- https://www.reddit.com/r/superwhisper/comments/1q4ryze/why_will_superwhisper_hallucinate_and_add_in_tons/, 2026-10-27 via mirror, post of 2026-01-05: text never said appended to voice memos.
- https://www.reddit.com/r/superwhisper/comments/1m9qdlf/is_superwhisper_leaking_the_transcription_text_of/, 2026-10-27 via mirror, post of 2025-07-26: paragraphs not said.
- https://www.reddit.com/r/WisprFlow/comments/1vj6tte/is_accuracy_back/, 2026-10-27 via mirror, post of 2026-08-08 (body removed) and comment of 2026-08-18: invented words.
- https://www.reddit.com/r/superwhisper/comments/1qz1hyn/why_is_superwhisper_answering_my_dictation_rather/, 2026-10-27 via mirror, post of 2026-02-08: model replies to the dictation.
- https://www.reddit.com/r/superwhisper/comments/1ufdvc6/new_superwhisper_mcp_and_cli/, 2026-10-27 via mirror, comment of 2026-06-25: answers instead of pasting the question.
- https://www.reddit.com/r/WisprFlow/comments/1rzglf0/feature_request_toggle_for_basic_vs_full/, 2026-10-27 via mirror, post of 2026-03-21: punctuation only when spoken.
- https://www.reddit.com/r/WisprFlow/comments/1olnnit/how_to_avoid_inserting_punctuation/, 2026-10-27 via mirror, post of 2025-11-01: no trailing period wanted.
- https://www.reddit.com/r/WisprFlow/comments/1pfq4sm/style_preference_for_comma_separated_lists_versus/, 2026-10-27 via mirror, post of 2025-12-06: list turned into bullets.
- https://www.reddit.com/r/WisprFlow/comments/1njkwy8/space_before_paste/, 2026-10-27 via mirror, comment of 2026-10-21: spoken "period" not applied.
- https://www.reddit.com/r/superwhisper/comments/1wh8i8o/issue_with_punctuations_and_formatting/, 2026-10-27 via mirror, post of 2026-09-15: spoken punctuation written out.
- https://www.reddit.com/r/WisprFlow/comments/1susv4c/april_24_2026_product_updates_insights_auto/, 2026-10-27 via mirror, vendor post of 2026-04-24 and comment of 2026-06-15: Light level changes words.
- https://www.reddit.com/r/WisprFlow/comments/1tx06rk/reliability_and_accuracy_update_what_happened/, 2026-10-27 via mirror, vendor post of 2026-06-04: auto-cleanup setting rollback.
- https://www.reddit.com/r/WisprFlow/comments/1x9mg7p/latency_issue_cutting_off_the_beginning_of/, 2026-10-27 via mirror, post of 2026-10-19, title only.
- https://www.reddit.com/r/WisprFlow/comments/1pnw05j/youre_fucking_kidding_me/, 2026-10-27 via mirror, post of 2025-12-16: support-request posts removed.
