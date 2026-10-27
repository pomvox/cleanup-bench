# Text for the SimpleWords v3 model card (decision 11)

To be acted on by the owner on Hugging Face if decision 11 in
`docs/decisions.md` is confirmed. Nothing on Hugging Face is changed from the
bench repository.

---

**Request:** remove the access gate on
`ReFyneLabs/simplewords-dictation-cleanup-v3` (and the `abhiram3040/...` id
that resolves to the same card), or publish an ungated mirror of the seven
artifacts the engine's `packs/simplewords-v3/pack.json` pins
(`chat_template.jinja`, `config.json`, `model.safetensors`,
`model.safetensors.index.json`, `system_v2.txt`, `tokenizer.json`,
`tokenizer_config.json`).

**Why:** Cleanup Bench's rule is that every leaderboard row is reproducible by
a stranger with one command (`docs/PROMPT.md`; `docs/spec.md` §9). On
2026-10-24 both model ids resolved to a gated Apache-2.0 card
(`docs/research/00-summary.md`, Sources). A gate means the stranger needs a
Hugging Face account and must accept conditions before `cleanupbench run` can
fetch the weights; the bench marks such rows `gated-download` until the gate
is gone (`docs/spec.md` §12).

**Also on the card, from the vault's verification notes (not a request, a
note the card author may want):** `system_v2.txt` is described as
byte-identical across v2 and v3; the vault records the two files differ by a
trailing newline and are equal only after stripping. The engine pack pins the
v3 file at 1,100 bytes. The bench hashes the prompt it actually sends, after
stripping, and records that hash in the manifest.
