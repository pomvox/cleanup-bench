"""The `run` command: two passes over the items, a manifest, an outputs file (docs/spec.md section 9).

The determinism hash covers (id, output_text, outcome, fallback_reason,
edits) and nothing else, so latency never breaks it. The stored outputs are
pass A's; pass B exists only to prove the hash. `outputs_sha256` is the hash
of the stored file and ties scores.json to it.
"""

from __future__ import annotations

import datetime as dt
import json
import platform
import subprocess
import sys
from collections.abc import Callable, Sequence
from importlib import metadata
from pathlib import Path
from typing import Any

from cleanupbench import BENCH_VERSION, __version__
from cleanupbench.adapters import Adapter, make_adapter
from cleanupbench.adapters.base import AdapterError, CleanOutput
from cleanupbench.hashing import sha256_file, sha256_json, sha256_text
from cleanupbench.items import Item, items_sha256, load_items, scorable
from cleanupbench.manifest import MANIFEST_NAME, OUTPUTS_NAME, OutputRecord, write_manifest, write_outputs


class RunConfigError(ValueError):
    pass


REQUIRED_RUN_CONFIG = ("system_name", "system_org", "organizer_row", "attestation")


def determinism_hash(records: Sequence[OutputRecord]) -> str:
    payload = [
        {
            "id": r.id,
            "output_text": r.output_text,
            "outcome": r.outcome,
            "fallback_reason": r.fallback_reason,
            "edits": list(r.edits) if r.edits is not None else None,
        }
        for r in sorted(records, key=lambda r: r.id)
    ]
    return sha256_json(payload)


def first_divergence(a: Sequence[OutputRecord], b: Sequence[OutputRecord]) -> str | None:
    bm = {r.id: r for r in b}
    for r in sorted(a, key=lambda r: r.id):
        o = bm.get(r.id)
        if o is None or (r.output_text, r.outcome, r.fallback_reason, r.edits) != (
            o.output_text,
            o.outcome,
            o.fallback_reason,
            o.edits,
        ):
            return r.id
    return None


def _now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _git_commit(repo: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True, timeout=10
        )
        return out.stdout.strip() or "unknown"
    except (subprocess.SubprocessError, OSError):
        return "unknown"


def _hardware() -> dict[str, Any]:
    machine = platform.machine() or "unknown"
    try:
        chip = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, timeout=5
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        chip = ""
    try:
        mem = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5).stdout.strip()
        ram_gb: float | None = round(int(mem) / (1024**3), 1) if mem else None
    except (subprocess.SubprocessError, OSError, ValueError):
        ram_gb = None
    return {
        "machine": f"{platform.node() or 'unknown'} ({chip or machine})",
        "os": f"{platform.system()} {platform.release()}",
        "accelerator": chip or machine,
        "ram_gb": ram_gb,
    }


