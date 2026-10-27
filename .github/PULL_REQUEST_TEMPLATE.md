<!--
Row submissions: fill in the checklist below. The mechanics are in SUBMITTING.md,
the rules in GOVERNANCE.md. Code or documentation changes: delete the checklist
and describe the change.
-->

## Row submission checklist

- [ ] This PR adds exactly one `runs/<system>/<date>/` folder containing `run.json`, `outputs.jsonl` and `scores.json`, and nothing else.
- [ ] The two passes hash identical (`determinism.identical: true` in the manifest), or this is a hosted row with `nondeterministic: true` and `hosted: true`.
- [ ] `scores.json` was produced by the scorer and `uv run cleanupbench score --check runs/<system>/<date>` prints `ok`.
- [ ] `uv run cleanupbench validate` passes.
- [ ] The attestation below is copied from the manifest.
- [ ] A system description is linked below (a model card, a README or a paper; a closed system still needs a description of what was called and how).
- [ ] This PR text makes no comparative claim about any row.
- [ ] If this is a row of Superwhisper's S1-mini, the manifest names it so that it prints as "S1-mini" by "Superwhisper", with that capitalisation.

## Attestation (copied from `run.json`)

```json
"attestation": {
  "no_training_on_items": ,
  "known_overlap": "",
  "declared_exposure": ""
}
```

## System description

Link:

## Checked mark

- [ ] I ask the maintainer to re-run a random subset of items for the "checked" mark.
