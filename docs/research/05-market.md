# 05: What the products publish about cleanup

Access date for every source below: 2026-10-24. Every number in this file is
quoted from the cited page. Vendor comparisons ("fewer edits than", "lowest
WER among") are reported as the vendor's own claims and are not endorsed here;
the house rule against comparative claims applies to this document's own voice,
not to the faithful recording of what a page says.

One correction to the brief: the brief lists "Typeless (mono-1)". mono-1 is
Monologue's model, not Typeless's. Monologue's own blog post "Introducing
mono-1, built for dictation" (2026-09-23) establishes this; nothing on
typeless.com mentions mono-1 (searched: "Typeless mono-1 dictation model";
"Typeless help center dictation how it works filler words corrections").

## What was found

### Summary table

| Product | Cleanup claimed | Evidence shown | Where cleanup runs | Scriptable? | Bench adapter | Open weights |
| --- | --- | --- | --- | --- | --- | --- |
| Wispr Flow | fillers, grammar, self-corrections ("Backtrack"), formatting, tone; "Auto Cleanup" None/Light/Medium | none for cleanup; vendor case-study figures only | cloud | no public API in docs; MCP server for notes only | none: not scriptable | no |
| Superwhisper S1-mini | fillers, stutters, self-corrections, lists, mail layout, number/date/currency/email/URL normalization, tone | held-out token accuracy and structure rates (vendor) | local, 0.6B | yes: open weights, GGUF, exact prompt published | llama-cpp (GGUF) or OpenAI-compatible (`llama-server`); mlx-lm not published by vendor | yes: Apache 2.0 with a naming clause |
| Superwhisper S1-Language | cleaning, formatting, summarizing | none | cloud | no public API found | none | no |
| Aqua Voice | formatting adapts to app, grammar, "preserve every word" (Avalon marketing); Edit Mode | ASR key-term and WER figures (vendor); nothing for cleanup | cloud | audio-in API only; no text-in cleanup route | none for cleanup (identity-style audio adapter not in scope) | no |
| Willow | fillers, punctuation, grammar, formatting, per-app tone | "3x more accurate" marketing claim, no method | cloud | no API in docs | none: not scriptable | no |
| Monologue / mono-1 | punctuation, casing, fillers, false starts, self-corrections, spoken commands, lists | WildSpeech-Bench WER, latency, "estimated edits" by a blinded AI editor (vendor) | cloud (local mode is ASR only; formatting needs network) | Enterprise API, private beta, "format existing text" in one request | OpenAI-compatible is not stated; would need a custom adapter if access were granted | no |
| Typeless | fillers, repetitions, self-corrections, lists/steps, tone per app, dictionary, translation | none | not stated clearly | no API in docs | none: not scriptable | no |
| Spokenly | none built in; AI Instructions field is user-written; BYO key or local LLM | none | user's choice: Spokenly cloud, OpenAI, Anthropic, any OpenAI-compatible base URL, Ollama, LM Studio, Apple Intelligence | the LLM behind it, yes; Spokenly itself, no | the underlying model via OpenAI-compatible or Anthropic adapter, with Spokenly's instructions as the prompt | n/a |
| VoiceInk | "Enhancement" mode: fillers, repetitions, structure, email layout; VoiceInk Refine local model | none (Refine card: no evaluation numbers) | user's choice: 7 cloud providers, Ollama, Local CLI, OpenAI-compatible custom endpoint, or Refine (MLX) | Refine weights are downloadable | mlx-lm for Refine; OpenAI-compatible for the rest | Refine: license "other", "provided for use with VoiceInk" |
| Handy | none by default; optional experimental post-processing via OpenAI-compatible/Anthropic/Apple Intelligence with a user prompt | none | user's choice | the LLM behind it, yes | OpenAI-compatible / Anthropic with Handy's prompt | app MIT; no model |
| Apple SpeechAnalyzer / DictationTranscriber | punctuation (option), emoji, etiquette replacements; no disfluency or correction handling documented | none | on device | Swift API; audio in | none for text-in cleanup | no |
| macOS Dictation | auto punctuation (commas, periods, question marks), "new line"/"new paragraph" commands | none | on device for general text | no | none | no |
| Deepgram | `punctuate`, `smart_format`, `paragraphs`, `numerals`, `dictation`, `filler_words` (default removes "uh" and "um") | none on the option pages | cloud | audio-in only; Text Intelligence is analysis, not cleanup | none for cleanup | no |
| AssemblyAI | fillers removed by default; `disfluencies=true` keeps them; `punctuate` and `format_text` default true | none on the option pages | cloud | audio-in; LLM Gateway is text-in but is a generic chat API | OpenAI-compatible-style chat via LLM Gateway at most; not a cleanup product | no |
| Speechmatics | `remove_disfluencies` (default false), punctuation overrides, smart entity formatting on by default with `spoken_form` recoverable | none | cloud | audio-in | none for cleanup | no |
| Gladia | `punctuation_enhanced` (alpha, default false), `custom_vocabulary` (beta), `custom_spelling` (alpha), no disfluency option | none | cloud | audio-in | none for cleanup | no |

### 1. Wispr Flow

- Homepage claims: "Flow automatically removes filler words, adds punctuation, and formats your writing." Self-correction example: say "let's meet at 5... actually 6pm" and "Flow gives you 'Let's meet at 6pm.'" Demo labels: "Filler identified", "Correction identified", "Repetition identified". Styles: Formal, Casual, Very casual. No accuracy numbers for cleanup; speed claim "4x faster than your keyboard". No model named. No API or SDK mentioned. (https://wisprflow.ai/)
- Help center, Auto Cleanup (Beta): levels None ("Pastes the raw transcript, including filler words, false starts, and spoken errors"), Light (default; removes filler words and fixes grammar), Medium (may reword phrases for clarity and conciseness while keeping the original meaning). High is no longer selectable. "Undo AI edit" restores pre-cleanup text. Mac and Windows. (https://docs.wisprflow.ai/articles/4283510616-auto-cleanup-control-how-much-flow-edits-your-dictation-beta)
- Help center, Smart Formatting and Backtrack: Smart Formatting "is on by default"; cleans fillers, grammar, punctuation, capitalization; "doesn't fix misheard words". Backtrack "Removes filler words, false starts, and self-corrections while you keep talking", triggered by "actually", "scratch that", "never mind" or restating; example "Let's do coffee at 2 actually 3" → "Let's do coffee at 3." Limit stated: "I actually enjoyed the movie" is kept. (https://docs.wisprflow.ai/articles/5373093536-how-do-i-use-smart-formatting-and-backtrack)
- Help center, Android "removes or changes words": Smart Formatting drops fillers, false starts and repeated words "unless they seem to add meaning"; it "can also mistake meaningful words for filler, such as a leading 'so', deliberate repetition, or emphasis"; structure markers "first"/"finally" are removed and implied lists may become list formatting; spoken numbers become digits; contractions are expanded; similar-sounding words can become punctuation. Verbatim output: Auto Cleanup "None" on desktop; Smart Formatting toggle off on iOS; no toggle on Android. This is the only vendor page found that documents its own over-cleaning failure modes. (https://docs.wisprflow.ai/articles/6568835559-why-wispr-flow-sometimes-removes-or-changes-words-on-android-smart-formatting)
- Accuracy and known limitations: "Transcription runs in the cloud"; "Changed wording or layout in pasted text is formatting, not mishearing. Missing words warrant a retry." No percentages or WER. (https://docs.wisprflow.ai/articles/4048537120-what-to-expect-from-flow-accuracy-and-known-limitations)
- Security FAQ: Flow "processes dictated audio in the cloud"; "third-party AI providers" unnamed; reported transcripts "can be used to train and evaluate its models". No API mentioned. (https://docs.wisprflow.ai/articles/3467817258-security-and-compliance-faq)
- Privacy page: "Transcription always happens in the cloud." (https://wisprflow.ai/privacy)
- Docs index: no API documentation; only an MCP client guide for the remote MCP server. (https://docs.wisprflow.ai/llms.txt)
- Third-party API catalog listings for "api.wisprflow.ai" exist (apievangelist.com) but no official developer page was found. Searched: "Wispr Flow API developers SDK". Not confirmed; treated as not found.

### 2. Superwhisper, S1 family and S1-mini

- Blog "Introducing the S1 family of models" (2026-08-19): S1-Voice (cloud STT), S1-Language (cloud "instruction-following model for cleaning, formatting, or summarizing dictations"), S1-mini ("a small 484 MB 0.6B language model" that runs locally with "zero network requests"). S1-mini tasks listed: lists as ordered/unordered, mail-mode greeting and sign-off, "Removing filler words and stutters, and handling self-corrections mid-dictation", normalizing numbers, dates, currency, percentages, phone numbers, spoken emails and URLs. Stated limits: will not add content, correct facts, soften profanity, flag topics, or rewrite dialect. Tone: five settings from casual (lowercase, minimal punctuation) to formal. Evaluation (vendor): held-out 7,519 cases across 104 transcripts; token accuracy 94.8%; text-edit error rate 11.6%; email greeting 99.3%, sign-off 97.9%; list-vs-paragraph structure 97.6%; exact email addresses 92%; degenerate output under 1%; "Correctly produced no output when none was needed: 98.6%". The post also makes comparative claims for S1-Voice against other vendors (a blended score table including Wispr Flow); those are the vendor's claims. (https://superwhisper.com/blog/s1)
- Model card `superwhisper/s1-mini`: license Apache 2.0 "with a naming clause" requiring the name "S1-mini" by "Superwhisper" wherever used, inherited from Qwen3-0.6B; base `Qwen/Qwen3-0.6B`; 596M params (0.44B non-embedding); BF16 safetensors with `chat_template.jinja`; English only (v1); recommended input up to about 1,000 tokens; exact system prompt required plus a control line `[Styling: …] [Structure: …] [Context: …]` with Styling ∈ {casual, semi-casual, semi-formal, formal}, Structure ∈ {prose, lists}, Context ∈ {general, email}; `enable_thinking=False` and greedy decoding required; "Filler-only input correctly returns an empty string"; "not a chat model". 94.8% token accuracy on 7,519 held-out cases measured on the Q4_K_M GGUF. Training data not described. MLX not mentioned. (https://huggingface.co/superwhisper/s1-mini)
- `superwhisper/s1-mini-GGUF`: Q4_K_M 462 MB (recommended; the build used for the published accuracy), F16 1.4 GB; `llama-server -hf superwhisper/s1-mini-GGUF:Q4_K_M --jinja --chat-template-kwargs '{"enable_thinking":false}' --temp 0`; Ollama Modelfile with temperature 0; LM Studio with thinking off. (https://huggingface.co/superwhisper/s1-mini-GGUF)
- Qwen/Qwen3-0.6B license field: apache-2.0. (https://huggingface.co/Qwen/Qwen3-0.6B)
- Docs, language models: cloud S1-Language (default for most modes), Anthropic Sonnet 5 / 4.6 / 4.5 / Haiku 4.5, OpenAI GPT-5.x family, Google Gemini 3.x Flash, Groq Llama 3.1 8B; local S1-mini (462 MB) "Cleans up English punctuation, numbers, dates, and filler words", works only in Message and Mail modes; "Bring your own key" for custom providers (Pro). (https://superwhisper.com/docs/models/language.md)
- Docs, built-in modes: Voice to Text = transcription only, "Filler words, grammar, and formatting are not changed"; Message = remove fillers and speech artifacts, fix grammar and punctuation, format for readability, keep tone; Mail = salutation, paragraphing, sign-off; Note = clarity, key points, lists; Super = app-aware vocabulary and spoken URL/email conversion. (https://superwhisper.com/docs/modes/built-in.md)
- Docs, modes: Tone slider Casual to Formal on Message/Mail/Note; Custom modes take user instructions. (https://superwhisper.com/docs/modes/modes.md; https://superwhisper.com/docs)
- Benchmarks page (updated 2026-09-03): voice models only; Wispr Flow was tested "with its cleanup pass switched off so the transcript can be scored against a word-for-word reference"; metrics WER, speed, recall, F-score, response time, blended score; 8 datasets (AMI, Common Voice AU, Common Voice spontaneous, Earnings 22 with and without vocabulary, LibriSpeech Other, Loquacious, Phonetic vocabulary). No cleanup or language model has measured numbers; language-model "Speed and Accuracy columns" are hand-assigned 1 to 10 ratings per the methodology page. (https://superwhisper.com/benchmarks; https://superwhisper.com/docs/models/benchmarks.md)

### 3. Aqua Voice

- Homepage: "Avalon" and "Avalon 1.5" named; marketing line "preserve every word while refining your text in real time" and "correct grammar"; "From lowercase Slack messages to structured docs, Aqua adapts"; custom prompting "Set your tone and rules"; vendor benchmark "AISpeak-10" key-term accuracy 97.4% (Avalon) vs 65.1% (Whisper Large v3), vendor's claim; headline "5x faster than typing and twice as accurate" without method. No statement of local vs cloud; Privacy Mode says "nothing is stored on our servers at all". Nav links to MCP, CLI, API. (https://aquavoice.com/)
- Avalon API: audio only; `POST /v1/audio/transcriptions` OpenAI-compatible, model `avalon-v1.5`; "Text-in, text-out cleanup: Not offered." $0.39 per audio hour. Vendor claim: 6.24% average WER on the Open ASR leaderboard "at its October 2025 debut". (https://aquavoice.com/api)
- Avalon benchmarks page: AISpeak-10/50/500 key-term accuracy tables and Open ASR per-dataset claims (vendor); Avalon "stays literal"; no mention of filler removal, formatting rules, or disfluency cleanup. Links a model card PDF, not opened. (https://aquavoice.com/avalon-api)
- API reference: `POST /dictations` is multipart with a required `audio` file (16 kHz mono PCM16 WAV or Ogg Opus); `operation=edit` applies the spoken instruction to `selected_text` (up to 6,000 characters) with `edit_unclear` / `edit_deleted` flags; context fields `text_before`, `text_after`, `app`; "Every dictation and transcription route requires an audio file"; `instructions` field exists for platform keys but still with audio. Transcription `temperature` accepts only 0. $0.49 per hour of dictation. (https://aquavoice.com/docs/api)
- CLI: `aqua transcribe` (audio in), plus dictionary / replacements / instructions management. No text-in cleanup command. (https://aquavoice.com/docs/cli)

### 4. Willow (willowvoice.com, the dictation app; not the Willow smart-speaker project)

- Features page: "Removes filler words, adds punctuation"; FAQ "cleans up your speech, adds punctuation, fixes grammar, formats your thoughts"; "Your tone per app"; "Offline mode" claimed ("powered entirely by your device") while the privacy article says transcription uses cloud models; "3x more accurate than built-in dictation" and "up to 3x more accurate than other dictation tools" (vendor claims, no method); "Under 200ms latency" (no conditions). No model names. No API. Self-correction handling not addressed. (https://willowvoice.com/features/dictation)
- Help article "Dictating with Willow Voice": text is "formatted and inserted"; in email apps it sets up greeting, body and closing; 50 languages. Fillers, corrections, models, API not covered. (https://help.willowvoice.com/en/articles/10876920-dictating-with-willow-voice)
- Privacy article: transcription runs on "cloud-based AI models"; Private Mode default stores no transcripts or audio on servers; "Help Improve" mode is the only training source. No providers named. (https://help.willowvoice.com/en/articles/12854269-how-willow-protects-your-data-and-privacy; collection index https://help.willowvoice.com/en/collections/16694558-privacy-secruity; help home https://help.willowvoice.com/en/)
- Y Combinator company page and App Store listing appeared in search but were not needed and were not opened.

### 5. Monologue and mono-1

- Blog "Introducing mono-1, built for dictation" (2026-09-23): in-house model covering "recognition, corrections, formatting, and writing preferences"; illustrative examples: "six, actually six thirty" → "6:30", "new paragraph" → line break, "um" removed, spoken list → bulleted list. Evaluation (vendor): WildSpeech-Bench, 1,100 English clips (1,000 synthetic voice-cloned, 100 real); WER mono-1 7.22%, GPT-4o Transcribe 6.68%, Cartesia Ink 7.39%; median raw-transcription latency 109 ms (mono-1), 570 ms (GPT-4o Transcribe), 109 ms (Cartesia Ink); "estimated edits" by "a blinded AI editor" fell from 13.64 to 6.21 per 100 words versus Monologue's previous pipeline; the post itself notes timings came from separate runs and environments and are indicative. Availability: enterprise API "limited to a small number of approved users"; developers request access via a form. No open weights, no license stated. (https://www.monologue.to/blog/introducing-mono-1)
- Homepage: "Self-corrections, handled."; "Monologue keeps the final message, not the correction."; local transcription models on Mac exist but "Smart formatting and syncing still require a connection"; AI providers process dictation with zero data retention. MCP/API/CLI give agents access to Notes, not dictation. (https://www.monologue.to/)
- Docs, first dictation: Monologue "cleans up punctuation, casing, filler words, and false starts according to your selected mode." (https://www.monologue.to/docs/getting-started/first-dictation)
- Docs, modes and instructions: standard dictation runs through smart post-processing; "Blazing Fast" skips it. (https://www.monologue.to/docs/personalize/modes-and-instructions)
- Docs, languages and models: Remote is the recommended default; Local (Apple silicon) runs only speech-to-text and "Smart cleanup and context-aware formatting still use Monologue's online service"; no model names. (https://www.monologue.to/docs/dictation/languages-and-models)
- Docs, Enterprise API: private beta, "not self-serve"; batch dictation "can 'format existing text' in one HTTPS request"; endpoints `POST /dictation/dictate`, `POST /authentication/createclienttoken`, `POST /feedback/submitenterprisefeedback`, `GET /languages/listlanguages`; mono-1 and pricing not mentioned. This is the only commercial text-in formatting endpoint found in this survey, and it is gated. (https://www.monologue.to/docs/enterprise-api)
- Docs, Public API: Notes read-only (`notes:read`), "The API cannot create, edit, or delete notes"; no dictation. (https://www.monologue.to/docs/public-api; index https://www.monologue.to/docs)
- Launch post on Every (2025-09-16): "polished and structured for the app you're in"; no fillers/corrections detail; no accuracy numbers. (https://every.to/on-every/introducing-monologue-effortless-voice-dictation)
- Changelog: no entry names mono-1, corrections or filler words. (https://www.monologue.to/changelog)
- Aggregator page that first surfaced mono-1, superseded by the primary post above. (https://digg.com/ai/eiitynxp)

### 6. Typeless

- Homepage: "Automatically removes filler words" ("um", "uh", "you know"); detects and removes repeated words; "Typeless recognizes when you correct yourself mid-sentence" and keeps the final message; "Automatically organizes spoken lists, steps, and key points into clean, structured text"; tone adapts per app; translation; 100+ languages. No accuracy numbers; "4x faster than typing", 220 wpm vs 45 wpm. "On device" and "Cloud Sync" labels without saying which processing is where; "Your audio is processed securely in real time and never stored in the cloud." No models or API named. (https://www.typeless.com/)
- Windows beta release note (2025-10-22): same filler, self-correction, list and dictionary claims; models not named. (https://www.typeless.com/help/release-notes/windows/introducing-typeless-windows-app-beta)
- mono-1 on Typeless: not found (see correction at top).

### 7. Spokenly

- Homepage: "AI text processing with modes and AI Instructions (GPT-4, Claude, Gemini)"; "Free local transcription with Whisper or Parakeet"; cloud models by default; BYO keys. No filler or correction claims of its own; no accuracy figures; open-source status not stated. (https://spokenly.app/)
- Docs, modes: AI Instructions are optional and user-written; provider can be Spokenly built-in, OpenAI, Anthropic, or "any OpenAI-compatible provider via your own base URL and key (BYOK)"; the page shows example instructions for translation, cleanup, spoken punctuation, and search, none built in. (https://spokenly.app/docs/modes)
- Docs, models: dictation BYO providers include Groq, OpenAI, ElevenLabs, OpenRouter, Google Gemini, Deepgram, Mistral AI, AssemblyAI, Cartesia, Cohere, Fireworks AI, Sarvam AI, Straico, xAI, "Any server with an OpenAI-compatible API"; AI Processing local options Ollama, LM Studio, Apple Intelligence; cloud BYO OpenAI, Gemini, Groq, OpenRouter, Anthropic, Cerebras, Inception, Mistral, Straico, xAI, Amazon Bedrock, any OpenAI-compatible endpoint. (https://spokenly.app/docs/models)
- Docs, Local Only Mode: blocks internet except model downloads; localhost allowed; "doesn't describe any built-in local cleanup". (https://spokenly.app/docs/local-only-mode)
- llms.txt: no license, no GitHub link. Spokenly is not open source as far as its site states. (https://spokenly.app/llms.txt)

### 8. VoiceInk (open source)

- GitHub README: "licensed under the GNU General Public License v3.0"; engines whisper.cpp, Parakeet via FluidAudio, TranscribeCpp, SenseVoice Small; features "Smart Modes", "Context Aware", "AI Assistant", "Personal Dictionary"; "100% offline processing" claim alongside optional cloud enhancement. macOS 15.0+. (https://github.com/Beingpax/VoiceInk)
- LICENSE file: GNU GPL v3, 29 June 2007. (https://raw.githubusercontent.com/Beingpax/VoiceInk/main/LICENSE)
- Website: enhancement examples (strip "um" and repeated phrases, tighten rambling, structure notes, email layout, rewrite selected text); "Cloud Enhancement is entirely optional"; prices Solo $25, Personal $39, Extended $49 one-time; build from source free. (https://tryvoiceink.com/)
- Docs, modes: starter modes Dictation (no AI), Enhancement ("Cleans up dictated text with AI"), Email, Rewrite, Assistant; "Refine supports fixed cleanup rather than custom prompt or Assistant workflows". (https://tryvoiceink.com/docs/modes)
- Docs, cloud providers: Groq, Cerebras, Gemini, OpenAI, OpenRouter, Anthropic, Mistral. (https://tryvoiceink.com/docs/cloud-providers)
- Docs, local models: "VoiceInk Refine: Built-in dictation cleanup on a supported Mac", Ollama (`http://localhost:11434`), Local CLI. (https://tryvoiceink.com/docs/local-models)
- Docs, custom models: OpenAI-compatible chat completion endpoint with base URL, key, model name. (https://tryvoiceink.com/docs/custom-models)
- Docs, model settings: "Skip short transcriptions" default on, minimum words default 3, timeout default 7 s, fallback keeps the original transcription with a warning. (https://tryvoiceink.com/docs/model-settings)
- Model card `beingpax/voiceink-refine-v1`: license "other", "provided for use with VoiceInk" with a LICENSE.md; base Qwen3.5-2B; 2B params; MLX 4-bit 1.06 GB; handles punctuation, capitalization, fillers, repetitions, spoken formatting cues, lists, email paragraphs; example turns "comma", "period", "new paragraph" into punctuation and breaks; served via `mlx_lm.server`; no evaluation numbers; no system prompt given. (https://huggingface.co/beingpax/voiceink-refine-v1)
- A third-party host (featherless.ai) describes a different base and parameter count for Refine than the Hugging Face card; the card is treated as authoritative and the third-party page was not opened.

### 9. Handy (open source)

- GitHub README: "MIT License"; "the Handy name, logo, icon, and brand assets are not open-source"; offline; Whisper and Parakeet V3, Silero VAD; a `--toggle-post-process` flag mentioned without explanation. Windows, macOS, Linux. (https://github.com/cjpais/Handy)
- LICENSE: MIT, "Copyright (c) 2025 CJ Pais". (https://raw.githubusercontent.com/cjpais/Handy/main/LICENSE)
- Site: "One tool, one job."; "Your voice stays on your computer." (https://handy.computer/)
- Docs, post-processing: gated behind Experimental Features; providers OpenAI, Anthropic, OpenRouter, Groq, Cerebras, Z.AI, Apple Intelligence (macOS 26+), and "Any 'OpenAI-compatible API endpoint'" (LM Studio example `http://localhost:1234/v1`); prompt uses `${output}`; "Only a dedicated post-processing hotkey triggers it. The regular shortcut always returns plain output."; "Models under 3B parameters often ignore instructions." (https://handy.computer/docs/post-processing)
- Docs, models: table of local STT models with formatting notes: Cohere Transcribe "outputs punctuated, capitalized text"; Parakeet "writes numbers as words"; Whisper "writes numbers as digits"; Canary 1B v2 outputs punctuation, capitalization and inverse text normalization. This matters for the bench's input form: different local recognizers emit different raw forms. (https://handy.computer/docs/models; index https://handy.computer/docs)

### 10. Apple SpeechAnalyzer, SpeechTranscriber, DictationTranscriber, macOS Dictation

- WWDC25 session 277: SpeechAnalyzer "manages an analysis session"; results are `AttributedString` with `audioTimeRange`; volatile vs finalized results; "transcription is entirely on device but the models need to be fetched"; introduced "in iOS 26"; DictationTranscriber offered as a fallback that "supports the same languages, speech-to-text model, and devices as iOS 10's on-device SFSpeechRecognizer". Punctuation, capitalization and disfluency handling are not discussed; no WER or latency numbers. (https://developer.apple.com/videos/play/wwdc2025/277/)
- SpeechAnalyzer reference: availability 26.0 on iOS, iPadOS, Mac Catalyst, macOS, tvOS, visionOS; one input sequence at a time; `AssetInventory` manages on-device assets. (https://developer.apple.com/tutorials/data/documentation/speech/speechanalyzer.json)
- SpeechTranscriber reference: "appropriate for normal conversation and general purposes"; option types TranscriptionOption, ReportingOption, ResultAttributeOption; 26.0. (https://developer.apple.com/tutorials/data/documentation/speech/speechtranscriber.json)
- SpeechTranscriber.TranscriptionOption: the only case is `etiquetteReplacements`, "Replaces certain words and phrases with a redacted form." No punctuation toggle and no disfluency option exist on this type. (https://developer.apple.com/tutorials/data/documentation/speech/speechtranscriber/transcriptionoption.json)
- SpeechTranscriber.Preset: `transcription`, `transcriptionWithAlternatives`, `timeIndexedTranscriptionWithAlternatives`, `progressiveTranscription`, `timeIndexedProgressiveTranscription`; the table lists reporting and attribute options only. (https://developer.apple.com/tutorials/data/documentation/speech/speechtranscriber/preset.json)
- SpeechTranscriber.ReportingOption: `alternativeTranscriptions`, `fastResults`, `volatileResults`. (https://developer.apple.com/tutorials/data/documentation/speech/speechtranscriber/reportingoption.json)
- DictationTranscriber reference: "similar to system dictation features and compatible with older devices"; uses "the same speech-to-text machine learning models as system dictation"; content hints `farField`, `customizedLanguage`; vocabulary biasing via `contextualStrings`; 26.0. (https://developer.apple.com/tutorials/data/documentation/speech/dictationtranscriber.json)
- DictationTranscriber.TranscriptionOption: `emoji` ("Transcribes named emoji as emoji"), `etiquetteReplacements`, `punctuation` ("Automatically punctuates the transcription"). (https://developer.apple.com/tutorials/data/documentation/speech/dictationtranscriber/transcriptionoption.json)
- DictationTranscriber.Preset: `phrase` (no punctuation), `shortDictation`, `progressiveShortDictation`, `longDictation`, `progressiveLongDictation`, `timeIndexedLongDictation` all enable `punctuation`. (https://developer.apple.com/tutorials/data/documentation/speech/dictationtranscriber/preset.json)
- Sample article stub "Bringing advanced speech-to-text capabilities to your app": body not served; metadata only. (https://developer.apple.com/tutorials/data/documentation/speech/bringing-advanced-speech-to-text-capabilities-to-your-app.json)
- macOS User Guide, Use dictation: general text dictation "may be 'processed on your device and not sent to Siri servers'"; auto-punctuation adds "commas, periods, and question marks" in supported languages and can be turned off; "new line" and "new paragraph" commands; ambiguous words underlined in blue; no mention of filler words or self-corrections. (https://support.apple.com/guide/mac-help/use-dictation-mh40584/mac)
- Nothing in Apple's documentation describes filler removal, repetition collapse or self-correction resolution. Apple's public APIs stop at punctuation, emoji and etiquette replacement.

### 11. Speech-to-text vendors' formatting options

Deepgram (all pages at developers.deepgram.com/docs/):

- `punctuate`: adds punctuation and capitalization; default `false`. (https://developers.deepgram.com/docs/punctuation)
- `smart_format`: default `false`; enables punctuation, paragraphs (whitespace-delimited languages), and in English dates, times, currency, phone numbers, emails, URLs; "Measurements and Dictation... must be enabled separately". (https://developers.deepgram.com/docs/smart-format)
- `filler_words`: default `false`; "When `false` or unset: Only 'uh' and 'um' are removed from the transcript"; when `true` transcribes uh, um, mhmm, mm-mm, uh-uh, uh-huh, nuh-uh; Nova models, English. So Deepgram removes two fillers by default and never removes others. (https://developers.deepgram.com/docs/filler-words)
- `paragraphs`: default `false`; turns on punctuation. (https://developers.deepgram.com/docs/paragraphs)
- `numerals`: default `false`; "nine hundred" → "900"; converted numbers carry no thousands separators. (https://developers.deepgram.com/docs/numerals)
- `dictation`: converts spoken "period", "comma", "colon", "question mark", "exclamation mark", "new line", "new paragraph" into marks and breaks; requires `punctuate=true`; English. This is the one vendor option that implements the spoken-command portion of cleanup. (https://developers.deepgram.com/docs/dictation)
- Text Intelligence: text-in, English only, 150K-token limit; summarization, topics, intents, sentiment; "doesn't describe any feature that cleans up or rewrites transcripts". (https://developers.deepgram.com/docs/text-intelligence)

AssemblyAI:

- Filler Words page: "By default, filler words are removed from the transcript before it's returned." `disfluencies=true` keeps them. Universal-3.5 Pro: English, Spanish, German, French, Portuguese, Italian; Universal-2: English only. Default behavior is the opposite of Deepgram's: remove by default. (https://www.assemblyai.com/docs/pre-recorded-audio/filler-words)
- API reference, submit transcript: `disfluencies` "Transcribe Filler Words, like 'umm'", default `false`; `punctuate` default `true`; `format_text` default `true`; `filter_profanity` default `false`; `speech_model` deprecated in favour of `speech_models`, default `["universal-3-5-pro", "universal-2"]`. (https://www.assemblyai.com/docs/api-reference/transcripts/submit)
- LeMUR: the documented LeMUR URLs now serve "LLM Gateway" content (a generic chat-completions API over "25+ models" with a `transcript_id` or `{{ transcript }}` substitution); no built-in cleanup; no `input_text` documented on the pages opened. Named LeMUR documentation: not found on the current site (opened https://www.assemblyai.com/docs/lemur, https://assemblyai.com/docs/getting-started/apply-llms-to-audio-files, https://www.assemblyai.com/docs/sdk-references/python/le-mur, https://www.assemblyai.com/docs/api-reference/lemur/task; all redirect to or render LLM Gateway material). The guide page https://www.assemblyai.com/docs/guides/disfluencies rendered the Filler Words page instead.

Speechmatics:

- Punctuation settings: `punctuation_overrides.permitted_marks` and `sensitivity` (default 0.5); `remove_disfluencies` default `false`; smart entity formatting "is applied by default"; `enable_entities` default `false`; `output_locale`; `replacements`. (https://docs.speechmatics.com/features/punctuation-settings)
- Word tagging: disfluency tags applied automatically (um, uh, hmm, erm, mhm, and a listed set) in 17 languages; `transcript_filtering_config.remove_disfluencies: true` removes them and "capitalization and spacing are adjusted"; default `false`. (https://docs.speechmatics.com/features/word-tagging)
- Entities: smart formatting converts spoken numbers, dates, currencies "on by default" ("nineteen ninety nine" → "1999", "twenty dollars" → "$20"); `enable_entities: true` exposes `written_form` and `spoken_form` in JSON; no documented way to switch formatting off entirely. (https://docs.speechmatics.com/features/entities)
- Output formatting page at docs.speechmatics.com/features/output-formatting: 404.

Gladia:

- Features index: enhanced punctuation, custom vocabulary (phoneme-based), custom spelling, name consistency; no cleanup or disfluency option. (https://docs.gladia.io/chapters/pre-recorded-stt/features)
- API reference, pre-recorded init: `punctuation_enhanced` "[Alpha]" default `false`; `custom_spelling` "[Alpha]" default `false`; `custom_vocabulary` "[Beta]" default `false`; `sentences`, `subtitles` default `false`; `name_consistency` not listed; no disfluency option. (https://docs.gladia.io/api-reference/v2/pre-recorded/init)
- Custom vocabulary: `vocabulary` entries with `value`, `pronunciations`, `intensity` (suggested 0.4 to 0.6), `default_intensity`. (https://docs.gladia.io/chapters/pre-recorded-stt/features/custom-vocabulary)
- Custom spelling: literal, case-insensitive post-processing replacement from listed variants to a key; "Does not use sound-based matching". (https://docs.gladia.io/chapters/audio-intelligence/custom-spelling.md)

### 12. Generic open-weight models named by the open-source tools

- Handy's post-processing page recommends GPT-4o-mini (OpenAI), Claude Haiku (Anthropic) and GLM-4.5-Air (Z.AI), none open-weight in that form, and points local users at LM Studio via an OpenAI-compatible endpoint without naming a local model. (https://handy.computer/docs/post-processing)
- VoiceInk names Ollama as a server, not a model. (https://tryvoiceink.com/docs/local-models)
- Spokenly names Ollama, LM Studio and Apple Intelligence as runtimes, not models. (https://spokenly.app/docs/models)
- Superwhisper's only open-weight cleanup model is S1-mini (Qwen3-0.6B base). Its hosted Groq option is Llama 3.1 8B. (https://superwhisper.com/docs/models/language.md)
- No open-source tool page names a default local cleanup model other than the vendors' own fine-tunes (S1-mini, VoiceInk Refine, SimpleWords v3).

### 13. SimpleWords v3 (ours), for completeness of the open-weights list

- Model card `ReFyneLabs/simplewords-dictation-cleanup-v3`: license apache-2.0; fine-tuned from Qwen/Qwen3.5-2B; 2B; prompt file `system_v2.txt` in one user turn with greedy decoding and `enable_thinking=False`; vendor-reported gates (cross-sentence 122/122, intra-sentence 43/44 with the `reg_003` miss stated, negatives 30/30, ordinary 25/25, Disfl-QA 231/300); access gated behind accepting conditions on Hugging Face. (https://huggingface.co/ReFyneLabs/simplewords-dictation-cleanup-v3)

### Cross-cutting observations

1. **Nobody publishes a cleanup measurement that separates the cleanup layer from recognition.** Superwhisper publishes S1-mini token accuracy on its own held-out set; Monologue publishes "estimated edits" judged by an AI editor; everyone else publishes nothing for cleanup. Superwhisper's own voice benchmark deliberately switches Wispr Flow's cleanup off to make WER scorable, which confirms the layer is treated as unmeasurable noise by the industry's own benchmarks.
2. **The only pages that document over-cleaning failure modes are Wispr Flow's help articles** (meaningful "so" treated as filler, emphasis repetition removed, structure markers deleted, similar-sounding words turned into punctuation) and S1-mini's model card (hallucination when the control line is wrong). These are exactly the "never lose words" and "when unsure, leave it" failures the bench must score.
3. **Input form differs by recognizer.** Handy's model table shows Parakeet writing numbers as words, Whisper as digits, Cohere Transcribe punctuated and cased, Canary with inverse text normalization. Apple's SpeechTranscriber has no punctuation toggle at all, while DictationTranscriber's `phrase` preset is unpunctuated and the others punctuated. A single "lowercase unpunctuated" input form is one of several real-world raw forms.
4. **Fillers are not neutral across vendors.** AssemblyAI removes fillers by default; Deepgram removes exactly "uh" and "um" by default and nothing else; Speechmatics keeps them unless `remove_disfluencies` is set; Gladia has no option. A cleanup bench's "fillers" category therefore sits partly upstream of cleanup for some pipelines.
5. **Spoken-command handling exists as an ASR option only at Deepgram (`dictation`)**; the others leave "new paragraph" to the cleanup layer. VoiceInk Refine's card and mono-1's post both show spoken commands being resolved by the cleanup model.
6. **Open-weight cleanup models found: three.** S1-mini (Apache 2.0 with a naming clause, GGUF published, exact prompt and control line published, greedy decoding mandated), VoiceInk Refine v1 (license "other", "provided for use with VoiceInk", MLX published, no prompt or numbers), SimpleWords v3 (Apache 2.0, gated download, prompt file published). No other vendor publishes weights.
7. **Text-in cleanup APIs are nearly absent commercially.** Monologue's Enterprise API can "format existing text" but is a gated private beta. Aqua's API is audio-only. Deepgram Text Intelligence and AssemblyAI LLM Gateway take text but are analysis or generic chat, not cleanup products. Wispr Flow, Willow, Typeless and Superwhisper's cloud models expose no public API in their docs.

## What is recommended

### Baselines for v1 and their adapters

- **Identity** (adapter: identity). Required as the floor; every negative-category item should score perfectly here, which also validates the scorer.
- **SimpleWords v3** through the Pomvox LocalServer (`POST /v1/clean`, adapter: Pomvox LocalServer) and through mlx-lm (adapter: mlx-lm) with `system_v2.txt`, one user turn, greedy, thinking off, as the model card specifies. Both rows, with the byte-for-byte agreement check the prompt requires.
- **Superwhisper S1-mini** via `llama-server` on the Q4_K_M GGUF (adapter: OpenAI-compatible against a loopback `llama-server`, or llama-cpp directly). Use the card's exact system prompt and a fixed control line, recommended `[Styling: semi-formal] [Structure: prose] [Context: general]` for prose categories, with `--temp 0` and `enable_thinking:false`. Run the Q4_K_M build because that is the build the vendor's published number was measured on. Record the control line in the run manifest, since the card says changing it alters output. Score the empty-string-on-filler-only behaviour the card documents against the bench's fallback/unchanged rules rather than as a word-loss violation; the spec must decide how an empty output is treated.
- **VoiceInk Refine v1** via mlx-lm (adapter: mlx-lm) only if the LICENSE.md permits evaluation use; the card's "provided for use with VoiceInk" wording needs reading before any row is published. No system prompt is published, so the row would use the card's bare chat-template usage, and that must be stated.
- **One generic prompt on a local open-weight model and one on a cloud model** (adapters: OpenAI-compatible for the local server, Anthropic for the cloud model). Use a published prompt from an open-source tool where one exists; Handy and VoiceInk publish none, Spokenly publishes example instructions but no default. The bench should therefore ship its own fixed generic prompt and version it.
- **Not runnable in v1:** Wispr Flow, Willow, Typeless, Aqua (cleanup), Superwhisper S1-Language, Monologue mono-1 (gated), Apple Dictation and SpeechAnalyzer (audio-in, Swift only). List them in the market report and in the submission guide as invited, with the adapter each would need: an OpenAI-compatible text endpoint, or a vendor-run submission under the governance rules in 04.

### Adapters needed and not needed

- Needed: identity, OpenAI-compatible (covers llama-server, mlx_lm.server, Ollama, LM Studio, Spokenly/VoiceInk/Handy-style custom endpoints), Anthropic, mlx-lm (SimpleWords and Refine), Pomvox LocalServer. llama-cpp as a direct binding is optional because `llama-server` already exposes OpenAI-compatible chat; keep it only if the determinism check needs process-level control of sampling.
- Not needed in v1: audio-in adapters for Deepgram, AssemblyAI, Speechmatics, Gladia, Aqua. Their cleanup is bound to audio and their text-in products are not cleanup. A future "ASR option" track could feed TTS audio of each item and treat `smart_format` / `format_text` / `remove_disfluencies` as a cleanup configuration, but that measures ASR plus cleanup together, which this bench is defined not to do.

### Input form

- The appendix's "raw lowercase unpunctuated transcript" matches Parakeet-style and Deepgram `punctuate=false` output and is a real form, but Whisper, Cohere Transcribe, Canary and Apple's SpeechTranscriber emit cased, punctuated text, and Whisper emits digits. Recommend that each item record its `input_form` (for example `lowercase-unpunctuated`, `cased-punctuated`, `digits`) and that v1 restrict scoring to one declared form while keeping the field so v2 can add others without an item-schema change. This is the one place the market evidence pushes against the appendix.
- Spoken commands ("new paragraph", "comma") are resolved by the cleanup layer in S1-mini, Refine and mono-1 and by the ASR layer only at Deepgram. Keep `lists-layout` as a cleanup category and state in the task definition that spoken layout commands are in scope, consistent with the engine's `spokenLayout` transform.

### Licenses and attribution for open-weight rows

- S1-mini: Apache 2.0 plus the vendor's naming clause; every table row and manifest must print "S1-mini" by "Superwhisper" with that capitalisation, and the NOTICE file terms should be checked in the GGUF repo before the first published run.
- SimpleWords v3: Apache 2.0; the download is gated, so the reproduction guide must say the stranger needs a Hugging Face account and must accept the repo's conditions. If "reproducible by a stranger with one command" is to hold literally, the gate should be removed or a mirror published; that is the owner's decision.
- VoiceInk Refine v1: license "other"; do not publish a row until LICENSE.md has been read and permits it.
- Generic models: use each model's own license field; Qwen3 bases are Apache 2.0 per the Qwen3-0.6B card.

### What this file could not establish

- Whether Wispr Flow has any official developer API (third-party catalogs list one; the vendor's docs do not).
- Which LLMs Willow, Typeless, Wispr Flow and Aqua use for cleanup: no page names them.
- Whether mono-1 is one model or an ASR model plus a formatting stage: the post describes capabilities, not architecture.
- Apple SpeechTranscriber's punctuation behaviour: its TranscriptionOption has no punctuation case, which implies punctuation is always on, but no page states that outright.
- VoiceInk Refine's licence terms: the card says "other" and points to a file that was not opened.
- Current LeMUR documentation: every LeMUR URL opened now renders LLM Gateway content.

## Sources

- https://superwhisper.com/blog/s1 — 2026-10-24 — S1 family post: S1-mini size, tasks, limits, tone slider, vendor eval numbers.
- https://huggingface.co/superwhisper/s1-mini — 2026-10-24 — model card: license with naming clause, base, params, prompt and control line, limitations, 94.8% on 7,519 cases.
- https://huggingface.co/superwhisper/s1-mini-GGUF — 2026-10-24 — GGUF sizes, llama-server/Ollama/LM Studio instructions, greedy decoding requirement.
- https://huggingface.co/Qwen/Qwen3-0.6B — 2026-10-24 — base model license apache-2.0.
- https://superwhisper.com/docs — 2026-10-24 — modes overview, S1-mini local formatting in Message/Mail modes.
- https://superwhisper.com/docs/modes/modes.md — 2026-10-24 — mode types, tone slider, custom instructions.
- https://superwhisper.com/docs/modes/built-in.md — 2026-10-24 — what each built-in mode does to the transcript.
- https://superwhisper.com/docs/models/language.md — 2026-10-24 — cloud and local language model list, BYO key.
- https://superwhisper.com/docs/models/benchmarks.md — 2026-10-24 — benchmark methodology; language models not benchmarked.
- https://superwhisper.com/benchmarks — 2026-10-24 — voice-only leaderboard; Wispr Flow cleanup switched off for scoring.
- https://superwhisper.com/docs/llms.txt — 2026-10-24 — docs index used to locate the pages above.
- https://wisprflow.ai/ — 2026-10-24 — marketing claims, correction example, no API, no model names.
- https://wisprflow.ai/privacy — 2026-10-24 — "Transcription always happens in the cloud"; retention; training opt-in.
- https://docs.wisprflow.ai/llms.txt — 2026-10-24 — help-center index; no API docs.
- https://docs.wisprflow.ai/articles/4283510616-auto-cleanup-control-how-much-flow-edits-your-dictation-beta — 2026-10-24 — Auto Cleanup levels and default.
- https://docs.wisprflow.ai/articles/5373093536-how-do-i-use-smart-formatting-and-backtrack — 2026-10-24 — Smart Formatting default on; Backtrack self-correction behaviour.
- https://docs.wisprflow.ai/articles/6568835559-why-wispr-flow-sometimes-removes-or-changes-words-on-android-smart-formatting — 2026-10-24 — vendor-documented over-cleaning failure modes.
- https://docs.wisprflow.ai/articles/4048537120-what-to-expect-from-flow-accuracy-and-known-limitations — 2026-10-24 — no accuracy numbers; cloud processing; limitations.
- https://docs.wisprflow.ai/articles/3467817258-security-and-compliance-faq — 2026-10-24 — cloud processing, unnamed providers, retention, no API.
- https://en.wikipedia.org/wiki/Wispr_Flow — 2026-10-24 — company history, platforms; no model names.
- https://aquavoice.com/ — 2026-10-24 — Avalon claims, AISpeak-10 figures (vendor), no local/cloud statement.
- https://aquavoice.com/api — 2026-10-24 — Avalon API audio-only, OpenAI-compatible, no text-in cleanup, pricing.
- https://aquavoice.com/avalon-api — 2026-10-24 — vendor benchmark tables; "stays literal"; no cleanup description.
- https://aquavoice.com/docs/api — 2026-10-24 — `/dictations` requires audio; `operation=edit`; `instructions`.
- https://aquavoice.com/docs/cli — 2026-10-24 — CLI transcribes audio and manages dictionary/instructions.
- https://willowvoice.com/features/dictation — 2026-10-24 — filler/punctuation/grammar claims, "3x" claims, offline mode, no API.
- https://help.willowvoice.com/en/ — 2026-10-24 — help collections index.
- https://help.willowvoice.com/en/articles/10876920-dictating-with-willow-voice — 2026-10-24 — formatting and email behaviour; 50 languages.
- https://help.willowvoice.com/en/collections/16694558-privacy-secruity — 2026-10-24 — privacy article list.
- https://help.willowvoice.com/en/articles/12854269-how-willow-protects-your-data-and-privacy — 2026-10-24 — cloud transcription, Private Mode, Help Improve training.
- https://www.monologue.to/blog/introducing-mono-1 — 2026-10-24 — mono-1 announcement, WildSpeech-Bench numbers, estimated edits, enterprise access.
- https://www.monologue.to/ — 2026-10-24 — "Self-corrections, handled."; local STT, cloud formatting; Notes-only API.
- https://www.monologue.to/docs — 2026-10-24 — docs index.
- https://www.monologue.to/docs/getting-started/first-dictation — 2026-10-24 — "cleans up punctuation, casing, filler words, and false starts".
- https://www.monologue.to/docs/personalize/modes-and-instructions — 2026-10-24 — smart post-processing vs Blazing Fast.
- https://www.monologue.to/docs/dictation/languages-and-models — 2026-10-24 — local mode is STT only; formatting needs network.
- https://www.monologue.to/docs/enterprise-api — 2026-10-24 — private beta; "format existing text"; endpoints.
- https://www.monologue.to/docs/public-api — 2026-10-24 — Notes read-only.
- https://www.monologue.to/changelog — 2026-10-24 — no mono-1 or correction entries.
- https://every.to/on-every/introducing-monologue-effortless-voice-dictation — 2026-10-24 — launch post (2025-09-16), no accuracy numbers.
- https://digg.com/ai/eiitynxp — 2026-10-24 — aggregator that surfaced mono-1; superseded by the primary post.
- https://www.typeless.com/ — 2026-10-24 — fillers, repetitions, self-corrections, lists, tone; no models or API.
- https://www.typeless.com/help/release-notes/windows/introducing-typeless-windows-app-beta — 2026-10-24 — release note (2025-10-22) restating the claims.
- https://spokenly.app/ — 2026-10-24 — AI text processing with modes; Whisper/Parakeet local; BYO keys.
- https://spokenly.app/docs/modes — 2026-10-24 — AI Instructions; OpenAI, Anthropic, any OpenAI-compatible base URL.
- https://spokenly.app/docs/models — 2026-10-24 — full provider lists for dictation and AI processing; Ollama, LM Studio, Apple Intelligence.
- https://spokenly.app/docs/local-only-mode — 2026-10-24 — localhost allowed; no built-in local cleanup.
- https://spokenly.app/llms.txt — 2026-10-24 — no license or repository link.
- https://github.com/Beingpax/VoiceInk — 2026-10-24 — README: GPL v3, engines, feature names.
- https://raw.githubusercontent.com/Beingpax/VoiceInk/main/LICENSE — 2026-10-24 — GPL v3 text.
- https://tryvoiceink.com/ — 2026-10-24 — enhancement examples, optional cloud, pricing.
- https://tryvoiceink.com/docs/modes — 2026-10-24 — starter modes; Refine does fixed cleanup.
- https://tryvoiceink.com/docs/cloud-providers — 2026-10-24 — seven cloud providers.
- https://tryvoiceink.com/docs/local-models — 2026-10-24 — Refine, Ollama, Local CLI.
- https://tryvoiceink.com/docs/custom-models — 2026-10-24 — OpenAI-compatible chat completion endpoint.
- https://tryvoiceink.com/docs/model-settings — 2026-10-24 — skip-short default, timeout default, fallback to original.
- https://huggingface.co/beingpax/voiceink-refine-v1 — 2026-10-24 — Refine card: license "other", Qwen3.5-2B base, MLX 4-bit, no eval numbers.
- https://github.com/cjpais/Handy — 2026-10-24 — README: MIT, models, post-process flag.
- https://raw.githubusercontent.com/cjpais/Handy/main/LICENSE — 2026-10-24 — MIT, CJ Pais 2025.
- https://handy.computer/ — 2026-10-24 — "One tool, one job"; offline.
- https://handy.computer/docs — 2026-10-24 — docs index; post-processing setup mention.
- https://handy.computer/docs/post-processing — 2026-10-24 — providers, OpenAI-compatible endpoint, hotkey-only, experimental.
- https://handy.computer/docs/models — 2026-10-24 — local STT model table with output-form notes (digits vs words, punctuation).
- https://developer.apple.com/videos/play/wwdc2025/277/ — 2026-10-24 — SpeechAnalyzer session: on device, attributed strings, DictationTranscriber fallback, iOS 26.
- https://developer.apple.com/tutorials/data/documentation/speech/speechanalyzer.json — 2026-10-24 — SpeechAnalyzer reference, availability 26.0.
- https://developer.apple.com/tutorials/data/documentation/speech/speechtranscriber.json — 2026-10-24 — SpeechTranscriber reference.
- https://developer.apple.com/tutorials/data/documentation/speech/speechtranscriber/transcriptionoption.json — 2026-10-24 — only case `etiquetteReplacements`.
- https://developer.apple.com/tutorials/data/documentation/speech/speechtranscriber/preset.json — 2026-10-24 — five presets and their options.
- https://developer.apple.com/tutorials/data/documentation/speech/speechtranscriber/reportingoption.json — 2026-10-24 — three reporting options.
- https://developer.apple.com/tutorials/data/documentation/speech/dictationtranscriber.json — 2026-10-24 — DictationTranscriber reference, content hints, vocabulary biasing.
- https://developer.apple.com/tutorials/data/documentation/speech/dictationtranscriber/transcriptionoption.json — 2026-10-24 — `emoji`, `etiquetteReplacements`, `punctuation`.
- https://developer.apple.com/tutorials/data/documentation/speech/dictationtranscriber/preset.json — 2026-10-24 — presets; `phrase` unpunctuated, others punctuated.
- https://developer.apple.com/tutorials/data/documentation/speech/bringing-advanced-speech-to-text-capabilities-to-your-app.json — 2026-10-24 — sample article metadata only.
- https://support.apple.com/guide/mac-help/use-dictation-mh40584/mac — 2026-10-24 — on-device general dictation, auto-punctuation, commands.
- https://developers.deepgram.com/docs/punctuation — 2026-10-24 — `punctuate` default false.
- https://developers.deepgram.com/docs/smart-format — 2026-10-24 — `smart_format` default false and sub-features.
- https://developers.deepgram.com/docs/filler-words — 2026-10-24 — `filler_words` default false; "uh"/"um" removed by default.
- https://developers.deepgram.com/docs/paragraphs — 2026-10-24 — `paragraphs` default false.
- https://developers.deepgram.com/docs/numerals — 2026-10-24 — `numerals` default false.
- https://developers.deepgram.com/docs/dictation — 2026-10-24 — spoken punctuation commands; requires punctuate.
- https://developers.deepgram.com/docs/text-intelligence — 2026-10-24 — text-in analysis, no cleanup.
- https://www.assemblyai.com/docs/pre-recorded-audio/filler-words — 2026-10-24 — fillers removed by default; `disfluencies=true` keeps them; model/language support.
- https://www.assemblyai.com/docs/api-reference/transcripts/submit — 2026-10-24 — `disfluencies`, `punctuate`, `format_text`, `filter_profanity` defaults; `speech_models` default.
- https://www.assemblyai.com/docs/lemur — 2026-10-24 — renders LLM Gateway content; no LeMUR cleanup feature.
- https://assemblyai.com/docs/getting-started/apply-llms-to-audio-files — 2026-10-24 — LLM Gateway `transcript_id` substitution; no cleanup.
- https://www.assemblyai.com/docs/sdk-references/python/le-mur — 2026-10-24 — renders LLM Gateway summary; no LeMUR parameters.
- https://www.assemblyai.com/docs/api-reference/lemur/task — 2026-10-24 — renders LLM Gateway chat-completions parameters.
- https://docs.speechmatics.com/features/punctuation-settings — 2026-10-24 — punctuation overrides, `remove_disfluencies` default false, entities on by default.
- https://docs.speechmatics.com/features/word-tagging — 2026-10-24 — disfluency tags, languages, removal config.
- https://docs.speechmatics.com/features/entities — 2026-10-24 — smart formatting on by default; `spoken_form` via `enable_entities`.
- https://docs.gladia.io/chapters/pre-recorded-stt/features — 2026-10-24 — feature index; no disfluency option.
- https://docs.gladia.io/api-reference/v2/pre-recorded/init — 2026-10-24 — `punctuation_enhanced`, `custom_spelling`, `custom_vocabulary` defaults.
- https://docs.gladia.io/chapters/pre-recorded-stt/features/custom-vocabulary — 2026-10-24 — vocabulary entry schema and intensity guidance.
- https://docs.gladia.io/chapters/audio-intelligence/custom-spelling.md — 2026-10-24 — literal replacement post-processing.
- https://huggingface.co/ReFyneLabs/simplewords-dictation-cleanup-v3 — 2026-10-24 — our model card: Apache 2.0, gated, prompt file, per-category gates.

Unreachable or empty pages (recorded, not cited above as evidence):
https://developers.deepgram.com/docs/smart-format (reached); https://www.assemblyai.com/docs/speech-to-text/pre-recorded-audio/filler-words (404); https://www.assemblyai.com/docs/speech-to-text/pre-recorded-audio/text-formatting (404); https://docs.speechmatics.com/features/output-formatting (404); https://feedback.monologue.to/changelog (404); https://www.monologue.to/mono-1 (404); https://x.com/usemonologue/status/2103165807442485742 (HTTP 402); https://tryvoiceink.com/docs/refine (404); https://developer.apple.com/documentation/speech/speechanalyzer, .../speechtranscriber, .../speechtranscriber/transcriptionoption and .../bringing-advanced-speech-to-text-capabilities-to-your-app (HTML pages served titles only; the JSON data endpoints above were used instead); https://docs.monologue.to/ and https://help.monologue.to/en/articles/14178197-dictating-with-monologue (308 redirects to www.monologue.to/docs, followed).
