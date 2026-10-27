"""End to end: the real `run` command with the identity adapter, then `score`, then `score --check`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cleanupbench import BENCH_VERSION
from cleanupbench.canary import CANARY
from cleanupbench.cli import main
from cleanupbench.manifest import ManifestError, read_manifest
from cleanupbench.runner import determinism_hash, run
from cleanupbench.scorer.score import score_run


def item(id_, category, input_, refs, must=(), must_not=(), slice_=None, **extra):
    obj = {
        "id": id_,
        "category": category,
        "input": input_,
        "input_form": "lowercase-unpunctuated",
        "vocabulary": [],
        "references": list(refs),
        "slots": {"must_contain": list(must), "must_not_contain": list(must_not)},
        "source": {
            "type": "synthetic",
            "method": "hand-written",
            "origin": "test",
            "license": "CC-BY-4.0",
            "attribution": "",
        },
        "notes": "test item",
        "taxonomy": [],
        "released": "2026-10-27",
        "status": "active",
        "scored": True,
    }
    if slice_:
        obj["slice"] = slice_
    obj.update(extra)
    return obj


@pytest.fixture
def items_dir(tmp_path: Path) -> Path:
    d = tmp_path / "items"
    d.mkdir()
    files = {
        "fillers.jsonl": [
            item("fillers-core-0001", "fillers", "um so let's go", ["Let's go."], must=["go"], must_not=["um"]),
            item("fillers-core-0002", "fillers", "um uh so yeah", [""], must_not=["um"]),
        ],
        "negatives.jsonl": [
            item(
                "negatives-negation-0001",
                "negatives",
                "never merge a change like this",
                ["Never merge a change like this."],
                must=["never"],
                slice_="negation",
            ),
            item(
                "negatives-fragments-0001",
                "negatives",
                "okay",
                ["Okay"],
                must=["okay"],
                slice_="fragments",
            ),
        ],
        "spoken-form.jsonl": [
            item(
                "spoken-form-cardinal-0001",
                "spoken-form",
                "we sold twenty five units",
                ["We sold twenty five units.", "We sold 25 units."],
                must=["units"],
                slice_="cardinal",
            ),
            item(
                "spoken-form-cardinal-0002",
                "spoken-form",
                "step one is easy",
                ["Step one is easy."],
                must=["step one"],
                slice_="cardinal",
                scored=False,
                input_form="cased-punctuated",
            ),
        ],
    }
    for name, objs in files.items():
        (d / name).write_text("# " + CANARY + "\n" + "\n".join(json.dumps(o) for o in objs) + "\n", "utf-8")
    return d


@pytest.fixture
def run_config(tmp_path: Path) -> Path:
    p = tmp_path / "run-config.json"
    p.write_text(
        json.dumps(
            {
                "system_name": "identity",
                "system_org": "Pomvox",
                "organizer_row": True,
                "attestation": {"no_training_on_items": True, "known_overlap": "", "declared_exposure": "none"},
                "hardware": {"machine": "test", "os": "test", "accelerator": "none", "ram_gb": None},
            }
        ),
        "utf-8",
    )
    return p


def test_run_identity_then_score(tmp_path: Path, items_dir: Path, run_config: Path, capsys):
    runs = tmp_path / "runs"
    rc = main(
        [
            "run",
            "--adapter",
            "identity",
            "--config",
            str(run_config),
            "--items",
            str(items_dir),
            "--runs",
            str(runs),
            "--date",
            "2026-10-27",
        ]
    )
    assert rc == 0, capsys.readouterr().err
    run_dir = runs / "identity" / "2026-10-27"
    assert (run_dir / "run.json").is_file() and (run_dir / "outputs.jsonl").is_file()
    manifest = read_manifest(run_dir)
    assert manifest["determinism"]["identical"] is True
    assert manifest["run"]["item_count"] == 5  # the unscored item is excluded
    assert manifest["system"]["organizer_row"] is True
    assert manifest["bench_version"] == BENCH_VERSION

    rc = main(["score", str(run_dir), "--items", str(items_dir), "--bootstrap-resamples", "20"])
    assert rc == 0
    scores = json.loads((run_dir / "scores.json").read_text("utf-8"))
    cats = scores["categories"]
    # Identity on fillers: item 1 has two reference edits missed (FN 2); item 2 has one (delete all): FN 1.
    assert (cats["fillers"]["edit"]["tp"], cats["fillers"]["edit"]["fp"], cats["fillers"]["edit"]["fn"]) == (0, 0, 3)
    assert cats["fillers"]["edit"]["precision"] is None  # no output edits at all
    assert cats["fillers"]["edit"]["recall"] == 0.0
    assert cats["fillers"]["word_loss"]["mean"] == 0.0  # identity never loses a word
    assert cats["fillers"]["status"]["unchanged"] == 2
    # Negatives: both are noop items; identity never over-cleans.
    assert cats["negatives"]["over_clean"] == {"mean": 0.0, "se": 0.0, "n": 2}
    assert cats["negatives"]["slot_fail"]["mean"] == 0.0
    # Slices are reported too.
    assert "negatives/negation" in scores["slices"]
    # Only categories with items appear (JSON keys are sorted; the report applies the spec's order).
    assert set(cats) == {"negatives", "spoken-form", "fillers"}

    # --check passes against what was just written, and the output is byte-deterministic.
    before = (run_dir / "scores.json").read_bytes()
    rc = main(["score", str(run_dir), "--items", str(items_dir), "--check", "--bootstrap-resamples", "20"])
    assert rc == 0
    rc = main(["score", str(run_dir), "--items", str(items_dir), "--bootstrap-resamples", "20"])
    assert (run_dir / "scores.json").read_bytes() == before

    # Different bootstrap parameters -> mismatch is reported, not silently accepted.
    rc = main(["score", str(run_dir), "--items", str(items_dir), "--check", "--bootstrap-resamples", "21"])
    assert rc == 1


def test_run_refuses_to_overwrite(tmp_path: Path, items_dir: Path, run_config: Path):
    runs = tmp_path / "runs"
    args = ["run", "--adapter", "identity", "--config", str(run_config)]
    args += ["--items", str(items_dir), "--runs", str(runs), "--date", "2026-10-27"]
    assert main(args) == 0
    assert main(args) == 1


def test_score_refuses_changed_items(tmp_path: Path, items_dir: Path, run_config: Path):
    runs = tmp_path / "runs"
    cfg = json.loads(run_config.read_text("utf-8"))
    run_dir = run(
        adapter_name="identity",
        adapter_config={},
        run_config=cfg,
        items_dir=items_dir,
        runs_dir=runs,
        repo_root=tmp_path,
        date="2026-10-27",
    )
    # Edit an item file after the run: the item hash no longer matches.
    f = items_dir / "fillers.jsonl"
    f.write_text(f.read_text("utf-8").replace("test item", "edited"), "utf-8")
    with pytest.raises(ManifestError, match="items_sha256"):
        score_run(run_dir, items_dir, bootstrap_resamples=5)


def test_score_refuses_missing_manifest_field(tmp_path: Path, items_dir: Path, run_config: Path):
    runs = tmp_path / "runs"
    cfg = json.loads(run_config.read_text("utf-8"))
    run_dir = run(
        adapter_name="identity", adapter_config={}, run_config=cfg, items_dir=items_dir, runs_dir=runs,
        repo_root=tmp_path, date="2026-10-27",
    )
    m = json.loads((run_dir / "run.json").read_text("utf-8"))
    del m["attestation"]
    (run_dir / "run.json").write_text(json.dumps(m), "utf-8")
    with pytest.raises(ManifestError, match="attestation"):
        score_run(run_dir, items_dir, bootstrap_resamples=5)


def test_score_refuses_output_set_mismatch(tmp_path: Path, items_dir: Path, run_config: Path):
    runs = tmp_path / "runs"
    cfg = json.loads(run_config.read_text("utf-8"))
    run_dir = run(
        adapter_name="identity", adapter_config={}, run_config=cfg, items_dir=items_dir, runs_dir=runs,
        repo_root=tmp_path, date="2026-10-27", limit=3,
    )
    with pytest.raises(ManifestError, match="cover exactly"):
        score_run(run_dir, items_dir, bootstrap_resamples=5)


def test_run_config_must_have_attestation(tmp_path: Path, items_dir: Path):
    from cleanupbench.runner import RunConfigError

    with pytest.raises(RunConfigError, match="attestation"):
        run(
            adapter_name="identity",
            adapter_config={},
            run_config={"system_name": "x", "system_org": "y", "organizer_row": False},
            items_dir=items_dir,
            runs_dir=tmp_path / "runs",
            repo_root=tmp_path,
        )


def test_determinism_hash_ignores_latency():
    from cleanupbench.manifest import OutputRecord

    a = OutputRecord("x", "out", "cleaned", None, None, (), 1.0, None)
    b = OutputRecord("x", "out", "cleaned", None, None, (), 99.0, "raw")
    assert determinism_hash([a]) == determinism_hash([b])
    c = OutputRecord("x", "out!", "cleaned", None, None, (), 1.0, None)
    assert determinism_hash([a]) != determinism_hash([c])


def test_human_ceiling_command(items_dir: Path, tmp_path: Path, capsys):
    out = tmp_path / "hc.json"
    rc = main(["human-ceiling", "--items", str(items_dir), "--out", str(out), "--bootstrap-resamples", "10"])
    assert rc == 0
    hc = json.loads(out.read_text("utf-8"))
    assert hc["system"] == "human-ceiling"
    assert hc["items_with_two_references"] == 1
    # Reference 2 ("We sold 25 units.") against reference 1: the "25" edit is an FP, "We" and "." are TP.
    sf = hc["categories"]["spoken-form"]["edit"]
    assert (sf["tp"], sf["fp"], sf["fn"]) == (2, 1, 0)
