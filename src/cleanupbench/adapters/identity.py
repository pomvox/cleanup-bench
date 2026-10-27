"""The identity adapter: the floor (docs/spec.md section 8)."""

from __future__ import annotations

from typing import Any

from cleanupbench.adapters.base import Adapter, CleanOutput, SystemDescription
from cleanupbench.hashing import sha256_text
from cleanupbench.items import Item


class IdentityAdapter(Adapter):
    name = "identity"
    version = "1"

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> IdentityAdapter:
        return cls()

    def describe(self) -> SystemDescription:
        return SystemDescription(
            model_id="identity",
            model_revision="none",
            open_weights=True,
            license="MIT",
            params_total=0,
            params_total_note="",
            weights_sha256=sha256_text("identity"),
            decoding={"strategy": "greedy", "temperature": 0, "max_tokens": None},
        )

    def clean(self, item: Item) -> CleanOutput:
        return CleanOutput(
            output_text=item.input,
            outcome="unchanged",
            edits=(),
            latency_ms=0.0,
        )
