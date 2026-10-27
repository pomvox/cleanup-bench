"""`cleanupbench data ...` subcommands: derive-disflqa, gate, review-sheet, agreement, promote."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from cleanupbench.data.disflqa import derive, load_disflqa
from cleanupbench.data.gates import gate_candidates
from cleanupbench.data.review import (
    agreement,
    promote,
    read_drafts,
    read_sheet,
    review_sheet,
    verdicts,
    write_item_file,
)
from cleanupbench.items import item_files, iter_item_file

DEFAULT_DRAFTS = Path("data/drafts")
DEFAULT_DISCARDS = Path("data/discards.jsonl")
DEFAULT_ITEMS = Path("data/items")


def _existing_max_seq(items_dir: Path) -> dict[str, int]:
    """Highest sequence number per `<category>-<slice or core>` prefix across drafts and items."""
    out: dict[str, int] = {}
    if not items_dir.exists():
        return out
    for path in item_files(items_dir):
        for _, obj in iter_item_file(path):
            prefix, _, seq = obj["id"].rpartition("-")
            try:
                out[prefix] = max(out.get(prefix, 0), int(seq))
            except ValueError:
                continue
    return out


def cmd_derive_disflqa(args: argparse.Namespace) -> int:
    try:
        data = load_disflqa(args.source)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    existing = _existing_max_seq(args.items)
    for d in (args.drafts,):
        if d.exists():
            for k, v in _existing_max_seq(d).items():
                existing[k] = max(existing.get(k, 0), v)
    start = {
        "correction-interrogative": existing.get("correction-interrogative-core", 0),
        "correction-intra": existing.get("correction-intra-core", 0),
        "negatives": existing.get("negatives-already-clean", 0),
    }
    released = args.released or dt.date.today().isoformat()
    buckets = derive(data, per_category=args.per_category, seed=args.seed, released=released, start_seq=start)
    args.drafts.mkdir(parents=True, exist_ok=True)
    total = 0
    for cat, objs in buckets.items():
        passing, discarded = gate_candidates(objs, discard_log=args.discards, stage="derive-disflqa")
        path = args.drafts / f"{cat}.jsonl"
        write_item_file(path, passing, append=path.exists())
        print(f"{cat}: {len(passing)} drafts -> {path}; {len(discarded)} discarded -> {args.discards}")
        total += len(passing)
    print(f"{total} candidates written; they are drafts until reviewed and promoted")
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    rc = 0
    for path in args.files:
        cands = read_drafts(path)
        passing, discarded = gate_candidates(cands, discard_log=args.discards, stage=f"gate:{path.name}")
        print(f"{path}: {len(passing)} pass, {len(discarded)} discarded")
        if discarded:
            rc = 1
            for d in discarded:
                print(f"  {d['id']}: {', '.join(d['gates_failed'])}", file=sys.stderr)
    return rc


def cmd_review_sheet(args: argparse.Namespace) -> int:
    drafts = []
    for path in sorted(args.drafts.glob("*.jsonl")):
        drafts.extend(read_drafts(path))
    rows = review_sheet(drafts, reviewer=args.reviewer)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {args.out} ({len(rows)} rows for reviewer {args.reviewer!r})")
    return 0


def cmd_agreement(args: argparse.Namespace) -> int:
    try:
        a = read_sheet(args.sheet_a)
        b = read_sheet(args.sheet_b)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(agreement(a, b), indent=2, sort_keys=True))
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    try:
        sheets = [read_sheet(p) for p in args.sheets]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    accepted = verdicts(sheets)
    drafts = []
    for path in sorted(args.drafts.glob("*.jsonl")):
        drafts.extend(read_drafts(path))
    promoted, discarded = promote(
        drafts, accepted, items_dir=args.items, discard_log=args.discards, released=args.released
    )
    print(f"promoted {len(promoted)} items into {args.items}; discarded {len(discarded)} (logged in {args.discards})")
    print("drafts are not removed automatically; delete the promoted lines from data/drafts/ in the same commit")
    return 0


def register_commands(sub) -> None:  # type: ignore[no-untyped-def]
    p = sub.add_parser("data", help="dataset tooling: derive, gate, review, promote (spec section 7)")
    dsub = p.add_subparsers(dest="data_command", required=True)

    d = dsub.add_parser("derive-disflqa", help="derive draft items from a Disfl-QA JSON split")
    d.add_argument("--source", type=Path, required=True, help="path to Disfl-QA test.json (download it yourself)")
    d.add_argument("--per-category", type=int, required=True, help="candidates per target category")
    d.add_argument("--seed", type=int, required=True, help="shuffle seed, recorded in the dataset card")
    d.add_argument("--released", default=None, help="released date to stamp (default: today)")
    d.add_argument("--drafts", type=Path, default=DEFAULT_DRAFTS)
    d.add_argument("--items", type=Path, default=DEFAULT_ITEMS)
    d.add_argument("--discards", type=Path, default=DEFAULT_DISCARDS)
    d.set_defaults(func=cmd_derive_disflqa)

    g = dsub.add_parser("gate", help="run the generation gates on candidate files; discards are logged")
    g.add_argument("files", type=Path, nargs="+")
    g.add_argument("--discards", type=Path, default=DEFAULT_DISCARDS)
    g.set_defaults(func=cmd_gate)

    r = dsub.add_parser("review-sheet", help="write a blank review sheet for one reviewer over all drafts")
    r.add_argument("--reviewer", required=True)
    r.add_argument("--drafts", type=Path, default=DEFAULT_DRAFTS)
    r.add_argument("--out", type=Path, required=True)
    r.set_defaults(func=cmd_review_sheet)

    a = dsub.add_parser("agreement", help="raw agreement and Cohen's kappa between two review sheets")
    a.add_argument("sheet_a", type=Path)
    a.add_argument("sheet_b", type=Path)
    a.set_defaults(func=cmd_agreement)

    pr = dsub.add_parser("promote", help="append reviewed, accepted drafts to data/items; log the rest")
    pr.add_argument("sheets", type=Path, nargs="+", help="one or more completed review sheets")
    pr.add_argument("--drafts", type=Path, default=DEFAULT_DRAFTS)
    pr.add_argument("--items", type=Path, default=DEFAULT_ITEMS)
    pr.add_argument("--discards", type=Path, default=DEFAULT_DISCARDS)
    pr.add_argument("--released", default=None, help="released date to stamp on promoted items")
    pr.set_defaults(func=cmd_promote)
