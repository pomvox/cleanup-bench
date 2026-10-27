"""Run manifests (`run.json`) and output records (`outputs.jsonl`).

`score` refuses a run folder whose manifest is incomplete or whose outputs
file does not match the manifest's `outputs_sha256` (docs/spec.md section 9).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from cleanupbench.hashing import sha256_file

MANIFEST_NAME = "run.json"
OUTPUTS_NAME = "outputs.jsonl"
SCORES_NAME = "scores.json"


class ManifestError(ValueError):
    """The manifest or outputs file is missing, malformed or inconsistent."""


def _load_schema(name: str) -> dict[str, Any]:
    text = resources.files("cleanupbench.schemas").joinpath(name).read_text("utf-8")
    return json.loads(text)


_RUN_VALIDATOR: Draft202012Validator | None = None
_OUTPUT_VALIDATOR: Draft202012Validator | None = None


def run_validator() -> Draft202012Validator:
    global _RUN_VALIDATOR
    if _RUN_VALIDATOR is None:
        _RUN_VALIDATOR = Draft202012Validator(_load_schema("run.schema.json"), format_checker=FormatChecker())
    return _RUN_VALIDATOR


def output_validator() -> Draft202012Validator:
    global _OUTPUT_VALIDATOR
    if _OUTPUT_VALIDATOR is None:
        _OUTPUT_VALIDATOR = Draft202012Validator(_load_schema("output.schema.json"))
    return _OUTPUT_VALIDATOR


def _format_errors(validator: Draft202012Validator, obj: Any, where: str) -> list[str]:
    return [
        f"{where}{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(obj), key=lambda e: list(e.absolute_path))
    ]


def validate_manifest_object(obj: Any, *, where: str = "run.json: ") -> list[str]:
    return _format_errors(run_validator(), obj, where)


def validate_output_object(obj: Any, *, where: str = "") -> list[str]:
    return _format_errors(output_validator(), obj, where)


@dataclass(frozen=True, slots=True)
class OutputRecord:
    id: str
    output_text: str
    outcome: str
    fallback_reason: str | None
    edits: tuple[dict[str, Any], ...] | None
    warnings: tuple[str, ...]
    latency_ms: float | None
    raw: str | None

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "output_text": self.output_text,
            "outcome": self.outcome,
            "fallback_reason": self.fallback_reason,
            "edits": list(self.edits) if self.edits is not None else None,
            "warnings": list(self.warnings),
            "latency_ms": self.latency_ms,
            "raw": self.raw,
        }

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> OutputRecord:
        edits = obj["edits"]
        return cls(
            id=obj["id"],
            output_text=obj["output_text"],
            outcome=obj["outcome"],
            fallback_reason=obj["fallback_reason"],
            edits=tuple(edits) if edits is not None else None,
            warnings=tuple(obj["warnings"]),
            latency_ms=obj["latency_ms"],
            raw=obj["raw"],
        )


def write_outputs(path: Path, records: list[OutputRecord]) -> None:
    """Write outputs.jsonl deterministically: one canonical JSON object per line, sorted by id."""
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for rec in sorted(records, key=lambda r: r.id):
            fh.write(json.dumps(rec.to_json(), sort_keys=True, ensure_ascii=False))
            fh.write("\n")


def read_outputs(path: Path) -> list[OutputRecord]:
    records: list[OutputRecord] = []
    errors: list[str] = []
    seen: set[str] = set()
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ManifestError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
            errs = validate_output_object(obj, where=f"{path}:{lineno}: ")
            if errs:
                errors.extend(errs)
                continue
            if obj["id"] in seen:
                errors.append(f"{path}:{lineno}: duplicate output id {obj['id']!r}")
            seen.add(obj["id"])
            records.append(OutputRecord.from_json(obj))
    if errors:
        raise ManifestError("\n".join(errors))
    return records


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    errors = validate_manifest_object(manifest)
    if errors:
        raise ManifestError("\n".join(errors))
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n", "utf-8")


def read_manifest(run_dir: Path) -> dict[str, Any]:
    path = run_dir / MANIFEST_NAME
    if not path.is_file():
        raise ManifestError(f"{path}: missing manifest")
    try:
        obj = json.loads(path.read_text("utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"{path}: invalid JSON: {exc}") from exc
    errors = validate_manifest_object(obj, where=f"{path}: ")
    if errors:
        raise ManifestError("\n".join(errors))
    return obj


def check_run_dir(run_dir: Path, *, allow_nondeterministic: bool = False) -> tuple[dict[str, Any], list[OutputRecord]]:
    """Load and cross-check a run folder. Raises ManifestError on any refusal.

    Refusals, in order: missing or invalid manifest; missing outputs file;
    outputs hash does not match the manifest; determinism check failed (unless
    the row is hosted and the caller allows it); malformed output records.
    """
    manifest = read_manifest(run_dir)
    outputs_path = run_dir / OUTPUTS_NAME
    if not outputs_path.is_file():
        raise ManifestError(f"{outputs_path}: missing outputs file")
    actual = sha256_file(outputs_path)
    if actual != manifest["outputs_sha256"]:
        raise ManifestError(
            f"{run_dir}: outputs_sha256 in manifest ({manifest['outputs_sha256']}) does not match "
            f"outputs.jsonl ({actual})"
        )
    det = manifest["determinism"]
    if not det["identical"]:
        if not (manifest["hosted"] and allow_nondeterministic and manifest.get("nondeterministic") is True):
            raise ManifestError(
                f"{run_dir}: determinism check failed (run_a != run_b); refusing to score. "
                "Hosted rows may be scored with --allow-nondeterministic when the manifest sets "
                "nondeterministic: true (decision S4)."
            )
    records = read_outputs(outputs_path)
    if manifest["run"]["item_count"] != len(records):
        raise ManifestError(
            f"{run_dir}: manifest item_count {manifest['run']['item_count']} != {len(records)} output records"
        )
    return manifest, records
