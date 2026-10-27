# Issue text for `pomvox/pomvox-cleanup-engine` (decision 17)

To be filed by the owner if decision 17 in `docs/decisions.md` is confirmed.
Nothing in the engine repository is changed from the bench repository.

---

**Title:** Guard and prompt assume sentence shape; fragments and single words get forced casing and a terminal period

**Body:**

Cleanup Bench (pomvox/cleanup-bench, `docs/spec.md` §2.2 and §3.4, decision
17 in `docs/decisions.md`) scores fragment and single-word inputs under the
rule "returned as said, minimally cased, no forced terminal period". The rule
comes from user reports that forced capitalization and periods on short
inserts are a damaging failure (`docs/research/06-user-pain.md` §1, §6, e.g.
Beingpax/VoiceInk#378).

The engine's frozen prompt and guard treat sentence shape as the norm:

- `CleanupLogic.swift` admits "Go ahead." for "go ahead" through
  `shortWordOverlap`, and the app's `eval_cleanup_v2.py` has a `period`
  special check that *requires* a terminal mark on `"go ahead"`.
- The vault's negatives (set D) are full sentences, so the model has no
  training signal for keeping a fragment a fragment.

Under the bench's rule, a period-terminated fragment scores as a false-positive
edit against the reference. This is intended by the bench and is reported, not
hidden. This issue asks the engine repository to decide whether:

1. the frozen prompt and corpus should treat fragments as fragments (a model
   and corpus change, a new pack version), or
2. the engine documents sentence-termination of fragments as deliberate
   behaviour, in which case the bench's `negatives/fragments` slice will show
   it as a cost on the board.

No change is requested in the bench's scoring either way. Related bench
material: `docs/spec.md` §2.2 "Fragments and single words", §3.4.
