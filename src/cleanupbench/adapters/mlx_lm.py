"""The mlx-lm adapter: SimpleWords v3 through `mlx_lm` exactly as the app's eval script does.

`mlx_lm` and `huggingface_hub` are imported inside `open()` so the module
imports on a machine without them (Linux CI). The recipe (app
`scripts/eval_cleanup_v2.py`, `clean()`): one user turn holding the prompt
file's text, a blank line and the raw transcript; `enable_thinking=False`;
`make_sampler(temp=0.0)`; `max_tokens=512`; the generation stripped.
"""

from __future__ import annotations

from importlib import metadata
from pathlib import Path
from typing import Any

from cleanupbench.adapters._prompting import (
    check_vocabulary_policy,
    describe_vocabulary_policy,
    with_vocabulary,
)
from cleanupbench.adapters.base import Adapter, AdapterConfigError, AdapterError, CleanOutput, SystemDescription
from cleanupbench.hashing import sha256_files
from cleanupbench.items import Item

# Quoted from the app's eval script, which is why this list is not an optimization and is not to be
# widened: "An unfiltered snapshot_download also pulls the repo's adapter/adapters.safetensors (67 MB
# of LoRA tensors) into the SHARED Hugging Face cache snapshot directory that Pomvox then loads with
# ModelConfiguration(directory:). mlx-swift-lm's loadWeights enumerates that directory RECURSIVELY,
# merges every .safetensors it finds, and calls update(parameters:verify: [.all]), which rejects the
# unused lora_a/lora_b keys -- so the app's cleanup prepare() fails and every dictation pastes the raw
# transcript until someone purges the cache by hand."
DEFAULT_ALLOW_PATTERNS: tuple[str, ...] = ("model*.safetensors", "*.json", "*.jinja", "system_v2.txt")
DEFAULT_MAX_TOKENS = 512
PROMPT_POSITIONS: tuple[str, ...] = ("user-prefix", "system")
WEIGHTS_GLOB = "model*.safetensors"