def _packages(extra: dict[str, str]) -> dict[str, str]:
    pkgs = {"cleanupbench": __version__}
    for name in ("jsonschema", "mlx-lm", "mlx", "huggingface-hub"):
        try:
            pkgs[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    pkgs.update(extra)
    return dict(sorted(pkgs.items()))


def run_pass(
    adapter: Adapter, items: Sequence[Item], *, progress: Callable[[int, int, Item], None] | None = None
) -> list[OutputRecord]:
    records: list[OutputRecord] = []
    total = len(items)
    for n, item in enumerate(items, start=1):
        if progress:
            progress(n, total, item)
        try:
            out = adapter.clean(item)
        except AdapterError as exc:
            out = CleanOutput(output_text="", outcome="error", warnings=(f"adapter error: {exc}",))
        records.append(
            OutputRecord(
                id=item.id,
                output_text=out.output_text,
                outcome=out.outcome,
                fallback_reason=out.fallback_reason,
                edits=tuple(out.edits) if out.edits is not None else None,
                warnings=tuple(out.warnings),
                latency_ms=out.latency_ms,
                raw=out.raw,
            )
        )
    return records


def _progress_logger(log: Callable[[str], None]) -> Callable[[int, int, Item], None]:
    def progress(n: int, total: int, item: Item) -> None:
        if n % 25 == 0 or n == total:
            log(f"  [{n}/{total}] {item.id}")

    return progress


def validate_run_config(config: dict[str, Any]) -> None:
    missing = [k for k in REQUIRED_RUN_CONFIG if k not in config]
    if missing:
        raise RunConfigError(f"run config is missing {', '.join(missing)}")
    att = config["attestation"]
    for k in ("no_training_on_items", "known_overlap", "declared_exposure"):
        if k not in att:
            raise RunConfigError(f"run config attestation is missing {k!r}")


def run(
    *,
    adapter_name: str,
    adapter_config: dict[str, Any],
    run_config: dict[str, Any],
    items_dir: Path,
    runs_dir: Path,
    repo_root: Path,
    date: str | None = None,
    passes: int = 2,
    limit: int | None = None,
    log: Callable[[str], None] = lambda s: None,
) -> Path:
    """Run a system over the scorable items and write runs/<system>/<date>/."""
    validate_run_config(run_config)
    items = scorable(load_items(items_dir))
    if limit is not None:
        items = items[:limit]
    if not items:
        raise RunConfigError(f"no scorable items under {items_dir}")
    adapter = make_adapter(adapter_name, adapter_config)
    adapter.open()
    try:
        desc = adapter.describe()
        started = _now()
        log(f"pass A: {len(items)} items")
        pass_a = run_pass(adapter, items, progress=_progress_logger(log))
        if passes >= 2:
            log("pass B (determinism check)")
            pass_b = run_pass(adapter, items)
        else:
            pass_b = pass_a
        finished = _now()
    finally:
        adapter.close()

    hash_a = determinism_hash(pass_a)
    hash_b = determinism_hash(pass_b)
    identical = hash_a == hash_b

    date_str = date or started[:10]
    run_dir = runs_dir / run_config["system_name"] / date_str
    if run_dir.exists():
        raise RunConfigError(f"{run_dir} already exists; a run folder is never overwritten (pick --date)")
    run_dir.mkdir(parents=True)
    outputs_path = run_dir / OUTPUTS_NAME
    write_outputs(outputs_path, pass_a)

    prompt_text = desc.prompt_text
    system: dict[str, Any] = {
        "name": run_config["system_name"],
        "org": run_config["system_org"],
        "organizer_row": bool(run_config["organizer_row"]),
        "model_id": desc.model_id,
        "model_revision": desc.model_revision,
        "open_weights": desc.open_weights,
        "license": desc.license,
        "params_total": desc.params_total,
        "params_total_note": desc.params_total_note,
    }
    if run_config.get("display_name"):
        system["display_name"] = run_config["display_name"]
    if desc.gated_download:
        system["gated_download"] = True
    if desc.hosted:
        system["api_model_id"] = desc.api_model_id or desc.model_id
        system["api_date"] = desc.api_date or date_str
    else:
        system["weights_sha256"] = desc.weights_sha256 or sha256_text(desc.model_id + "@" + desc.model_revision)
    prompt: dict[str, Any] = {"sha256": sha256_text(prompt_text), "text": prompt_text}
    if desc.control_line is not None:
        prompt["control_line"] = desc.control_line
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "bench_version": BENCH_VERSION,
        "items_sha256": items_sha256(items_dir),
        "system": system,
        "adapter": {"name": adapter.name, "version": adapter.version, "config": desc.adapter_config},
        "prompt": prompt,
        "decoding": desc.decoding or {"strategy": "greedy", "temperature": 0, "max_tokens": None},
        "vocabulary_policy": desc.vocabulary_policy,
        "hardware": run_config.get("hardware") or _hardware(),
        "software": {
            "python": platform.python_version(),
            "packages": _packages(desc.packages),
            "bench_commit": _git_commit(repo_root),
        },
        "run": {
            "started_at": started,
            "finished_at": finished,
            "item_count": len(pass_a),
            "items_path": items_dir.as_posix(),
        },
        "determinism": {
            "run_a_sha256": hash_a,
            "run_b_sha256": hash_b,
            "identical": identical,
            "first_divergent_item": None if identical else first_divergence(pass_a, pass_b),
        },
        "outputs_sha256": sha256_file(outputs_path),
        "attestation": {
            "no_training_on_items": bool(run_config["attestation"]["no_training_on_items"]),
            "known_overlap": str(run_config["attestation"]["known_overlap"]),
            "declared_exposure": str(run_config["attestation"]["declared_exposure"]),
        },
        "hosted": desc.hosted,
        "hosted_expiry_flag": None,
        "checked_by": None,
        "checked_date": None,
    }
    if desc.hosted and not identical:
        manifest["nondeterministic"] = True
    if run_config.get("notes"):
        manifest["notes"] = str(run_config["notes"])
    write_manifest(run_dir / MANIFEST_NAME, manifest)
    log(f"wrote {run_dir} (determinism {'identical' if identical else 'DIFFERS'})")
    if not identical:
        print(
            "warning: the two passes differ (first divergent item: "
            f"{manifest['determinism']['first_divergent_item']}); "
            "score will refuse this row unless it is hosted and flagged",
            file=sys.stderr,
        )
    return run_dir


def load_json_file(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunConfigError(f"{path}: {exc}") from exc
    if not isinstance(obj, dict):
        raise RunConfigError(f"{path}: expected a JSON object")
    return obj
