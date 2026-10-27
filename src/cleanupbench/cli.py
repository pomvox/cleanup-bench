"""Command-line entry points: validate, run, score, report (docs/PROMPT.md Part 3).

Phase 1 (scaffold): `validate` checks item files and run folders against the
schemas; `run`, `score` and `report` exist and explain that they are not
implemented yet. Later phases fill them in without changing the interface.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cleanupbench import BENCH_VERSION, __version__
from cleanupbench.items import validate_items_dir
from cleanupbench.manifest import ManifestError, check_run_dir

DEFAULT_ITEMS_DIR = Path("data/items")
DEFAULT_RUNS_DIR = Path("runs")


def _print_errors(errors: list[str]) -> None:
    for err in errors:
        print(err, file=sys.stderr)


def cmd_validate(args: argparse.Namespace) -> int:
    rc = 0
    items_dir: Path = args.items
    if items_dir.exists():
        errors = validate_items_dir(items_dir, require_canary=args.canary)
        if errors:
            _print_errors(errors)
            rc = 1
        else:
            print(f"items: ok ({items_dir})")
    else:
        print(f"items: no directory at {items_dir} (nothing to validate)")
    runs_dir: Path = args.runs
    if runs_dir.exists():
        run_dirs = sorted(p.parent for p in runs_dir.glob("*/*/run.json"))
        for run_dir in run_dirs:
            try:
                check_run_dir(run_dir, allow_nondeterministic=True)
            except ManifestError as exc:
                _print_errors(str(exc).splitlines())
                rc = 1
            else:
                print(f"run: ok ({run_dir})")
        if not run_dirs:
            print(f"runs: no run folders under {runs_dir}")
    else:
        print(f"runs: no directory at {runs_dir} (nothing to validate)")
    return rc


def cmd_not_implemented(name: str):
    def handler(args: argparse.Namespace) -> int:
        print(f"cleanupbench {name}: not implemented in this phase (see docs/spec.md section 13)", file=sys.stderr)
        return 2

    return handler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cleanupbench", description="Cleanup Bench command line.")
    parser.add_argument("--version", action="version", version=f"cleanupbench {__version__} (bench {BENCH_VERSION})")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="validate item files and run folders against the schemas")
    p_validate.add_argument("--items", type=Path, default=DEFAULT_ITEMS_DIR, help="item directory")
    p_validate.add_argument("--runs", type=Path, default=DEFAULT_RUNS_DIR, help="runs directory (default: runs)")
    p_validate.add_argument("--canary", default=None, help="require this canary string in every item file header")
    p_validate.set_defaults(func=cmd_validate)

    p_run = sub.add_parser("run", help="run a system over the items and write a run folder")
    p_run.set_defaults(func=cmd_not_implemented("run"))

    p_score = sub.add_parser("score", help="score a run folder; refuses an incomplete manifest")
    p_score.set_defaults(func=cmd_not_implemented("score"))

    p_report = sub.add_parser("report", help="generate the static leaderboard from runs/")
    p_report.set_defaults(func=cmd_not_implemented("report"))

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