class MlxLmAdapter(Adapter):
    name = "mlx-lm"
    version = "1"

    def __init__(self, config: dict[str, Any]) -> None:
        self.model_id: str | None = config.get("model_id")
        self.model_path: str | None = config.get("model_path")
        if bool(self.model_id) == bool(self.model_path):
            raise AdapterConfigError("mlx-lm adapter needs exactly one of model_id or model_path")
        self.revision: str | None = config.get("revision")
        self.allow_patterns: list[str] = list(config.get("allow_patterns") or DEFAULT_ALLOW_PATTERNS)
        self.prompt_file: str | None = config.get("prompt_file")
        self.system_prompt_config: str | None = config.get("system_prompt")
        if bool(self.prompt_file) == bool(self.system_prompt_config is not None):
            raise AdapterConfigError("mlx-lm adapter needs exactly one of prompt_file or system_prompt")
        self.prompt_position = str(config.get("prompt_position", "user-prefix"))
        if self.prompt_position not in PROMPT_POSITIONS:
            raise AdapterConfigError(f"prompt_position must be one of {', '.join(PROMPT_POSITIONS)}")
        if config.get("enable_thinking", False) is not False:
            raise AdapterConfigError("enable_thinking must be false: the bench decodes greedily without thinking")
        self.max_tokens = int(config.get("max_tokens", DEFAULT_MAX_TOKENS))
        self.strip_output = bool(config.get("strip_output", True))
        self.vocabulary_policy = check_vocabulary_policy(str(config.get("vocabulary_policy", "none")))
        self.gated_download = bool(config.get("gated_download", False))
        self.license = str(config.get("license", "unknown"))
        self.open_weights = bool(config.get("open_weights", True))
        self.params_total: int | None = config.get("params_total")
        default_note = "" if self.params_total is not None else "unknown"
        self.params_total_note = str(config.get("params_total_note", default_note))
        self._config = config
        self._path: Path | None = None
        self._model: Any = None
        self._tokenizer: Any = None
        self._sampler: Any = None
        self._generate: Any = None
        self._system: str | None = None
        self._model_revision: str = str(self.revision or "unknown")
        self._weights_sha256: str | None = None

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> MlxLmAdapter:
        return cls(config)

    # -- lifecycle -----------------------------------------------------------------------------------------------

    def open(self) -> None:
        from mlx_lm import generate, load
        from mlx_lm.sample_utils import make_sampler

        if self.model_id:
            from huggingface_hub import snapshot_download

            kwargs: dict[str, Any] = {"allow_patterns": list(self.allow_patterns)}
            if self.revision:
                kwargs["revision"] = self.revision
            path = Path(snapshot_download(self.model_id, **kwargs)).resolve()
            # The HF cache lays a snapshot out as models--org--name/snapshots/<commit>/.
            self._model_revision = path.name if path.parent.name == "snapshots" else str(self.revision or path.name)
        else:
            path = Path(str(self.model_path)).resolve()
            if not path.is_dir():
                raise AdapterConfigError(f"model_path {path} is not a directory")
        self._path = path
        weights = sorted(path.glob(WEIGHTS_GLOB))
        if not weights:
            raise AdapterConfigError(f"no {WEIGHTS_GLOB} under {path}")
        self._weights_sha256 = sha256_files(weights)
        if self.prompt_file:
            prompt_path = path / self.prompt_file
            try:
                self._system = prompt_path.read_text("utf-8").strip()
            except OSError as exc:
                raise AdapterConfigError(f"prompt_file {prompt_path} cannot be read: {exc}") from exc
        else:
            self._system = str(self.system_prompt_config).strip()
        self._model, self._tokenizer = load(str(path))
        self._sampler = make_sampler(temp=0.0)
        self._generate = generate

    def close(self) -> None:
        self._model = self._tokenizer = self._sampler = self._generate = None

    def _require_open(self) -> None:
        if self._system is None or self._tokenizer is None:
            raise AdapterError("mlx-lm adapter is not open; call open() first")

    # -- prompt --------------------------------------------------------------------------------------------------

    def messages_for(self, item: Item) -> list[dict[str, str]]:
        self._require_open()
        system = with_vocabulary(str(self._system), item, self.vocabulary_policy)
        if self.prompt_position == "system":
            return [{"role": "system", "content": system}, {"role": "user", "content": item.input}]
        return [{"role": "user", "content": f"{system}\n\n{item.input}"}]

    def prompt_for(self, item: Item) -> str:
        return self._tokenizer.apply_chat_template(
            self.messages_for(item), add_generation_prompt=True, enable_thinking=False, tokenize=False
        )

    # -- the interface -------------------------------------------------------------------------------------------

    def describe(self) -> SystemDescription:
        self._require_open()
        packages: dict[str, str] = {}
        for pkg in ("mlx-lm", "mlx", "huggingface-hub"):
            try:
                packages[pkg] = metadata.version(pkg)
            except metadata.PackageNotFoundError:
                continue
        adapter_config = dict(self._config)
        adapter_config.update(
            {
                "allow_patterns": list(self.allow_patterns),
                "snapshot_path": self._path.as_posix() if self._path else None,
                "prompt_position": self.prompt_position,
                "strip_output": self.strip_output,
                "max_tokens": self.max_tokens,
            }
        )
        rendering = {
            "user-prefix": "one user turn: prompt text, a blank line, the transcript",
            "system": "a system turn holding the prompt text, then the transcript as the user turn",
        }[self.prompt_position]
        adapter_config["prompt_rendering"] = rendering
        return SystemDescription(
            model_id=self.model_id or str(self.model_path),
            model_revision=self._model_revision,
            open_weights=self.open_weights,
            license=self.license,
            params_total=self.params_total,
            params_total_note=self.params_total_note,
            weights_sha256=self._weights_sha256,
            hosted=False,
            gated_download=self.gated_download,
            prompt_text=str(self._system),
            decoding={"strategy": "greedy", "temperature": 0, "max_tokens": self.max_tokens, "thinking": False},
            vocabulary_policy=describe_vocabulary_policy(self.vocabulary_policy),
            adapter_config=adapter_config,
            packages=packages,
        )

    def clean(self, item: Item) -> CleanOutput:
        import time

        self._require_open()
        prompt = self.prompt_for(item)
        t0 = time.perf_counter()
        try:
            raw = self._generate(
                self._model, self._tokenizer, prompt=prompt, max_tokens=self.max_tokens, sampler=self._sampler,
                verbose=False,
            )
        except Exception as exc:  # noqa: BLE001 - mlx raises assorted runtime errors; surface them as adapter errors
            raise AdapterError(f"mlx_lm.generate failed: {exc.__class__.__name__}: {exc}") from exc
        latency_ms = (time.perf_counter() - t0) * 1000.0
        if not isinstance(raw, str):
            raise AdapterError("mlx_lm.generate did not return a string")
        output = raw.strip() if self.strip_output else raw
        return CleanOutput(
            output_text=output,
            outcome=CleanOutput.derive_outcome(item.input, output),
            latency_ms=round(latency_ms, 3),
            raw=raw,
        )
