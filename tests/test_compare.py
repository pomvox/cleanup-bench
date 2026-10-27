"""`compare-rows`: byte-for-byte agreement where run A returned cleaned, and the issue draft."""

from __future__ import annotations

import argparse
from pathlib import Path

from cleanupbench.compare import compare_rows, format_issue, register_commands
from cleanupbench.manifest import OUTPUTS_NAME, OutputRecord, write_outputs


def rec(id_: str, text: str, outcome: str = "cleaned") -> OutputRecord:
    return OutputRecord(id_, text, outcome, None, None, (), 1.0, None)


def make_runs(tmp_path: Path) -> tuple[Path, Path]:
    a = tmp_path / "runs" / "engine" / "2026-10-28"
    b = tmp_path / "runs" / "mlx" / "2026-10-28"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    write_outputs(
        a / OUTPUTS_NAME,
        [
            rec("fillers-core-0001", "Let's go."),
            rec("fillers-core-0002", "Same."),
            rec("negatives-core-0001", "okay", "unchanged"),
            rec("restarts-core-0001", "we should go", "fallback"),
            rec("restarts-core-0002", "Only in A."),
        ],
    )
    write_outputs(
        b / OUTPUTS_NAME,
        [
            rec("fillers-core-0001", "Let's go"),  # differs by a period
            rec("fillers-core-0002", "Same."),
            rec("negatives-core-0001", "Okay"),  # A was unchanged: not compared
            rec("restarts-core-0001", "We should go."),  # A was fallback: not compared
        ],
    )
    return a, b


def test_compare_rows(tmp_path: Path):
    a, b = make_runs(tmp_path)
    result = compare_rows(a, b)
    assert result["compared"] == 3 and result["agree"] == 1 and result["a_not_cleaned"] == 2
    assert result["disagree"] == [
        {"id": "fillers-core-0001", "a": "Let's go.", "b": "Let's go"},
        {"id": "restarts-core-0002", "a": "Only in A.", "b": None},
    ]


def test_compare_rows_all_agree(tmp_path: Path):
    a, b = make_runs(tmp_path)
    write_outputs(b / OUTPUTS_NAME, [rec("fillers-core-0001", "Let's go."), rec("fillers-core-0002", "Same.")])
    write_outputs(a / OUTPUTS_NAME, [rec("fillers-core-0001", "Let's go."), rec("fillers-core-0002", "Same.")])
    assert compare_rows(a, b) == {"compared": 2, "agree": 2, "disagree": [], "a_not_cleaned": 0}


def test_issue_draft(tmp_path: Path):
    a, b = make_runs(tmp_path)
    text = format_issue(compare_rows(a, b), a, b)
    assert text.startswith("**Title:** LocalServer and mlx-lm disagree on 2 items")
    assert a.as_posix() in text and b.as_posix() in text
    assert "| `fillers-core-0001` | `Let's go.` | `Let's go` |" in text
    assert "*(no output record)*" in text
    assert "unknown (manifest unreadable)" in text  # no run.json in the fixture; the draft says so


def test_cli_subcommand(tmp_path: Path, capsys):
    a, b = make_runs(tmp_path)
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    register_commands(sub)
    draft = tmp_path / "issue.md"
    args = parser.parse_args(["compare-rows", str(a), str(b), "--issue-draft", str(draft)])
    assert args.func(args) == 1
    out = capsys.readouterr().out
    assert "1 agree, 2 disagree" in out and "2 skipped" in out
    assert draft.is_file() and "disagree on 2 items" in draft.read_text("utf-8")

    write_outputs(b / OUTPUTS_NAME, [rec("fillers-core-0001", "Let's go."), rec("fillers-core-0002", "Same.")])
    write_outputs(a / OUTPUTS_NAME, [rec("fillers-core-0001", "Let's go."), rec("fillers-core-0002", "Same.")])
    draft2 = tmp_path / "issue2.md"
    args = parser.parse_args(["compare-rows", str(a), str(b), "--issue-draft", str(draft2)])
    assert args.func(args) == 0
    assert not draft2.exists()
    assert "not written" in capsys.readouterr().out
