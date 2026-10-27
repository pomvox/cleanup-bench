"""The adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from cleanupbench.items import Item


class AdapterConfigError(ValueError):
    """The adapter's configuration is missing or wrong."""


class AdapterError(RuntimeError):
    """A request to the system failed in a way the adapter could not express as an outcome."""


@dataclass(frozen=True, slots=True)
class CleanOutput:
    """What a system returned for one item, raw."""

    output_text: str
    outcome: str  # cleaned | unchanged | fallback | error
    fallback_reason: str | None = None
    edits: tuple[dict[str, Any], ...] | None = None
    warnings: tuple[str, ...] = ()
    latency_ms: float | None = None
    raw: str | None = None

    @staticmethod
    def derive_outcome(input_text: str, output_text: str) -> str:
        """For adapters without outcomes: byte-identical output is `unchanged`, else `cleaned`."""
        return "unchanged" if output_text == input_text else "cleaned"


@dataclass
class SystemDescription:
    """What the adapter knows about the system, for the manifest (docs/spec.md section 9)."""

    model_id: str
    model_revision: str
    open_weights: bool
    license: str
    params_total: int | None
    params_total_note: str
    weights_sha256: str | None = None
    api_model_id: str | None = None
    api_date: str | None = None
    hosted: bool = False
    gated_download: bool = False
    prompt_text: str = ""
    control_line: str | None = None
    decoding: dict[str, Any] = field(default_factory=dict)
    vocabulary_policy: dict[str, str] = field(default_factory=lambda: {"source": "none", "rendering": ""})
    adapter_config: dict[str, Any] = field(default_factory=dict)
    packages: dict[str, str] = field(default_factory=dict)


class Adapter(ABC):
    """One system behind one interface.

    `name` and `version` identify the bench's own code path; `describe()`
    fills the manifest; `clean()` is called once per item per pass. Adapters
    must be deterministic given greedy decoding; the runner checks that.
    """

    name: str = "abstract"
    version: str = "0"

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict[str, Any]) -> Adapter: ...

    @abstractmethod
    def describe(self) -> SystemDescription: ...

    @abstractmethod
    def clean(self, item: Item) -> CleanOutput: ...

    def open(self) -> None:  # noqa: B027 - optional hook
        """Acquire resources (load a model, check a server). Default: nothing."""

    def close(self) -> None:  # noqa: B027 - optional hook
        """Release resources. Default: nothing."""
