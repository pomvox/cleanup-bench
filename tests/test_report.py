"""The static leaderboard (phase 5): deterministic output, board placement, escaping, --check."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pytest

from cleanupbench.canary import CANARY
from cleanupbench.manifest import write_manifest
from cleanupbench.report import (
    NO_RANKING_SENTENCE,
    NULL,
    REPORT_FILES,
    build_report,
    collect_rows,
    comparative_words,
    parse_errata,
    register_commands,
)

REPO = Path(__file__).resolve().parents[1]
ITEMS_DIR = REPO / "data" / "items"
IDENTITY_ROW = REPO / "runs" / "identity" / "2026-10-27"

HOSTED_NAME = "hosted-example"
HOSTED_DISPLAY = "hosted <b>example</b>"
UNSCORED_NAME = "unscored-row"


@pytest.fixture
def runs_dir(tmp_path: Path) -> Path:
    runs = tmp_path / "runs"
    # (a) the committed identity row, as is
    shutil.copytree(IDENTITY_ROW, runs / "identity" / "2026-10-27")
    manifest = json.loads((IDENTITY_ROW / "run.json").read_text("utf-8"))
    scores = json.loads((IDENTITY_ROW / "scores.json").read_text("utf-8"))
    # (b) a synthetic hosted, nondeterministic row reusing the identity scores
    hosted_dir = runs / HOSTED_NAME / "2026-10-28"
    hosted_dir.mkdir(parents=True)
    hosted = json.loads(json.dumps(manifest))
    hosted["system"].update({"name": HOSTED_NAME, "display_name": HOSTED_DISPLAY, "organizer_row": False})
    hosted["system"].pop("weights_sha256")
    hosted["system"]["api_model_id"] = "example-model-2026-10-01"
    hosted["system"]["api_date"] = "2026-10-28"
    hosted["hosted"] = True
    hosted["nondeterministic"] = True
    hosted["determinism"]["identical"] = False
    hosted["determinism"]["run_b_sha256"] = "f" * 64
    hosted["determinism"]["first_divergent_item"] = "fillers-core-0001"
    write_manifest(hosted_dir / "run.json", hosted)
    shutil.copy(IDENTITY_ROW / "outputs.jsonl", hosted_dir / "outputs.jsonl")
    hosted_scores = dict(scores, system=HOSTED_NAME)
    (hosted_dir / "scores.json").write_text(json.dumps(hosted_scores, indent=2, sort_keys=True) + "\n", "utf-8")
    # (c) an unscored row: run.json only
    unscored_dir = runs / UNSCORED_NAME / "2026-10-29"
    unscored_dir.mkdir(parents=True)
    unscored = json.loads(json.dumps(manifest))
    unscored["system"]["name"] = UNSCORED_NAME
    unscored["system"].pop("display_name")
    write_manifest(unscored_dir / "run.json", unscored)
    return runs


@pytest.fixture
def site(runs_dir: Path, tmp_path: Path) -> tuple[Path, dict[str, str]]:
    out = tmp_path / "site"
    files = build_report(runs_dir, ITEMS_DIR, out, errata_path=tmp_path / "ERRATA.md")
    return out, files


def test_collect_rows_sorted_and_unscored(runs_dir: Path):
    rows = collect_rows(runs_dir)
    assert [r.system for r in rows] == [HOSTED_NAME, "identity", UNSCORED_NAME]
    assert [r.scored for r in rows] == [True, True, False]
    assert [r.hosted for r in rows] == [True, False, False]


def test_three_files_written_and_deterministic(runs_dir: Path, tmp_path: Path):
    out = tmp_path / "site"
    first = build_report(runs_dir, ITEMS_DIR, out, errata_path=None)
    assert set(first) == set(REPORT_FILES)
    for name in REPORT_FILES:
        assert (out / name).read_bytes() == first[name].encode("utf-8")
    second = build_report(runs_dir, ITEMS_DIR, out, errata_path=None)
    assert second == first


def test_hosted_row_in_hosted_table_only(site):
    _, files = site
    model = json.loads(files["leaderboard.json"])
    assert [r["system"] for r in model["rows"]] == ["identity"]
    assert [r["system"] for r in model["hosted"]] == [HOSTED_NAME]
    hosted = model["hosted"][0]
    assert hosted["api_model_id"] == "example-model-2026-10-01"
    assert hosted["nondeterministic"] is True
    assert hosted["expiry_flag"] is None
    html = files["index.html"]
    main_board = html[html.index("<h2>Main board</h2>") : html.index("<h2>Hosted table</h2>")]
    hosted_table = html[html.index("<h2>Hosted table</h2>") : html.index("<h2>Human ceiling")]
    assert HOSTED_NAME not in main_board
    assert "hosted &lt;b&gt;example&lt;/b&gt;" in hosted_table
    assert "<th>Nondeterministic</th>" in hosted_table
    assert "<th>Nondeterministic</th>" not in main_board


def test_unscored_row_listed(site):
    _, files = site
    model = json.loads(files["leaderboard.json"])
    assert [u["system"] for u in model["unscored"]] == [UNSCORED_NAME]
    html = files["index.html"]
    unscored = html[html.index("<h2>Unscored run folders</h2>") : html.index("<h2>Retired items</h2>")]
    assert UNSCORED_NAME in unscored
    assert UNSCORED_NAME not in html[: html.index("<h2>Unscored run folders</h2>")]


def test_nulls_render_as_dash(site):
    _, files = site
    # The identity row makes no edits, so F0.5 and precision are null (decision S3).
    model = json.loads(files["leaderboard.json"])
    assert model["rows"][0]["categories"]["fillers"]["edit"]["f0_5"] is None
    assert f"<td>{NULL}</td>" in files["index.html"]
    assert f"| {NULL} |" in files["leaderboard.md"]


def test_canary_and_no_ranking_sentence(site):
    _, files = site
    for name in REPORT_FILES:
        assert CANARY in files[name]
        assert NO_RANKING_SENTENCE in files[name]


def test_html_escapes_manifest_text(site):
    _, files = site
    assert "<b>" not in files["index.html"]
    assert "&lt;b&gt;example&lt;/b&gt;" in files["index.html"]
    assert "<b>" not in files["leaderboard.md"]


def test_no_comparative_words(site):
    _, files = site
    for name in REPORT_FILES:
        assert comparative_words(files[name]) == [], name
    assert comparative_words("the top row beats the rest") == ["top", "beats"]
    assert comparative_words("stop desktop bestiary") == []


def test_human_ceiling_and_latency(site):
    _, files = site
    model = json.loads(files["leaderboard.json"])
    ceiling = model["human_ceiling"]
    assert ceiling["items_with_two_references"] > 0
    assert ceiling["parameters"]["bootstrap_resamples"] == model["rows"][0]["categories"]["fillers"]["edit"][
        "f0_5_bootstrap_95"
    ]["resamples"]
    assert f"<h2>Human ceiling ({ceiling['items_with_two_references']} items with two references)</h2>" in (
        files["index.html"]
    )
    assert [lat["system"] for lat in model["latency"]] == [HOSTED_NAME, "identity"]
    assert model["latency"][1]["machine"] == "Abhis-MacBook-Pro.local (Apple M1)"


def test_html_is_self_contained(site):
    _, files = site
    html = files["index.html"]
    assert "<script" not in html
    assert "http://" not in html and "https://" not in html
    assert '<meta name="viewport"' in html


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    register_commands(parser.add_subparsers(dest="command", required=True))
    return parser


def test_check_command(runs_dir: Path, tmp_path: Path, capsys):
    out = tmp_path / "site"
    errata = tmp_path / "ERRATA.md"
    base = ["--runs", str(runs_dir), "--items", str(ITEMS_DIR), "--out", str(out), "--errata", str(errata)]
    parser = _parser()
    args = parser.parse_args(["report", *base])
    assert args.func(args) == 0
    assert sorted(p.name for p in out.iterdir()) == sorted(REPORT_FILES)
    args = parser.parse_args(["report", *base, "--check"])
    assert args.func(args) == 0
    assert capsys.readouterr().out.count("ok: ") == len(REPORT_FILES)
    (out / "index.html").write_text((out / "index.html").read_text("utf-8") + "<!-- edited -->\n", "utf-8")
    args = parser.parse_args(["report", *base, "--check"])
    assert args.func(args) == 1
    output = capsys.readouterr().out
    assert "MISMATCH: " in output and output.count("ok: ") == len(REPORT_FILES) - 1


def test_check_fails_on_missing_site(runs_dir: Path, tmp_path: Path):
    parser = _parser()
    args = parser.parse_args(
        ["report", "--runs", str(runs_dir), "--items", str(ITEMS_DIR), "--out", str(tmp_path / "none"), "--check"]
    )
    assert args.func(args) == 1


ERRATA_TEXT = """# Errata

