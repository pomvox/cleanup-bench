"""The static leaderboard (docs/spec.md section 10).

`cleanupbench report` reads every committed run folder under `runs/`, the
human-ceiling row from the item files and the retired-items log from
`ERRATA.md`, and writes three files: `leaderboard.json` (machine-readable),
`leaderboard.md` (Markdown tables) and `index.html` (one self-contained page:
inline CSS, no scripts, no external resources). Output is byte-deterministic
for the same inputs; CI regenerates it and fails on a difference.

There is no overall score and no ranking. Rows are sorted by system name and
then by run date, and the generated text never compares rows.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cleanupbench import BENCH_VERSION
from cleanupbench.canary import CANARY
from cleanupbench.items import CATEGORY_ORDER
from cleanupbench.manifest import MANIFEST_NAME, SCORES_NAME, read_manifest
from cleanupbench.scorer.aggregate import DEFAULT_BOOTSTRAP_SEED
from cleanupbench.scorer.score import human_ceiling

REPORT_FILES: tuple[str, ...] = ("leaderboard.json", "leaderboard.md", "index.html")
NULL = "—"
"""How a null metric is printed (an em dash)."""

NO_RANKING_SENTENCE = "There is no overall score and no ranking; rows are listed alphabetically by system name."
"""Printed verbatim in the footer (GOVERNANCE.md, conflict-of-interest rule 6)."""

FORBIDDEN_WORDS: tuple[str, ...] = ("better", "beats", "best", "top", "wins")
"""Comparative words that must not appear in generated text."""

_FORBIDDEN_RE = re.compile(r"\b(" + "|".join(FORBIDDEN_WORDS) + r")\b", re.IGNORECASE)

ERRATA_COLUMNS: tuple[str, ...] = ("id", "retired_in", "date", "issue", "reason")

ROW_COLUMNS: tuple[tuple[str, str], ...] = (
    ("display_name", "System"),
    ("org", "Org"),
    ("organizer_row", "Organizer row"),
    ("adapter", "Adapter"),
    ("open_weights", "Open weights"),
    ("license", "License"),
    ("gated_download", "Gated download"),
    ("checked", "Checked"),
    ("declared_exposure", "Declared exposure"),
    ("date", "Run date"),
    ("link", "Run folder"),
)
HOSTED_COLUMNS: tuple[tuple[str, str], ...] = ROW_COLUMNS + (
    ("api_model_id", "API model id"),
    ("api_date", "API date"),
    ("expiry_flag", "Expiry flag"),
    ("nondeterministic", "Nondeterministic"),
)
METRIC_COLUMNS: tuple[str, ...] = (
    "F0.5 [95% bootstrap]",
    "P",
    "R",
    "Exact match",
    "Word loss",
    "Insertion",
    "Slot fail",
    "Over-clean",
    "Fallback",
    "Unchanged",
    "Empty",
    "Invalid",
    "n",
)
CEILING_COLUMNS: tuple[str, ...] = (
    "Category",
    "n",
    "F0.5 [95% bootstrap]",
    "P",
    "R",
    "Exact match",
    "Word loss",
    "Insertion",
)
LATENCY_COLUMNS: tuple[str, ...] = ("System", "Run date", "p50 ms", "p95 ms", "n", "Machine", "Accelerator")


@dataclass(frozen=True, slots=True)
class Row:
    """One `runs/<system>/<date>/` folder. `scores` is None when scores.json is absent (an unscored row)."""

    system: str
    date: str
    run_dir: Path
    manifest: dict[str, Any]
    scores: dict[str, Any] | None

    @property
    def scored(self) -> bool:
        return self.scores is not None

    @property
    def hosted(self) -> bool:
        return bool(self.manifest.get("hosted"))


def collect_rows(runs_dir: Path) -> list[Row]:
    """Every `runs/<system>/<date>/` folder with a run.json, sorted by system name then date.

    Folders with run.json and scores.json are board rows; folders with run.json
    only are returned with `scores=None` and listed as unscored.
    """
    rows: list[Row] = []
    if not runs_dir.is_dir():
        return rows
    for manifest_path in runs_dir.glob(f"*/*/{MANIFEST_NAME}"):
        run_dir = manifest_path.parent
        manifest = read_manifest(run_dir)
        scores_path = run_dir / SCORES_NAME
        scores = json.loads(scores_path.read_text("utf-8")) if scores_path.is_file() else None
        rows.append(
            Row(system=manifest["system"]["name"], date=run_dir.name, run_dir=run_dir, manifest=manifest, scores=scores)
        )
    rows.sort(key=lambda r: (r.system, r.date, r.run_dir.parent.name))
    return rows


# --- ERRATA.md ---------------------------------------------------------------


def parse_errata(text: str) -> list[dict[str, str]]:
    """The rows of the Markdown table in ERRATA.md (`| id | retired_in | date | issue | reason |`)."""
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        if header is None:
            header = [c.lower() for c in cells]
            continue
        record = dict(zip(header, cells, strict=False))
        rows.append({col: record.get(col, "") for col in ERRATA_COLUMNS})
    return rows


def read_errata(errata_path: Path | None) -> list[dict[str, str]]:
    if errata_path is None or not errata_path.is_file():
        return []
    return parse_errata(errata_path.read_text("utf-8"))


# --- The model (leaderboard.json) ---------------------------------------------


def _relative_link(out_dir: Path, target: Path) -> str:
    try:
        return Path(os.path.relpath(target, out_dir)).as_posix()
    except ValueError:  # different drives
        return target.as_posix()


def _row_record(row: Row, out_dir: Path) -> dict[str, Any]:
    m = row.manifest
    system = m["system"]
    adapter = m["adapter"]
    expiry = m.get("hosted_expiry_flag")
    return {
        "system": system["name"],
        "display_name": system.get("display_name") or system["name"],
        "org": system["org"],
        "organizer_row": bool(system["organizer_row"]),
        "adapter": f"{adapter['name']}@{adapter['version']}",
        "open_weights": bool(system["open_weights"]),
        "license": system["license"],
        "gated_download": bool(system.get("gated_download", False)),
        "checked_by": m.get("checked_by"),
        "checked_date": m.get("checked_date"),
        "declared_exposure": m["attestation"]["declared_exposure"],
        "date": row.date,
        "link": _relative_link(out_dir, row.run_dir),
        "hosted": row.hosted,
        "api_model_id": system.get("api_model_id"),
        "api_date": system.get("api_date"),
        "expiry_flag": expiry,
        "nondeterministic": bool(m.get("nondeterministic", False)),
        "items_sha256": m["items_sha256"],
        "categories": dict(row.scores.get("categories", {})) if row.scores else {},
    }


def _latency_record(row: Row) -> dict[str, Any]:
    assert row.scores is not None
    lat = row.scores.get("latency") or {}
    hw = row.manifest["hardware"]
    return {
        "system": row.system,
        "display_name": row.manifest["system"].get("display_name") or row.system,
        "date": row.date,
        "p50": lat.get("p50"),
        "p95": lat.get("p95"),
        "n": lat.get("n", 0),
        "machine": hw["machine"],
        "accelerator": hw["accelerator"],
    }


def build_model(
    rows: Iterable[Row], items_dir: Path, out_dir: Path, *, retired: list[dict[str, str]], repo_root: Path
) -> dict[str, Any]:
    rows = list(rows)
    scored = [r for r in rows if r.scored]
    if scored:
        params = scored[0].scores.get("parameters", {})  # type: ignore[union-attr]
        resamples = int(params.get("bootstrap_resamples", 0))
        seed = int(params.get("bootstrap_seed", DEFAULT_BOOTSTRAP_SEED))
    else:
        resamples, seed = 0, DEFAULT_BOOTSTRAP_SEED
    ceiling = human_ceiling(items_dir, bootstrap_resamples=resamples, bootstrap_seed=seed)
    return {
        "schema_version": 1,
        "bench_version": BENCH_VERSION,
        "items_sha256": sorted({r.manifest["items_sha256"] for r in scored}),
        "categories": list(CATEGORY_ORDER),
        "rows": [_row_record(r, out_dir) for r in scored if not r.hosted],
        "hosted": [_row_record(r, out_dir) for r in scored if r.hosted],
        "unscored": [
            {"system": r.system, "date": r.date, "link": _relative_link(out_dir, r.run_dir)}
            for r in rows
            if not r.scored
        ],
        "human_ceiling": {
            "items_sha256": ceiling["items_sha256"],
            "items_with_two_references": ceiling["items_with_two_references"],
            "parameters": ceiling["parameters"],
            "categories": ceiling["categories"],
        },
        "latency": [_latency_record(r) for r in scored],
        "retired_items": retired,
        "links": {
            "governance": _relative_link(out_dir, repo_root / "GOVERNANCE.md"),
            "submitting": _relative_link(out_dir, repo_root / "SUBMITTING.md"),
        },
        "no_ranking": NO_RANKING_SENTENCE,
        "canary": CANARY,
    }


# --- Cell formatting ------------------------------------------------------------


def _num(x: float | int | None, digits: int = 3) -> str:
    if x is None:
        return NULL
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, int):
        return str(x)
    return f"{x:.{digits}f}"


def _mean_se(block: dict[str, Any] | None) -> str:
    if not block or block.get("mean") is None:
        return NULL
    se = block.get("se")
    return _num(block["mean"]) if se is None else f"{_num(block['mean'])} ±{_num(se)}"


def _f_interval(edit: dict[str, Any] | None) -> str:
    if not edit or edit.get("f0_5") is None:
        return NULL
    boot = edit.get("f0_5_bootstrap_95") or {}
    low, high = boot.get("low"), boot.get("high")
    if low is None or high is None:
        return _num(edit["f0_5"])
    return f"{_num(edit['f0_5'])} [{_num(low)}, {_num(high)}]"


def _over_clean(block: dict[str, Any] | None) -> str:
    if not block or not block.get("n"):
        return NULL
    return f"{_mean_se(block)} (n={block['n']})"


def metric_cells(cat: dict[str, Any] | None) -> list[str]:
    """The METRIC_COLUMNS cells for one category aggregate (all nulls when the row lacks the category)."""
    if not cat:
        return [NULL] * len(METRIC_COLUMNS)
    edit = cat.get("edit") or {}
    status = cat.get("status") or {}
    return [
        _f_interval(edit),
        _num(edit.get("precision")),
        _num(edit.get("recall")),
        _mean_se(cat.get("exact_match")),
        _mean_se(cat.get("word_loss")),
        _mean_se(cat.get("insertion")),
        _mean_se(cat.get("slot_fail")),
        _over_clean(cat.get("over_clean")),
        _num(status.get("fallback")),
        _num(status.get("unchanged")),
        _num(status.get("empty")),
        _num(status.get("invalid")),
        _num(cat.get("n")),
    ]


def _yes_no(flag: bool) -> str:
    return "yes" if flag else "no"


def _checked(rec: dict[str, Any]) -> str:
    if rec.get("checked_by"):
        return f"checked by {rec['checked_by']} ({rec.get('checked_date') or NULL})"
    return "unchecked"


def _expiry(flag: dict[str, Any] | None) -> str:
    if not flag:
        return "no"
    note = flag.get("note") or ""
    return f"withdrawn {flag.get('withdrawn_on', NULL)}" + (f": {note}" if note else "")


def row_cells(rec: dict[str, Any], columns: tuple[tuple[str, str], ...]) -> list[tuple[str, str | None]]:
    """(text, href) per column of ROW_COLUMNS or HOSTED_COLUMNS."""
    cells: list[tuple[str, str | None]] = []
    for key, _ in columns:
        if key == "organizer_row":
            cells.append(("organizer" if rec["organizer_row"] else "no", None))
        elif key in ("open_weights", "gated_download", "nondeterministic"):
            cells.append((_yes_no(rec[key]), None))
        elif key == "checked":
            cells.append((_checked(rec), None))
        elif key == "link":
            cells.append((rec["link"], rec["link"]))
        elif key == "expiry_flag":
            cells.append((_expiry(rec["expiry_flag"]), None))
        else:
            value = rec.get(key)
            cells.append((NULL if value is None else str(value), None))
    return cells


def _ceiling_rows(ceiling: dict[str, Any]) -> list[list[str]]:
    rows = []
    for cat in CATEGORY_ORDER:
        block = ceiling["categories"].get(cat)
        if not block:
            continue
        edit = block.get("edit") or {}
        rows.append(
            [
                cat,
                _num(block.get("n")),
                _f_interval(edit),
                _num(edit.get("precision")),
                _num(edit.get("recall")),
                _mean_se(block.get("exact_match")),
                _mean_se(block.get("word_loss")),
                _mean_se(block.get("insertion")),
            ]
        )
    return rows


def _latency_rows(model: dict[str, Any]) -> list[list[str]]:
    return [
        [
            rec["display_name"],
            rec["date"],
            _num(rec["p50"], 1),
            _num(rec["p95"], 1),
            _num(rec["n"]),
            rec["machine"],
            rec["accelerator"],
        ]
        for rec in model["latency"]
    ]


# --- Markdown ------------------------------------------------------------------


def _md_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")


def _md_table(headers: Iterable[str], rows: Iterable[Iterable[str]]) -> list[str]:
    headers = list(headers)
    lines = ["| " + " | ".join(_md_escape(h) for h in headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(_md_escape(c) for c in row) + " |")
    lines.append("")
    return lines


def _md_row_table(records: list[dict[str, Any]], columns: tuple[tuple[str, str], ...]) -> list[str]:
    body = []
    for rec in records:
        cells = []
        for text, href in row_cells(rec, columns):
            cells.append(f"[{_md_escape(text)}]({href})" if href else _md_escape(text))
        body.append("| " + " | ".join(cells) + " |")
    headers = [label for _, label in columns]
    return ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |", *body, ""]


def _md_board(records: list[dict[str, Any]], columns: tuple[tuple[str, str], ...]) -> list[str]:
    if not records:
        return ["No rows.", ""]
    lines = ["### Rows", ""]
    lines += _md_row_table(records, columns)
    for cat in CATEGORY_ORDER:
        lines += [f"### {cat}", ""]
        lines += _md_table(
            ("System", *METRIC_COLUMNS),
            ([rec["display_name"], *metric_cells(rec["categories"].get(cat))] for rec in records),
        )
    return lines


def render_markdown(model: dict[str, Any]) -> str:
    lines = [
        "# Cleanup Bench leaderboard",
        "",
        f"Bench version {model['bench_version']}. Item file hash(es): "
        + (", ".join(f"`{h}`" for h in model["items_sha256"]) or "none")
        + ".",
        "",
        NO_RANKING_SENTENCE,
        "",
        "## Main board",
        "",
        *_md_board(model["rows"], ROW_COLUMNS),
        "## Hosted table",
        "",
        *_md_board(model["hosted"], HOSTED_COLUMNS),
        f"## Human ceiling ({model['human_ceiling']['items_with_two_references']} items with two references)",
        "",
        "Reference 2 scored against reference 1. It bounds the other rows; it is not a system.",
        "",
    ]
    ceiling_rows = _ceiling_rows(model["human_ceiling"])
    lines += _md_table(CEILING_COLUMNS, ceiling_rows) if ceiling_rows else ["No items with two references.", ""]
    lines += ["## Latency", ""]
    lines += _md_table(LATENCY_COLUMNS, _latency_rows(model)) if model["latency"] else ["No rows.", ""]
    lines += ["## Unscored run folders", ""]
    if model["unscored"]:
        lines += [f"- {_md_escape(u['system'])} {u['date']}: [{u['link']}]({u['link']})" for u in model["unscored"]]
        lines.append("")
    else:
        lines += ["none", ""]
    lines += ["## Retired items", ""]
    if model["retired_items"]:
        lines += _md_table(ERRATA_COLUMNS, ([r[c] for c in ERRATA_COLUMNS] for r in model["retired_items"]))
    else:
        lines += ["none", ""]
    lines += [
        "## About",
        "",
        f"Bench version {model['bench_version']}. "
        f"[Governance]({model['links']['governance']}) and [how to submit]({model['links']['submitting']}).",
        "",
        NO_RANKING_SENTENCE,
        "",
        model["canary"],
        "",
    ]
    return "\n".join(lines)


# --- HTML ---------------------------------------------------------------------

_CSS = """
:root { color-scheme: light dark; }
body { max-width: 80rem; margin: 0 auto; padding: 1rem; font-family: system-ui, sans-serif; line-height: 1.4; }
h1, h2, h3 { line-height: 1.2; }
h3 { margin: 1.5rem 0 0.5rem; }
.scroll { overflow-x: auto; max-width: 100%; }
table { border-collapse: collapse; font-size: 0.9rem; }
th, td { border-bottom: 1px solid #8884; padding: 0.3rem 0.6rem; text-align: left; white-space: nowrap; }
th { font-weight: 600; }
footer { margin: 2rem 0 0; padding: 1rem 0 0; border-bottom: 0; font-size: 0.85rem; word-break: break-all; }
"""


def _h(text: str) -> str:
    return html.escape(str(text), quote=True)


def _html_table(headers: Iterable[str], rows: Iterable[Iterable[tuple[str, str | None]]]) -> list[str]:
    head = "".join(f"<th>{_h(h)}</th>" for h in headers)
    lines = ['<div class="scroll"><table>', f"<thead><tr>{head}</tr></thead>", "<tbody>"]
    for row in rows:
        cells = []
        for text, href in row:
            cells.append(f'<td><a href="{_h(href)}">{_h(text)}</a></td>' if href else f"<td>{_h(text)}</td>")
        lines.append("<tr>" + "".join(cells) + "</tr>")
    lines += ["</tbody></table></div>"]
    return lines


def _plain(cells: Iterable[str]) -> list[tuple[str, str | None]]:
    return [(c, None) for c in cells]


def _html_board(records: list[dict[str, Any]], columns: tuple[tuple[str, str], ...]) -> list[str]:
    if not records:
        return ["<p>No rows.</p>"]
    lines = ["<h3>Rows</h3>"]
    lines += _html_table([label for _, label in columns], (row_cells(rec, columns) for rec in records))
    for cat in CATEGORY_ORDER:
        lines.append(f"<h3>{_h(cat)}</h3>")
        lines += _html_table(
            ("System", *METRIC_COLUMNS),
            (_plain([rec["display_name"], *metric_cells(rec["categories"].get(cat))]) for rec in records),
        )
    return lines


def render_html(model: dict[str, Any]) -> str:
    hashes = ", ".join(f"<code>{_h(h)}</code>" for h in model["items_sha256"]) or "none"
    n_two = model["human_ceiling"]["items_with_two_references"]
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Cleanup Bench leaderboard</title>",
        f"<style>{_CSS}</style>",
        "</head>",
        "<body>",
        "<h1>Cleanup Bench leaderboard</h1>",
        f"<p>Bench version {_h(model['bench_version'])}. Item file hash(es): {hashes}.</p>",
        f"<p>{_h(NO_RANKING_SENTENCE)}</p>",
        "<h2>Main board</h2>",
        *_html_board(model["rows"], ROW_COLUMNS),
        "<h2>Hosted table</h2>",
        *_html_board(model["hosted"], HOSTED_COLUMNS),
        f"<h2>Human ceiling ({n_two} items with two references)</h2>",
        "<p>Reference 2 scored against reference 1. It bounds the other rows; it is not a system.</p>",
    ]
    ceiling_rows = _ceiling_rows(model["human_ceiling"])
    if ceiling_rows:
        lines += _html_table(CEILING_COLUMNS, (_plain(r) for r in ceiling_rows))
    else:
        lines.append("<p>No items with two references.</p>")
    lines.append("<h2>Latency</h2>")
    if model["latency"]:
        lines += _html_table(LATENCY_COLUMNS, (_plain(r) for r in _latency_rows(model)))
    else:
        lines.append("<p>No rows.</p>")
    lines.append("<h2>Unscored run folders</h2>")
    if model["unscored"]:
        lines.append("<ul>")
        lines += [
            f'<li>{_h(u["system"])} {_h(u["date"])}: <a href="{_h(u["link"])}">{_h(u["link"])}</a></li>'
            for u in model["unscored"]
        ]
        lines.append("</ul>")
    else:
        lines.append("<p>none</p>")
    lines.append("<h2>Retired items</h2>")
    if model["retired_items"]:
        lines += _html_table(ERRATA_COLUMNS, (_plain(r[c] for c in ERRATA_COLUMNS) for r in model["retired_items"]))
    else:
        lines.append("<p>none</p>")
    lines += [
        "<footer>",
        f"<p>Bench version {_h(model['bench_version'])}. "
        f'<a href="{_h(model["links"]["governance"])}">Governance</a> and '
        f'<a href="{_h(model["links"]["submitting"])}">how to submit</a>.</p>',
        f"<p>{_h(NO_RANKING_SENTENCE)}</p>",
        f"<p>{_h(model['canary'])}</p>",
        "</footer>",
        "</body>",
        "</html>",
        "",
    ]
    return "\n".join(lines)


# --- Entry points -------------------------------------------------------------


def comparative_words(text: str) -> list[str]:
    """The forbidden comparative words found in `text`, lower-cased, in order of appearance."""
    return [m.group(1).lower() for m in _FORBIDDEN_RE.finditer(text)]


def render_report(runs_dir: Path, items_dir: Path, out_dir: Path, *, errata_path: Path | None) -> dict[str, str]:
    """Build the three site files in memory: {filename: content}."""
    model = build_model(
        collect_rows(runs_dir), items_dir, out_dir, retired=read_errata(errata_path), repo_root=runs_dir.parent
    )
    return {
        "leaderboard.json": json.dumps(model, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        "leaderboard.md": render_markdown(model),
        "index.html": render_html(model),
    }


def build_report(runs_dir: Path, items_dir: Path, out_dir: Path, *, errata_path: Path | None) -> dict[str, str]:
    """Build the site and write it into `out_dir`. Returns {filename: content}."""
    files = render_report(runs_dir, items_dir, out_dir, errata_path=errata_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (out_dir / name).write_text(content, "utf-8", newline="\n")
    return files


def check_report(runs_dir: Path, items_dir: Path, out_dir: Path, *, errata_path: Path | None) -> list[tuple[str, bool]]:
    """Rebuild in memory and compare byte for byte with the files in `out_dir`: [(filename, matches)]."""
    files = render_report(runs_dir, items_dir, out_dir, errata_path=errata_path)
    results = []
    for name, content in files.items():
        path = out_dir / name
        results.append((name, path.is_file() and path.read_bytes() == content.encode("utf-8")))
    return results


def cmd_report(args: argparse.Namespace) -> int:
    if args.check:
        rc = 0
        for name, ok in check_report(args.runs, args.items, args.out, errata_path=args.errata):
            print(f"{'ok' if ok else 'MISMATCH'}: {args.out / name}")
            if not ok:
                rc = 1
        return rc
    for name in build_report(args.runs, args.items, args.out, errata_path=args.errata):
        print(f"wrote {args.out / name}")
    return 0


def register_commands(sub: argparse._SubParsersAction) -> None:
    """Add `report [--runs runs] [--items data/items] [--out site] [--errata ERRATA.md] [--check]`."""
    p = sub.add_parser("report", help="generate the static leaderboard from runs/ (or --check the committed one)")
    p.add_argument("--runs", type=Path, default=Path("runs"), help="runs directory (default: runs)")
    p.add_argument("--items", type=Path, default=Path("data/items"), help="item directory (default: data/items)")
    p.add_argument("--out", type=Path, default=Path("site"), help="site directory (default: site)")
    p.add_argument("--errata", type=Path, default=Path("ERRATA.md"), help="retired-items log (default: ERRATA.md)")
    p.add_argument("--check", action="store_true", help="compare with the committed site byte for byte, do not write")
    p.set_defaults(func=cmd_report)
