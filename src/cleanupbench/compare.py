"""`compare-rows`: do two run folders agree byte for byte where the first returned `cleaned`?

The SimpleWords v3 rows through the engine and through mlx-lm must agree on
every item where the engine returns `cleaned` (docs/spec.md section 8). A
disagreement is a finding for the engine repository, filed as an issue and
never patched here; `format_issue` drafts that issue.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from cleanupbench.manifest import OUTPUTS_NAME, ManifestError, read_manifest, read_outputs

ISSUE_TABLE_LIMIT = 20


def compare_rows(run_a: Path, run_b: Path) -> dict[str, Any]:
    """Compare run_b's output_text with run_a's on every item where run_a's outcome is `cleaned`."""
    a = read_outputs(run_a / OUTPUTS_NAME)
    b = {r.id: r for r in read_outputs(run_b / OUTPUTS_NAME)}
    compared = agree = 0
    disagree: list[dict[str, str | None]] = []
    a_not_cleaned = 0
    for rec in sorted(a, key=lambda r: r.id):
        if rec.outcome != "cleaned":
            a_not_cleaned += 1
            continue
        compared += 1
        other = b.get(rec.id)
        if other is not None and other.output_text == rec.output_text:
            agree += 1
        else:
            disagree.append({"id": rec.id, "a": rec.output_text, "b": other.output_text if other else None})
    return {"compared": compared, "agree": agree, "disagree": disagree, "a_not_cleaned": a_not_cleaned}


def _revision(run_dir: Path) -> str:
    try:
        m = read_manifest(run_dir)
    except ManifestError:
        return "unknown (manifest unreadable)"
    s = m["system"]
    return f"{s['model_id']} @ {s['model_revision']} (adapter {m['adapter']['name']} v{m['adapter']['version']})"


def _cell(text: str | None) -> str:
    if text is None:
        return "*(no output record)*"
    return "`" + text.replace("`", "\\`").replace("|", "\\|").replace("\n", "\\n") + "`"


def format_issue(result: dict[str, Any], run_a: Path, run_b: Path) -> str:
    """A Markdown issue draft for the engine repository."""
    n = len(result["disagree"])
    rows = result["disagree"][:ISSUE_TABLE_LIMIT]
    lines = [
        f"**Title:** LocalServer and mlx-lm disagree on {n} items",
        "",
        "**Body:**",
        "",
        "Cleanup Bench (pomvox/cleanup-bench, `docs/spec.md` section 8) requires the SimpleWords v3 row",
        "through `Examples/LocalServer` (`POST /v1/clean`, protocol v1) and the row through `mlx-lm`",
        "(`system_v2.txt` in one user turn, `enable_thinking=False`, greedy) to agree byte for byte on",
        "every item where the engine returns `cleaned`. They do not. Per the bench's rule the disagreement",
        "is reported here and not patched in the bench.",
        "",
        f"- Run A (engine): `{run_a.as_posix()}`; model {_revision(run_a)}",
        f"- Run B (mlx-lm): `{run_b.as_posix()}`; model {_revision(run_b)}",
        f"- Items compared (engine `cleaned`): {result['compared']}; agree: {result['agree']}; disagree: {n};",
        f"  engine not `cleaned` (skipped): {result['a_not_cleaned']}",
        "",
        f"First {min(n, ISSUE_TABLE_LIMIT)} disagreements (outputs verbatim, newlines shown as `\\n`):",
        "",
        "| item | engine (A) | mlx-lm (B) |",
        "| --- | --- | --- |",
    ]
    lines.extend(f"| `{d['id']}` | {_cell(d['a'])} | {_cell(d['b'])} |" for d in rows)
    if n > ISSUE_TABLE_LIMIT:
        lines.append("")
        lines.append(f"{n - ISSUE_TABLE_LIMIT} more in the two `outputs.jsonl` files.")
    lines.extend(
        [
            "",
            "Questions for the engine repository: is the difference in the prompt template, the tokenizer,",
            "the sampler, a transform, or the guard? The bench keeps both rows on the board as they are.",
            "",
        ]
    )
    return "\n".join(lines)


def cmd_compare_rows(args: argparse.Namespace) -> int:
    try:
        result = compare_rows(args.run_a, args.run_b)
    except (ManifestError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    n = len(result["disagree"])
    print(
        f"compared {result['compared']} items where {args.run_a} is cleaned: "
        f"{result['agree']} agree, {n} disagree; {result['a_not_cleaned']} skipped (not cleaned in A)"
    )
    for d in result["disagree"][:ISSUE_TABLE_LIMIT]:
        print(f"  {d['id']}: A={d['a']!r} B={d['b']!r}")
    if args.issue_draft:
        if n:
            args.issue_draft.parent.mkdir(parents=True, exist_ok=True)
            args.issue_draft.write_text(format_issue(result, args.run_a, args.run_b), "utf-8")
            print(f"wrote issue draft {args.issue_draft} (file it in the engine repository; do not patch here)")
        else:
            print(f"no disagreement; {args.issue_draft} not written")
    return 0 if n == 0 else 1


def register_commands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser(
        "compare-rows", help="check two run folders agree byte for byte where the first returned cleaned"
    )
    p.add_argument("run_a", type=Path, help="run folder whose cleaned items are compared (the engine row)")
    p.add_argument("run_b", type=Path, help="run folder compared against (the mlx-lm row)")
    p.add_argument("--issue-draft", type=Path, default=None, help="write a Markdown issue draft here on disagreement")
    p.set_defaults(func=cmd_compare_rows)
