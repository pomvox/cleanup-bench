# Prompts

Prompt files used by the bench's own baseline rows (docs/spec.md section 8).
Every run manifest records `prompt.sha256` and `prompt.text` (section 9), so
a row is tied to the exact bytes of the prompt it ran with.

## `generic-v1.txt`

The bench's own fixed generic cleanup prompt, version 1, written in plain
prose from the task definition in `docs/spec.md` section 2.2. It is
**frozen**: the file is never edited. A change is a new file (`generic-v2.txt`)
and a new row; rows that ran with v1 keep their recorded hash. Used by the
`generic-local` and `generic-cloud` rows.

## `s1-mini-system.txt` (not committed until fetched)

The S1-mini row (decision 12) needs the exact system prompt from the model
card at https://huggingface.co/superwhisper/s1-mini. The runbook
(`docs/MAC_STUDIO_RUNBOOK.md`) fetches it: open the card, copy the system
prompt verbatim into `prompts/s1-mini-system.txt`, and record below the card
URL and the date it was copied. The control line
`[Styling: semi-formal] [Structure: prose] [Context: general]` is not part of
the file; the adapter appends it and the manifest records it as
`prompt.control_line`.

- Card URL: (record when fetched)
- Copied on: (record when fetched)

## SimpleWords v3

The SimpleWords rows do not use a file here. The engine row reads the prompt
from inside the pack (`system_v2.txt`; its in-pack sha256 is recorded in
`adapter.config.prompt_sha256_in_pack`), and the mlx-lm row reads
`system_v2.txt` from the Hugging Face snapshot and records its text and hash
in the manifest.
