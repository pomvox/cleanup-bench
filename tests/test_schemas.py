"""Schema tests for items, manifests and output records (phase 1)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from cleanupbench.hashing import sha256_file, sha256_text
from cleanupbench.items import (
    Item,
    ItemError,
    items_sha256,
    load_items,
    validate_item_object,
    validate_items_dir,
)
from cleanupbench.manifest import (
    ManifestError,
    OutputRecord,
    check_run_dir,
    read_outputs,
    validate_manifest_object,
    validate_output_object,
    write_manifest,
    write_outputs,
)

SHA = "0" * 64


def good_item() -> dict:
    return {
        "id": "negatives-negation-0001",
        "category": "negatives",
        "slice": "negation",
        "input": "never merge a change like this without a review",
        "input_form": "lowercase-unpunctuated",
        "vocabulary": [],
        "references": ["Never merge a change like this without a review."],
        "slots": {"must_contain": ["never"], "must_not_contain": []},
        "source": {
            "type": "synthetic",
            "method": "hand-written",
            "origin": "cleanup-bench authors",
            "license": "CC-BY-4.0",
            "attribution": "",
        },
        "notes": "negation word must survive",
        "taxonomy": [],
        "released": "2026-10-27",
        "status": "active",
        "scored": True,
    }


def good_manifest() -> dict:
    return {
        "schema_version": 1,
        "bench_version": "1.0.0-dev",
        "items_sha256": SHA,
        "system": {
            "name": "identity",
            "org": "Pomvox",
            "organizer_row": True,
            "model_id": "none",
            "model_revision": "none",
            "open_weights": True,
            "license": "MIT",
            "params_total": 0,
            "params_total_note": "",
            "weights_sha256": SHA,
        },
        "adapter": {"name": "identity", "version": "1", "config": {}},
        "prompt": {"sha256": sha256_text(""), "text": ""},
        "decoding": {"strategy": "greedy", "temperature": 0, "max_tokens": None},
        "vocabulary_policy": {"source": "none", "rendering": ""},
        "hardware": {"machine": "test", "os": "test", "accelerator": "none", "ram_gb": None},
        "software": {"python": "3.12", "packages": {}, "bench_commit": "test"},
        "run": {"started_at": "2026-10-27T00:00:00Z", "finished_at": "2026-10-27T00:00:01Z", "item_count": 1},
        "determinism": {"run_a_sha256": SHA, "run_b_sha256": SHA, "identical": True},
        "outputs_sha256": SHA,
        "attestation": {"no_training_on_items": True, "known_overlap": "", "declared_exposure": "none"},
        "hosted": False,
        "hosted_expiry_flag": None,
        "checked_by": None,
        "checked_date": None,
    }


def good_output() -> dict:
    return {
        "id": "negatives-negation-0001",
        "output_text": "Never merge a change like this without a review.",
        "outcome": "cleaned",
        "fallback_reason": None,
        "edits": None,
        "warnings": [],
        "latency_ms": 1.5,
        "raw": None,
    }


# --- items -------------------------------------------------------------------


def test_good_item_validates():
    assert validate_item_object(good_item()) == []


@pytest.mark.parametrize(
    "mutate, fragment",
    [
        (lambda o: o.pop("references"), "'references' is a required property"),
        (lambda o: o.__setitem__("references", []), "should be non-empty"),
        (lambda o: o.__setitem__("references", ["a", "b", "c", "d"]), "is too long"),
        (lambda o: o.__setitem__("category", "fluff"), "is not one of"),
        (lambda o: o.__setitem__("input_form", "shouting"), "is not one of"),
        (lambda o: o.__setitem__("id", "bad id"), "does not match"),
        (lambda o: o.__setitem__("released", "27/10/2026"), "does not match"),
        (lambda o: o.__setitem__("status", "retired"), "'retired_in' is a required property"),
        (lambda o: o.__setitem__("extra", 1), "Additional properties are not allowed"),
        (lambda o: o.__setitem__("vocabulary", ["two\nlines"]), "does not match"),
        (lambda o: o["source"].__setitem__("type", "scraped"), "is not one of"),
        (lambda o: o["source"].__setitem__("method", "magic"), "does not match"),
        (lambda o: o.__setitem__("taxonomy", ["banana"]), "is not one of"),
    ],
)
def test_bad_items_are_rejected(mutate, fragment):
    obj = good_item()
    mutate(obj)
    errors = validate_item_object(obj)
    assert errors, "expected a validation error"
    assert any(fragment in e for e in errors), errors


def test_id_must_match_category_and_slice():
    obj = good_item()
    obj["id"] = "fillers-core-0001"
    errors = validate_item_object(obj)
    assert any("must start with 'negatives-negation-'" in e for e in errors)


def test_whitespace_padding_is_rejected():
    obj = good_item()
    obj["input"] = " padded"
    assert any("leading or trailing whitespace" in e for e in validate_item_object(obj))


def test_duplicate_references_rejected():
    obj = good_item()
    obj["references"] = ["Same.", "Same."]
    assert any("duplicate reference" in e for e in validate_item_object(obj))


def test_item_roundtrip():
    obj = good_item()
    item = Item.from_json(obj)
    assert item.to_json() == obj
    assert item.is_scorable


def test_retired_item_not_scorable():
    obj = good_item()
    obj.update({"status": "retired", "retired_in": "1.1.0", "issue": "https://example.org/1"})
    assert validate_item_object(obj) == []
    assert not Item.from_json(obj).is_scorable


def write_item_file(dir_: Path, name: str, objs: list[dict], canary: str = "canary TEST") -> Path:
    path = dir_ / name
    lines = [f"# {canary}"] + [json.dumps(o, ensure_ascii=False) for o in objs]
    path.write_text("\n".join(lines) + "\n", "utf-8")
    return path


def test_items_dir_validation_and_loading(tmp_path: Path):
    write_item_file(tmp_path, "negatives.jsonl", [good_item()])
    assert validate_items_dir(tmp_path, require_canary="canary TEST") == []
    items = load_items(tmp_path)
    assert [i.id for i in items] == ["negatives-negation-0001"]
    assert items_sha256(tmp_path) == items_sha256(tmp_path)


def test_items_dir_rejects_wrong_file_and_duplicates(tmp_path: Path):
    write_item_file(tmp_path, "fillers.jsonl", [good_item()])
    errors = validate_items_dir(tmp_path)
    assert any("does not match file" in e for e in errors)
    write_item_file(tmp_path, "negatives.jsonl", [good_item(), good_item()])
    errors = validate_items_dir(tmp_path)
    assert any("duplicate id" in e for e in errors)


def test_items_dir_requires_canary(tmp_path: Path):
    write_item_file(tmp_path, "negatives.jsonl", [good_item()], canary="nothing here")
    errors = validate_items_dir(tmp_path, require_canary="canary GUID 1234")
    assert any("canary string missing" in e for e in errors)


def test_load_items_raises_on_invalid(tmp_path: Path):
    obj = good_item()
    del obj["notes"]
    write_item_file(tmp_path, "negatives.jsonl", [obj])
    with pytest.raises(ItemError):
        load_items(tmp_path)


def test_items_sha256_changes_with_content(tmp_path: Path):
    write_item_file(tmp_path, "negatives.jsonl", [good_item()])
    before = items_sha256(tmp_path)
    obj = good_item()
    obj["notes"] = "different"
    write_item_file(tmp_path, "negatives.jsonl", [obj])
    assert items_sha256(tmp_path) != before


# --- manifest ----------------------------------------------------------------


def test_good_manifest_validates():
    assert validate_manifest_object(good_manifest()) == []


@pytest.mark.parametrize(
    "mutate, fragment",
    [
        (lambda m: m.pop("determinism"), "'determinism' is a required property"),
        (lambda m: m.pop("attestation"), "'attestation' is a required property"),
        (lambda m: m["decoding"].__setitem__("strategy", "sampling"), "was expected"),
        (lambda m: m["decoding"].__setitem__("temperature", 0.7), "was expected"),
        (lambda m: m["adapter"].__setitem__("name", "llama-cpp"), "is not one of"),
        (lambda m: m.__setitem__("items_sha256", "abc"), "does not match"),
        (lambda m: m["system"].pop("weights_sha256"), "'weights_sha256' is a required property"),
        (lambda m: m["system"].__setitem__("params_total", None), "should be non-empty"),
        (lambda m: m.__setitem__("surprise", True), "Additional properties are not allowed"),
        (lambda m: m["run"].__setitem__("started_at", "yesterday"), "does not match"),
        (lambda m: m["attestation"].__setitem__("declared_exposure", "maybe"), "is not one of"),
    ],
)
def test_bad_manifests_are_rejected(mutate, fragment):
    m = good_manifest()
    mutate(m)
    errors = validate_manifest_object(m)
    assert errors
    assert any(fragment in e for e in errors), errors


def test_hosted_manifest_needs_api_fields():
    m = good_manifest()
    m["hosted"] = True
    errors = validate_manifest_object(m)
    assert any("'api_model_id' is a required property" in e for e in errors)
    m["system"]["api_model_id"] = "claude-x"
    m["system"]["api_date"] = "2026-10-27"
    assert validate_manifest_object(m) == []


# --- outputs -----------------------------------------------------------------


def test_good_output_validates():
    assert validate_output_object(good_output()) == []


def test_output_edit_shape():
    o = good_output()
    o["edits"] = [{"start": 0, "end": 1, "replacement": "N", "extra": 1}]
    assert any("Additional properties" in e for e in validate_output_object(o))
    o["edits"] = [{"start": 0, "end": 1, "replacement": "N"}]
    assert validate_output_object(o) == []


def test_outputs_roundtrip_is_deterministic(tmp_path: Path):
    recs = [OutputRecord.from_json(good_output()), OutputRecord.from_json({**good_output(), "id": "a-core-0001"})]
    p1 = tmp_path / "a.jsonl"
    p2 = tmp_path / "b.jsonl"
    write_outputs(p1, recs)
    write_outputs(p2, list(reversed(recs)))
    assert sha256_file(p1) == sha256_file(p2)
    assert [r.id for r in read_outputs(p1)] == ["a-core-0001", "negatives-negation-0001"]


# --- run folder cross-checks ---------------------------------------------------


def make_run_dir(tmp_path: Path, manifest: dict | None = None) -> Path:
    run_dir = tmp_path / "runs" / "identity" / "2026-10-27"
    run_dir.mkdir(parents=True)
    write_outputs(run_dir / "outputs.jsonl", [OutputRecord.from_json(good_output())])
    m = copy.deepcopy(manifest or good_manifest())
    m["outputs_sha256"] = sha256_file(run_dir / "outputs.jsonl")
    write_manifest(run_dir / "run.json", m)
    return run_dir


def test_check_run_dir_ok(tmp_path: Path):
    run_dir = make_run_dir(tmp_path)
    manifest, records = check_run_dir(run_dir)
    assert manifest["system"]["name"] == "identity"
    assert len(records) == 1


def test_check_run_dir_refuses_hash_mismatch(tmp_path: Path):
    run_dir = make_run_dir(tmp_path)
    (run_dir / "outputs.jsonl").write_text("", "utf-8")
    with pytest.raises(ManifestError, match="outputs_sha256"):
        check_run_dir(run_dir)


def test_check_run_dir_refuses_nondeterministic(tmp_path: Path):
    m = good_manifest()
    m["determinism"] = {"run_a_sha256": SHA, "run_b_sha256": "1" * 64, "identical": False}
    run_dir = make_run_dir(tmp_path, m)
    with pytest.raises(ManifestError, match="determinism"):
        check_run_dir(run_dir)
    with pytest.raises(ManifestError, match="determinism"):
        check_run_dir(run_dir, allow_nondeterministic=True)  # not hosted, not flagged


def test_check_run_dir_allows_flagged_hosted_nondeterministic(tmp_path: Path):
    m = good_manifest()
    m["hosted"] = True
    m["nondeterministic"] = True
    m["system"]["api_model_id"] = "x"
    m["system"]["api_date"] = "2026-10-27"
    m["determinism"] = {"run_a_sha256": SHA, "run_b_sha256": "1" * 64, "identical": False}
    run_dir = make_run_dir(tmp_path, m)
    with pytest.raises(ManifestError):
        check_run_dir(run_dir)
    manifest, _ = check_run_dir(run_dir, allow_nondeterministic=True)
    assert manifest["nondeterministic"] is True


def test_check_run_dir_refuses_item_count_mismatch(tmp_path: Path):
    m = good_manifest()
    m["run"]["item_count"] = 2
    run_dir = make_run_dir(tmp_path, m)
    with pytest.raises(ManifestError, match="item_count"):
        check_run_dir(run_dir)


def test_write_manifest_refuses_invalid(tmp_path: Path):
    m = good_manifest()
    del m["hosted"]
    with pytest.raises(ManifestError):
        write_manifest(tmp_path / "run.json", m)
