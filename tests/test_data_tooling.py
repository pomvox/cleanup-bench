"""Generation gates, Disfl-QA derivation, review and promotion (docs/spec.md section 7)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cleanupbench.canary import CANARY, CANARY_GUID
from cleanupbench.data.disflqa import derive, label, reparandum_tokens, to_input_form
from cleanupbench.data.gates import gate_candidates, run_gates
from cleanupbench.data.review import agreement, cohens_kappa, promote, read_sheet, review_sheet, verdicts
from cleanupbench.items import load_items


def good_candidate(**overrides) -> dict:
    obj = {
        "id": "fillers-core-0001",
        "category": "fillers",
        "input": "um so let's go",
        "input_form": "lowercase-unpunctuated",
        "vocabulary": [],
        "references": ["Let's go."],
        "slots": {"must_contain": ["go"], "must_not_contain": ["um"]},
        "source": {
            "type": "synthetic",
            "method": "hand-written",
            "origin": "test",
            "license": "CC-BY-4.0",
            "attribution": "",
        },
        "notes": "filled pause removed",
        "taxonomy": ["filled-pause"],
        "released": "2026-10-27",
        "status": "active",
        "scored": True,
    }
    obj.update(overrides)
    return obj


# --- gates --------------------------------------------------------------------------


def test_gates_pass_on_a_good_candidate():
    assert run_gates(good_candidate()) == {}


def test_gate_schema():
    failed = run_gates(good_candidate(category="nonsense"))
    assert "schema" in failed


def test_gate_slots_against_own_reference():
    failed = run_gates(good_candidate(slots={"must_contain": ["um"], "must_not_contain": []}))
    assert "slots" in failed


def test_gate_no_content_loss_empty_reference_needs_declaration():
    failed = run_gates(
        good_candidate(input="um uh", references=[""], slots={"must_contain": [], "must_not_contain": ["um"]})
    )
    assert "no-content-loss" in failed
    ok = run_gates(
        good_candidate(
            input="um uh",
            references=[""],
            slots={"must_contain": [], "must_not_contain": ["um"]},
            notes="filler-only input",
        )
    )
    assert ok == {}


def test_gate_no_invention_and_sanctioned_tokens():
    cand = good_candidate(
        input="we sold twenty five units",
        references=["We sold 25 units."],
        slots={"must_contain": [], "must_not_contain": []},
    )
    failed = run_gates(cand)
    assert "no-invention" in failed and "25" in failed["no-invention"][0]
    assert run_gates(cand, sanctioned_tokens=["25"]) == {}
    # Vocabulary spellings are allowed.
    cand2 = good_candidate(
        input="email salamagari",
        references=["Email Salammagari."],
        vocabulary=["Salammagari"],
        slots={"must_contain": [], "must_not_contain": []},
    )
    assert run_gates(cand2) == {}


def test_gate_input_form():
    assert list(run_gates(good_candidate(input="Um so let's go"))) == ["input-form"]  # uppercase
    assert list(run_gates(good_candidate(input="um  so let's go"))) == ["input-form"]  # double space
    ok = good_candidate(
        input="at six o'clock twenty-five people",
        references=["At six o'clock twenty-five people"],
        slots={"must_contain": [], "must_not_contain": []},
    )
    assert run_gates(ok) == {}


def test_gate_no_canary():
    assert "no-canary" in run_gates(good_candidate(notes=f"contains {CANARY_GUID}"))


def test_gate_candidates_logs_discards(tmp_path: Path):
    log = tmp_path / "discards.jsonl"
    passing, discarded = gate_candidates(
        [good_candidate(), good_candidate(id="fillers-core-0002", input="Um so let's go")],
        discard_log=log,
        stage="test",
    )
    assert [c["id"] for c in passing] == ["fillers-core-0001"]
    assert [d["id"] for d in discarded] == ["fillers-core-0002"]
    rec = json.loads(log.read_text("utf-8").strip())
    assert rec["gates_failed"] == ["input-form"] and rec["stage"] == "test"


# --- Disfl-QA derivation --------------------------------------------------------------


def test_to_input_form():
    assert to_input_form("In what country is Normandy located?") == "in what country is normandy located"
    assert (
        to_input_form("Who gave their name to Normandy in the 1000's and 1100's")
        == "who gave their name to normandy in the 1000's and 1100's"
    )
    assert to_input_form("Well - no, 'quoted' word's") == "well no quoted word's"


def test_label_interrogative_vs_intra():
    assert (
        label(
            "When were the Normans in Normandy?", "From which countries no tell me when were the Normans in Normandy?"
        )
        == "correction-interrogative"
    )
    assert label("Who was the Norse leader?", "When I mean who was the Norse leader?") == "correction-interrogative"
    assert label("What is France a region of?", "What is Denmark a region of uh no France?") == "correction-intra"
    assert (
        label(
            "From which countries did the Norse originate?",
            "From which Norse leader I mean countries did the Norse originate?",
        )
        == "correction-intra"
    )


def test_reparandum_tokens_exclude_editing_terms():
    assert reparandum_tokens(
        "When were the Normans in Normandy?", "From which countries no tell me when were the Normans in Normandy?"
    ) == ["from", "which", "countries"]
    assert reparandum_tokens("What is France a region of?", "What is Denmark a region of uh no France?") == ["denmark"]


DATA = {
    "id1": {
        "original": "When were the Normans in Normandy?",
        "disfluent": "From which countries no tell me when were the Normans in Normandy?",
    },
    "id2": {"original": "What is France a region of?", "disfluent": "What is Denmark a region of uh no France?"},
    "id3": {"original": "Who was the Norse leader?", "disfluent": "When I mean who was the Norse leader?"},
    "id4": {
        "original": "Who did King Charles III swear fealty to?",
        "disfluent": "Who did King Rollo or instead uh Charles III swear fealty to?",
    },
    "id5": {
        "original": "In what country is Normandy located?",
        "disfluent": "In what country is Norse found no wait Normandy not Norse?",
    },
}


def test_derive_is_deterministic_and_gated(tmp_path: Path):
    b1 = derive(DATA, per_category=1, seed=7, released="2026-10-27")
    b2 = derive(DATA, per_category=1, seed=7, released="2026-10-27")
    assert b1 == b2
    assert len(b1["correction-interrogative"]) == 1 and len(b1["correction-intra"]) == 1 and len(b1["negatives"]) == 1
    # No input appears twice across buckets.
    inputs = [c["input"] for cat in b1.values() for c in cat]
    assert len(inputs) == len(set(inputs))
    # Every candidate validates and the gates pass or discard (id5's reference says "located", the input says "found").
    all_cands = [c for cat in b1.values() for c in cat]
    passing, discarded = gate_candidates(all_cands, discard_log=tmp_path / "d.jsonl", stage="t")
    assert len(passing) + len(discarded) == len(all_cands)
    for c in passing:
        assert c["source"]["type"] == "derived" and "CC BY 4.0 as asserted" in c["source"]["attribution"]
    # Start sequences continue past existing ids.
    b3 = derive(DATA, per_category=1, seed=7, released="2026-10-27", start_seq={"correction-intra": 10})
    assert b3["correction-intra"][0]["id"] == "correction-intra-core-0011"


def test_candidate_id5_is_discarded_for_invention(tmp_path: Path):
    only = {"id5": DATA["id5"]}
    b = derive(only, per_category=1, seed=1, released="2026-10-27")
    cands = [c for cat in b.values() for c in cat]
    _, discarded = gate_candidates(cands, discard_log=tmp_path / "d.jsonl", stage="t")
    assert any("no-invention" in d["gates_failed"] for d in discarded)


# --- review and promotion -----------------------------------------------------------------


def test_review_sheet_and_verdicts():
    drafts = [
        good_candidate(),
        good_candidate(
            id="fillers-core-0002",
            input="uh okay",
            references=["Okay"],
            slots={"must_contain": ["okay"], "must_not_contain": ["uh"]},
        ),
    ]
    sheet = review_sheet(drafts, reviewer="r1")
    assert [r["id"] for r in sheet] == ["fillers-core-0001", "fillers-core-0002"]
    assert sheet[0]["consistent"] is None
    a = [dict(r, consistent=True, natural=True, laws=True) for r in sheet]
    b = [dict(r, consistent=True, natural=True, laws=(r["id"] != "fillers-core-0002")) for r in sheet]
    v = verdicts([a, b])
    assert v == {"fillers-core-0001": True, "fillers-core-0002": False}


def test_cohens_kappa_hand_worked():
    # Two reviewers agree on 3 of 4; a says yes 3 times, b says yes 2 times.
    # po = 0.75; pe = 0.75*0.5 + 0.25*0.5 = 0.5; kappa = (0.75 - 0.5) / 0.5 = 0.5
    assert cohens_kappa([True, True, True, False], [True, True, False, False]) == 0.5
    assert cohens_kappa([True, True], [True, True]) is None  # expected agreement is 1
    assert cohens_kappa([], []) is None


def test_agreement_report():
    drafts = [
        good_candidate(),
        good_candidate(
            id="fillers-core-0002",
            input="uh okay",
            references=["Okay"],
            slots={"must_contain": [], "must_not_contain": ["uh"]},
        ),
    ]
    sheet = review_sheet(drafts, reviewer="r1")
    a = [dict(r, consistent=True, natural=True, laws=True) for r in sheet]
    b = [dict(r, consistent=True, natural=False, laws=True) for r in sheet]
    rep = agreement(a, b)
    assert rep["items_in_common"] == 2
    assert rep["categories"]["fillers"]["consistent"]["raw_agreement"] == 1.0
    assert rep["categories"]["fillers"]["natural"]["raw_agreement"] == 0.0


def test_promote_appends_and_logs(tmp_path: Path):
    items_dir = tmp_path / "items"
    items_dir.mkdir()
    (items_dir / "fillers.jsonl").write_text(
        f"# {CANARY}\n" + json.dumps(good_candidate(id="fillers-core-0001")) + "\n", "utf-8"
    )
    drafts = [
        good_candidate(
            id="fillers-core-0002",
            input="uh okay",
            references=["Okay"],
            slots={"must_contain": ["okay"], "must_not_contain": ["uh"]},
        ),
        good_candidate(
            id="fillers-core-0003",
            input="uh yes",
            references=["Yes"],
            slots={"must_contain": ["yes"], "must_not_contain": ["uh"]},
        ),
        good_candidate(
            id="fillers-core-0004",
            input="uh fine",
            references=["Fine"],
            slots={"must_contain": ["fine"], "must_not_contain": ["uh"]},
        ),
    ]
    accepted = {"fillers-core-0002": True, "fillers-core-0003": False}  # 0004 unreviewed
    promoted, discarded = promote(
        drafts, accepted, items_dir=items_dir, discard_log=tmp_path / "d.jsonl", released="2026-11-01"
    )
    assert promoted == ["fillers-core-0002"] and discarded == ["fillers-core-0003"]
    items = load_items(items_dir)
    assert [i.id for i in items] == ["fillers-core-0001", "fillers-core-0002"]
    assert items[1].released == "2026-11-01"
    log = [json.loads(line) for line in (tmp_path / "d.jsonl").read_text("utf-8").splitlines()]
    assert log[0]["id"] == "fillers-core-0003" and log[0]["stage"] == "review"


def test_read_sheet_requires_answers(tmp_path: Path):
    p = tmp_path / "s.jsonl"
    p.write_text(json.dumps({"id": "x", "consistent": True, "natural": None, "laws": True}) + "\n", "utf-8")
    with pytest.raises(ValueError, match="natural"):
        read_sheet(p)
