"""Content hashing used by manifests and the determinism check.

Everything here is deterministic by construction: canonical JSON with sorted
keys and no insignificant whitespace, UTF-8 bytes, SHA-256.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_files(paths: Iterable[Path]) -> str:
    """Hash of several files in sorted path order, each prefixed by its name.

    Used for `items_sha256`: the hash changes if any item file's bytes or
    name changes, and does not depend on directory listing order.
    """
    h = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.as_posix()):
        h.update(path.name.encode("utf-8"))
        h.update(b"\0")
        h.update(sha256_file(path).encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def canonical_json(value: Any) -> str:
    """Canonical JSON: sorted keys, no extra whitespace, non-ASCII kept."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return sha256_text(canonical_json(value))
