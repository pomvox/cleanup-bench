"""End to end: `runner.run` with the openai-compatible adapter against the fake server, then `score_run`.

A deterministic fake passes the determinism check and scores; a fake that
alternates its answers fails the check (manifest `identical: false`) and
`score` refuses the row because it is not hosted (decision S4).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import FakeServer, Recorded, item_json, write_items_dir

from cleanupbench.manifest import ManifestError, read_manifest, read_outputs
from cleanupbench.runner import run
from cleanupbench.scorer.score import score_run

CLEANED = {
    "um so let's go": "Let's go.",
    "um uh so yeah": "",
    "never merge a change like this": "Never merge a change like this.",
    "okay": "okay",
    "we sold twenty five units": "We sold 25 units.",
}


@pytest.fixture
def items_dir(tmp_path: Path) -> Path:
    return write_items_dir(
        tmp_path,
        {
            "fillers.jsonl": [
                item_json(
                    "fillers-core-0001", "fillers", "um so let's go", ["Let's go."], must=("go",), must_not=("um",)
                ),
                item_json("fillers-core-0002", "fillers", "um uh so yeah", [""], must_not=("um",)),
            ],
            "negatives.jsonl": [
                item_json(
                    "negatives-negation-0001",
                    "negatives",
                    "never merge a change like this",
                    ["Never merge a change like this."],
                    must=("never",),
                    slice_="negation",
                ),
                item_json(
                    "negatives-fragments-0001", "negatives", "okay", ["Okay"], must=("okay",), slice_="fragments"
                ),
            ],
            "spoken-form.jsonl": [
                item_json(
                    "spoken-form-cardinal-0001",
                    "spoken-form",
                    "we sold twenty five units",
                    ["We sold twenty five units.", "We sold 25 units."],
                    must=("units",),
                    slice_="cardinal",
                ),
            ],
        },
    )


def run_config() -> dict:
    return {
        "system_name": "fake-local",
        "system_org": "test",
        "organizer_row": True,
        "attestation": {"no_training_on_items": True, "known_overlap": "", "declared_exposure": "none"},
        "hardware": {"machine": "test", "os": "test", "accelerator": "none", "ram_gb": None},
    }


def chat(text: str) -> dict:
    return {"choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}]}


def adapter_config(server: FakeServer, tmp_path: Path) -> dict:
    prompt = tmp_path / "generic.txt"
    prompt.write_text("Clean the dictation.\n", "utf-8")
    return {
        "base_url": server.base_url + "/v1",
        "model": "fake",
        "system_prompt_file": str(prompt),
        "extra_body": {"chat_template_kwargs": {"enable_thinking": False}},
        "max_tokens": 64,
    }


def test_deterministic_fake_runs_and_scores(tmp_path: Path, items_dir: Path, fake_server: FakeServer):
    fake_server.responder = lambda req: (200, chat(CLEANED[req.json["messages"][-1]["content"]]))
    run_dir = run(
        adapter_name="openai-compatible",
        adapter_config=adapter_config(fake_server, tmp_path),
        run_config=run_config(),
        items_dir=items_dir,
        runs_dir=tmp_path / "runs",
        repo_root=tmp_path,
        date="2026-10-28",
    )
    assert run_dir == tmp_path / "runs" / "fake-local" / "2026-10-28"
    manifest = read_manifest(run_dir)
    assert manifest["determinism"]["identical"] is True
    assert manifest["hosted"] is False and "nondeterministic" not in manifest
    assert manifest["adapter"]["name"] == "openai-compatible"
    assert manifest["decoding"] == {"strategy": "greedy", "temperature": 0, "max_tokens": 64, "thinking": False}
    assert manifest["prompt"]["text"] == "Clean the dictation.\n"
    assert manifest["adapter"]["config"]["endpoint"] == fake_server.base_url + "/v1/chat/completions"
    assert manifest["run"]["item_count"] == 5
    assert len(fake_server.requests) == 10  # two passes over five items

    records = {r.id: r for r in read_outputs(run_dir / "outputs.jsonl")}
    assert records["fillers-core-0001"].output_text == "Let's go." and records["fillers-core-0001"].outcome == "cleaned"
    assert records["negatives-fragments-0001"].outcome == "unchanged"
    assert records["fillers-core-0002"].output_text == ""
    assert records["fillers-core-0001"].raw is not None and json.loads(records["fillers-core-0001"].raw)["choices"]
    assert records["fillers-core-0001"].latency_ms is not None

    scores = score_run(run_dir, items_dir, bootstrap_resamples=10)
    cats = scores["categories"]
    assert set(cats) == {"fillers", "negatives", "spoken-form"}
    assert cats["fillers"]["word_loss"]["mean"] == 0.0
    assert cats["negatives"]["status"]["unchanged"] == 1
    assert cats["negatives"]["over_clean"]["n"] == 2


def test_alternating_fake_fails_determinism_and_is_refused(tmp_path: Path, items_dir: Path, fake_server: FakeServer):
    counter: dict[str, int] = {}

    def alternate(req: Recorded):
        raw = req.json["messages"][-1]["content"]
        n = counter.get(raw, 0)
        counter[raw] = n + 1
        text = CLEANED[raw] if n % 2 == 0 else CLEANED[raw] + " (again)"
        return 200, chat(text)

    fake_server.responder = alternate
    run_dir = run(
        adapter_name="openai-compatible",
        adapter_config=adapter_config(fake_server, tmp_path),
        run_config=run_config(),
        items_dir=items_dir,
        runs_dir=tmp_path / "runs",
        repo_root=tmp_path,
        date="2026-10-28",
    )
    manifest = read_manifest(run_dir)
    assert manifest["determinism"]["identical"] is False
    assert manifest["determinism"]["run_a_sha256"] != manifest["determinism"]["run_b_sha256"]
    assert manifest["determinism"]["first_divergent_item"] == "fillers-core-0001"
    assert "nondeterministic" not in manifest  # only hosted rows get the flag
    with pytest.raises(ManifestError, match="determinism check failed"):
        score_run(run_dir, items_dir, bootstrap_resamples=10)
    with pytest.raises(ManifestError, match="determinism check failed"):
        score_run(run_dir, items_dir, allow_nondeterministic=True, bootstrap_resamples=10)  # not hosted: still refused


def test_adapter_error_becomes_error_outcome(tmp_path: Path, items_dir: Path, fake_server: FakeServer):
    def flaky(req: Recorded):
        raw = req.json["messages"][-1]["content"]
        if raw == "okay":
            return 500, {"error": "boom"}
        return 200, chat(CLEANED[raw])

    fake_server.responder = flaky
    run_dir = run(
        adapter_name="openai-compatible",
        adapter_config=adapter_config(fake_server, tmp_path),
        run_config=run_config(),
        items_dir=items_dir,
        runs_dir=tmp_path / "runs",
        repo_root=tmp_path,
        date="2026-10-28",
    )
    records = {r.id: r for r in read_outputs(run_dir / "outputs.jsonl")}
    assert records["negatives-fragments-0001"].outcome == "error"
    assert records["negatives-fragments-0001"].warnings[0].startswith("adapter error: HTTP 500")
    assert read_manifest(run_dir)["determinism"]["identical"] is True
