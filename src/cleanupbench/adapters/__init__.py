"""Adapters: one interface, several systems (docs/spec.md section 8, decision 19).

An adapter turns an item into an output record. It never scores, never
normalizes, and never applies a guard; raw output is stored and the scorer
does the rest.
"""

from __future__ import annotations

from cleanupbench.adapters.base import Adapter, AdapterConfigError, CleanOutput

ADAPTER_NAMES: tuple[str, ...] = ("identity", "openai-compatible", "anthropic", "mlx-lm", "pomvox-localserver")


def make_adapter(name: str, config: dict) -> Adapter:
    """Construct an adapter by name. Imports are lazy so optional dependencies stay optional."""
    try:
        return _make_adapter(name, config)
    except ImportError as exc:
        raise AdapterConfigError(f"adapter {name!r} is not available in this build: {exc}") from exc


def _make_adapter(name: str, config: dict) -> Adapter:
    if name == "identity":
        from cleanupbench.adapters.identity import IdentityAdapter

        return IdentityAdapter.from_config(config)
    if name == "openai-compatible":
        from cleanupbench.adapters.openai_compatible import OpenAICompatibleAdapter

        return OpenAICompatibleAdapter.from_config(config)
    if name == "anthropic":
        from cleanupbench.adapters.anthropic import AnthropicAdapter

        return AnthropicAdapter.from_config(config)
    if name == "mlx-lm":
        from cleanupbench.adapters.mlx_lm import MlxLmAdapter

        return MlxLmAdapter.from_config(config)
    if name == "pomvox-localserver":
        from cleanupbench.adapters.pomvox_localserver import PomvoxLocalServerAdapter

        return PomvoxLocalServerAdapter.from_config(config)
    raise AdapterConfigError(f"unknown adapter {name!r}; choose one of {', '.join(ADAPTER_NAMES)}")


__all__ = ["ADAPTER_NAMES", "Adapter", "AdapterConfigError", "CleanOutput", "make_adapter"]
