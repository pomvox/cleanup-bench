"""Command-line entry points: validate, run, score, report (docs/PROMPT.md Part 3).

- `validate` checks item files and run folders against the schemas.
- `run` runs one adapter over the scorable items twice and writes a run folder.
- `score` recomputes scores.json for a run folder and refuses incomplete rows;
  `--check` compares against the committed scores.json instead of writing.
- `human-ceiling` scores reference 2 against reference 1 (spec section 6.10).
- `report` generates the static leaderboard from runs/ and `--check` compares it with the committed site.
- `compare-rows`, `power` and `data ...` are registered by their own modules.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cleanupbench import BENCH_VERSION, __version__
from cleanupbench.adapters import ADAPTER_NAMES
from cleanupbench.canary import CANARY
from cleanupbench.items import validate_items_dir
from cleanupbench.manifest import ManifestError, check_run_dir
from cleanupbench.scorer.aggregate import DEFAULT_BOOTSTRAP_RESAMPLES, DEFAULT_BOOTSTRAP_SEED
from cleanupbench.scorer.score import human_ceiling, score_run, scores_match, scores_text, write_scores

DEFAULT_ITEMS_DIR = Path("data/items")
DEFAULT_RUNS_DIR = Path("runs")


def _print_errors(errors: list[str]) -> None:
    for err in errors:
        print(err, file=sys.stderr)


def _run_dirs(runs_dir: Path) -> list[Path]:
    return sorted(p.parent for p in runs_dir.glob("*/*/run.json"))


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
        run_dirs = _run_dirs(runs_dir)
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


def cmd_run(args: argparse.Namespace) -> int:
    from cleanupbench.runner import RunConfigError, load_json_file, run

    try:
        adapter_config = load_json_file(args.adapter_config) if args.adapter_config else {}
        run_config = load_json_file(args.config)
        for key, value in (("system_name", args.system), ("system_org", args.org), ("date", args.date)):
            if value is not None:
                run_config[key] = value
        if args.organizer_row:
            run_config["organizer_row"] = True
        run_dir = run(
            adapter_name=args.adapter,
            adapter_config=adapter_config,
            run_config=run_config,
            items_dir=args.items,
            runs_dir=args.runs,
            repo_root=Path.cwd(),
            date=run_config.get("date"),
            passes=1 if args.single_pass else 2,
            limit=args.limit,
            log=lambda s: print(s, file=sys.stderr),
        )
    except (RunConfigError, ManifestError) as exc:
        _print_errors(str(exc).splitlines())
        return 1
    except ValueError as exc:  # adapter configuration errors
        _print_errors([str(exc)])
        return 1
    print(run_dir)
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    rc = 0
    run_dirs = [args.run_dir] if args.run_dir else _run_dirs(args.runs)
    if not run_dirs:
        print(f"no run folders under {args.runs}", file=sys.stderr)
        return 1
    for run_dir in run_dirs:
        try:
            scores = score_run(
                run_dir,
                args.items,
                allow_nondeterministic=args.allow_nondeterministic,
                bootstrap_resamples=args.bootstrap_resamples,
                bootstrap_seed=args.bootstrap_seed,
            )
        except ManifestError as exc:
            _print_errors(str(exc).splitlines())
            rc = 1
            continue
        if args.check:
            ok, msg = scores_match(run_dir, scores)
            print(f"{'ok' if ok else 'MISMATCH'}: {msg}")
            if not ok:
                rc = 1
        else:
            path = write_scores(run_dir, scores)
            print(f"wrote {path}")
    return rc


def cmd_human_ceiling(args: argparse.Namespace) -> int:
    scores = human_ceiling(args.items, bootstrap_resamples=args.bootstrap_resamples, bootstrap_seed=args.bootstrap_seed)
    text = scores_text(scores)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, "utf-8")
        print(f"wrote {args.out}")
    else:
        print(text, end="")
    return 0


def cmd_canary(args: argparse.Namespace) -> int:
    print(CANARY)
    return 0


def _add_bootstrap_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--bootstrap-resamples", type=int, default=DEFAULT_BOOTSTRAP_RESAMPLES)
    p.add_argument("--bootstrap-seed", type=int, default=DEFAULT_BOOTSTRAP_SEED)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cleanupbench", description="Cleanup Bench command line.")
    parser.add_argument("--version", action="version", version=f"cleanupbench {__version__} (bench {BENCH_VERSION})")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="validate item files and run folders against the schemas")
    p_validate.add_argument("--items", type=Path, default=DEFAULT_ITEMS_DIR, help="item directory")
    p_validate.add_argument("--runs", type=Path, default=DEFAULT_RUNS_DIR, help="runs directory (default: runs)")
    p_validate.add_argument("--canary", default=CANARY, help="canary string required in every item file header")
    p_validate.set_defaults(func=cmd_validate)

    p_run = sub.add_parser("run", help="run a system over the items twice and write runs/<system>/<date>/")
    p_run.add_argument("--adapter", required=True, choices=ADAPTER_NAMES)
    p_run.add_argument("--config", type=Path, required=True, help="run config JSON (system, attestation, ...)")
    p_run.add_argument("--adapter-config", type=Path, default=None, help="adapter config JSON")
    p_run.add_argument("--items", type=Path, default=DEFAULT_ITEMS_DIR)
    p_run.add_argument("--runs", type=Path, default=DEFAULT_RUNS_DIR)
    p_run.add_argument("--system", default=None, help="override system_name from the run config")
    p_run.add_argument("--org", default=None, help="override system_org from the run config")
    p_run.add_argument("--date", default=None, help="run folder date (default: today, UTC)")
    p_run.add_argument("--organizer-row", action="store_true", help="mark the row as produced by the maintainer")
    p_run.add_argument("--limit", type=int, default=None, help="only the first N scorable items (pilots, never a row)")
    p_run.add_argument("--single-pass", action="store_true", help="skip pass B (the row will be refused by score)")
    p_run.set_defaults(func=cmd_run)

    p_score = sub.add_parser("score", help="score run folders; refuses an incomplete manifest")
    p_score.add_argument("run_dir", type=Path, nargs="?", default=None, help="one run folder (default: all)")
    p_score.add_argument("--items", type=Path, default=DEFAULT_ITEMS_DIR)
    p_score.add_argument("--runs", type=Path, default=DEFAULT_RUNS_DIR)
    p_score.add_argument("--check", action="store_true", help="compare with the committed scores.json, do not write")
    p_score.add_argument("--allow-nondeterministic", action="store_true", help="score a flagged hosted row (S4)")
    _add_bootstrap_args(p_score)
    p_score.set_defaults(func=cmd_score)

    p_hc = sub.add_parser("human-ceiling", help="score reference 2 against reference 1 (spec section 6.10)")
    p_hc.add_argument("--items", type=Path, default=DEFAULT_ITEMS_DIR)
    p_hc.add_argument("--out", type=Path, default=None, help="write here instead of stdout")
    _add_bootstrap_args(p_hc)
    p_hc.set_defaults(func=cmd_human_ceiling)

    p_canary = sub.add_parser("canary", help="print the bench's canary string")
    p_canary.set_defaults(func=cmd_canary)

    from cleanupbench.compare import register_commands as register_compare
    from cleanupbench.data.cli import register_commands as register_data
    from cleanupbench.power import register_commands as register_power
    from cleanupbench.report import register_commands as register_report

    register_compare(sub)
    register_power(sub)
    register_data(sub)
    register_report(sub)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
