"""CLI smoke tests (phase 1)."""

from __future__ import annotations

import json
from pathlib import Path

from cleanupbench.cli import main


def test_version(capsys):
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    out = capsys.readouterr().out
    assert out.startswith("cleanupbench ")


def test_validate_with_nothing_present(tmp_path: Path, capsys):
    rc = main(["validate", "--items", str(tmp_path / "none"), "--runs", str(tmp_path / "none")])
    assert rc == 0
    out = capsys.readouterr().out
    assert "nothing to validate" in out


def test_validate_reports_item_errors(tmp_path: Path, capsys):
    items = tmp_path / "items"
    items.mkdir()
    (items / "fillers.jsonl").write_text("# canary\n" + json.dumps({"id": "x"}) + "\n", "utf-8")
    rc = main(["validate", "--items", str(items), "--runs", str(tmp_path / "none")])
    assert rc == 1
    err = capsys.readouterr().err
    assert "is a required property" in err


def test_all_commands_registered():
    from cleanupbench.cli import build_parser

    names = set(build_parser()._subparsers._group_actions[0].choices)  # type: ignore[union-attr]
    assert {"validate", "run", "score", "report", "human-ceiling", "canary", "compare-rows", "power", "data"} <= names


def test_canary_command(capsys):
    assert main(["canary"]) == 0
    assert "cleanup-bench canary GUID" in capsys.readouterr().out
