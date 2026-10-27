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


def test_unimplemented_commands_say_so(capsys):
    rc = main(["report"])
    assert rc == 2
    assert "not implemented" in capsys.readouterr().err


def test_canary_command(capsys):
    assert main(["canary"]) == 0
    assert "cleanup-bench canary GUID" in capsys.readouterr().out