Some prose with | a pipe that is not a table.

| id | retired_in | date | issue | reason |
| --- | --- | --- | --- | --- |
| fillers-core-0003 | 1.1.0 | 2026-11-02 | https://example.invalid/issues/7 | reference dropped a content word (law 1) |
| restarts-core-0001 | 1.1.0 | 2026-11-05 | https://example.invalid/issues/9 | two references disagree on the restart |
"""


def test_parse_errata_two_rows():
    rows = parse_errata(ERRATA_TEXT)
    assert rows == [
        {
            "id": "fillers-core-0003",
            "retired_in": "1.1.0",
            "date": "2026-11-02",
            "issue": "https://example.invalid/issues/7",
            "reason": "reference dropped a content word (law 1)",
        },
        {
            "id": "restarts-core-0001",
            "retired_in": "1.1.0",
            "date": "2026-11-05",
            "issue": "https://example.invalid/issues/9",
            "reason": "two references disagree on the restart",
        },
    ]
    assert parse_errata((REPO / "ERRATA.md").read_text("utf-8")) == []


def test_retired_items_section(runs_dir: Path, tmp_path: Path):
    errata = tmp_path / "ERRATA.md"
    errata.write_text(ERRATA_TEXT, "utf-8")
    files = build_report(runs_dir, ITEMS_DIR, tmp_path / "site", errata_path=errata)
    model = json.loads(files["leaderboard.json"])
    assert [r["id"] for r in model["retired_items"]] == ["fillers-core-0003", "restarts-core-0001"]
    assert "<td>fillers-core-0003</td>" in files["index.html"]
    assert "| restarts-core-0001 | 1.1.0 |" in files["leaderboard.md"]
    without = build_report(runs_dir, ITEMS_DIR, tmp_path / "site2", errata_path=tmp_path / "missing.md")
    assert "<h2>Retired items</h2>\n<p>none</p>" in without["index.html"]
