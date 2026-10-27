"""Loading and validating benchmark items (docs/spec.md section 4).

Item files are JSON Lines under `data/items/`. Every file begins with one or
more comment lines (`#`); the first of them carries the canary string
(docs/spec.md section 7.5). Blank lines are ignored.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cleanupbench.hashing import sha256_files

ITEM_FILE_SUFFIX = ".jsonl"

CATEGORY_ORDER: tuple[str, ...] = (
    "negatives",
    "adversarial-meaning",
    "instruction-like",
    "punctuation-casing",
    "correction-intra",
    "correction-cross",
    "correction-interrogative",
    "restarts",
    "spoken-form",
    "lists-layout",
    "names-vocabulary",
    "fillers",
)
"""Leaderboard column order (docs/spec.md section 3.2)."""

SCORED_INPUT_FORMS: frozenset[str] = frozenset({"lowercase-unpunctuated"})
"""Input forms scored in v1 (decision 20)."""


class ItemError(ValueError):
    """An item file or item is malformed."""


@dataclass(frozen=True, slots=True)
class Item:
    id: str
    category: str
    input: str
    input_form: str
    vocabulary: tuple[str, ...]
    references: tuple[str, ...]
    must_contain: tuple[str, ...]
    must_not_contain: tuple[str, ...]
    source: dict[str, str]
    notes: str
    released: str
    status: str
    scored: bool
    slice: str | None = None
    taxonomy: tuple[str, ...] = ()
    retired_in: str | None = None
    issue: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def is_scorable(self) -> bool:
        return self.status == "active" and self.scored and self.input_form in SCORED_INPUT_FORMS

    def to_json(self) -> dict[str, Any]:
        obj: dict[str, Any] = {
            "id": self.id,
            "category": self.category,
        }
        if self.slice is not None:
            obj["slice"] = self.slice
        obj.update(
            {
                "input": self.input,
                "input_form": self.input_form,
                "vocabulary": list(self.vocabulary),
                "references": list(self.references),
                "slots": {
                    "must_contain": list(self.must_contain),
                    "must_not_contain": list(self.must_not_contain),
                },
                "source": dict(self.source),
                "notes": self.notes,
                "taxonomy": list(self.taxonomy),
                "released": self.released,
                "status": self.status,
            }
        )
        if self.retired_in is not None:
            obj["retired_in"] = self.retired_in
        if self.issue is not None:
            obj["issue"] = self.issue
        obj["scored"] = self.scored
        return obj

    @classmethod
    def from_json(cls, obj: dict[str, Any]) -> Item:
        slots = obj["slots"]
        return cls(
            id=obj["id"],
            category=obj["category"],
            slice=obj.get("slice"),
            input=obj["input"],
            input_form=obj["input_form"],
            vocabulary=tuple(obj["vocabulary"]),
            references=tuple(obj["references"]),
            must_contain=tuple(slots["must_contain"]),
            must_not_contain=tuple(slots["must_not_contain"]),
            source=dict(obj["source"]),
            notes=obj["notes"],
            taxonomy=tuple(obj.get("taxonomy", ())),
            released=obj["released"],
            status=obj["status"],
            retired_in=obj.get("retired_in"),
            issue=obj.get("issue"),
            scored=obj["scored"],
        )


def _schema() -> dict[str, Any]:
    text = resources.files("cleanupbench.schemas").joinpath("item.schema.json").read_text("utf-8")
    return json.loads(text)


_VALIDATOR: Draft202012Validator | None = None


def item_validator() -> Draft202012Validator:
    global _VALIDATOR
    if _VALIDATOR is None:
        _VALIDATOR = Draft202012Validator(_schema())
    return _VALIDATOR


def validate_item_object(obj: dict[str, Any], *, where: str = "") -> list[str]:
    """Return a list of human-readable schema and consistency errors (empty when valid)."""
    errors = [
        f"{where}{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in sorted(item_validator().iter_errors(obj), key=lambda e: list(e.absolute_path))
    ]
    if errors:
        return errors
    # Consistency checks beyond the schema.
    category = obj["category"]
    slice_ = obj.get("slice")
    expected_prefix = f"{category}-{slice_ or 'core'}-"
    if not obj["id"].startswith(expected_prefix):
        errors.append(f"{where}id: {obj['id']!r} must start with {expected_prefix!r}")
    for ref in obj["references"]:
        if ref != ref.strip() and ref != "":
            errors.append(f"{where}references: {ref!r} has leading or trailing whitespace")
    if obj["input"] != obj["input"].strip():
        errors.append(f"{where}input: has leading or trailing whitespace")
    if len(set(obj["references"])) != len(obj["references"]):
        errors.append(f"{where}references: duplicate reference")
    return errors


def item_files(items_dir: Path) -> list[Path]:
    return sorted(p for p in items_dir.glob(f"*{ITEM_FILE_SUFFIX}") if p.is_file())


def iter_item_file(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield (line_number, object) for each non-comment, non-blank line."""
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ItemError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
            if not isinstance(obj, dict):
                raise ItemError(f"{path}:{lineno}: item must be a JSON object")
            yield lineno, obj


def file_header(path: Path) -> list[str]:
    """The leading comment lines of an item file (without the `#`)."""
    header: list[str] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                header.append(line[1:].strip())
            elif line.strip():
                break
    return header


def validate_items_dir(items_dir: Path, *, require_canary: str | None = None) -> list[str]:
    """Validate every item file. Returns errors; empty means valid."""
    errors: list[str] = []
    seen: dict[str, str] = {}
    files = item_files(items_dir)
    if not files:
        return [f"{items_dir}: no item files found"]
    for path in files:
        if require_canary is not None:
            header = file_header(path)
            if not any(require_canary in h for h in header):
                errors.append(f"{path}: canary string missing from file header")
        try:
            for lineno, obj in iter_item_file(path):
                where = f"{path}:{lineno}: "
                errors.extend(validate_item_object(obj, where=where))
                if "id" in obj and "category" in obj:
                    if obj["id"] in seen:
                        errors.append(f"{where}duplicate id {obj['id']!r} (also in {seen[obj['id']]})")
                    seen[obj["id"]] = f"{path}:{lineno}"
                    if obj["category"] != path.stem:
                        errors.append(
                            f"{where}category {obj['category']!r} does not match file {path.name!r}"
                        )
        except ItemError as exc:
            errors.append(str(exc))
    return errors


def load_items(items_dir: Path, *, validate: bool = True) -> list[Item]:
    if validate:
        errors = validate_items_dir(items_dir)
        if errors:
            raise ItemError("\n".join(errors))
    items: list[Item] = []
    for path in item_files(items_dir):
        for _, obj in iter_item_file(path):
            items.append(Item.from_json(obj))
    return items


def items_sha256(items_dir: Path) -> str:
    return sha256_files(item_files(items_dir))


def scorable(items: Iterable[Item]) -> list[Item]:
    return [i for i in items if i.is_scorable]
