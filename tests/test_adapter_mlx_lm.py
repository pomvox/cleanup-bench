"""mlx-lm adapter with fake `mlx_lm`, `mlx_lm.sample_utils` and `huggingface_hub` modules injected into sys.modules."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from conftest import make_item

from cleanupbench.adapters import make_adapter
from cleanupbench.adapters.base import AdapterConfigError
from cleanupbench.adapters.mlx_lm import DEFAULT_ALLOW_PATTERNS
from cleanupbench.hashing import sha256_files

PROMPT = "You clean dictation.\n"


class FakeTokenizer:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def apply_chat_template(self, messages, **kwargs):
        self.calls.append({"messages": messages, **kwargs})
        return "<chat>" + "|".join(f"{m['role']}:{m['content']}" for m in messages) + "</chat>"


class Fakes:
    def __init__(self, snapshot: Path, generation: str) -> None:
        self.snapshot = snapshot
        self.generation = generation
        self.snapshot_calls: list[dict] = []
        self.load_calls: list[str] = []
        self.sampler_calls: list[dict] = []
        self.generate_calls: list[dict] = []
        self.tokenizer = FakeTokenizer()

    def snapshot_download(self, repo_id, **kwargs):
        self.snapshot_calls.append({"repo_id": repo_id, **kwargs})
        return str(self.snapshot)

    def load(self, path):
        self.load_calls.append(path)
        return object(), self.tokenizer

    def make_sampler(self, **kwargs):
        self.sampler_calls.append(kwargs)
        return ("sampler", tuple(sorted(kwargs.items())))

    def generate(self, model, tokenizer, **kwargs):
        self.generate_calls.append({"model": model, "tokenizer": tokenizer, **kwargs})
        return self.generation


@pytest.fixture
def fakes(tmp_path: Path, monkeypatch) -> Fakes:
    snapshot = tmp_path / "hub" / "models--ReFyneLabs--simplewords" / "snapshots" / "abc123def456"
    snapshot.mkdir(parents=True)
    (snapshot / "model-00001-of-00002.safetensors").write_bytes(b"weights-one")
    (snapshot / "model-00002-of-00002.safetensors").write_bytes(b"weights-two")
    (snapshot / "config.json").write_text("{}", "utf-8")
    (snapshot / "system_v2.txt").write_text(PROMPT, "utf-8")
    f = Fakes(snapshot, "  Let's go.  \n")
    mlx_lm = types.ModuleType("mlx_lm")
    mlx_lm.load = f.load
    mlx_lm.generate = f.generate
    sample_utils = types.ModuleType("mlx_lm.sample_utils")
    sample_utils.make_sampler = f.make_sampler
    mlx_lm.sample_utils = sample_utils
    hf = types.ModuleType("huggingface_hub")
    hf.snapshot_download = f.snapshot_download
    monkeypatch.setitem(sys.modules, "mlx_lm", mlx_lm)
    monkeypatch.setitem(sys.modules, "mlx_lm.sample_utils", sample_utils)
    monkeypatch.setitem(sys.modules, "huggingface_hub", hf)
    return f


def base_config(**extra) -> dict:
    cfg = {"model_id": "ReFyneLabs/simplewords-dictation-cleanup-v3", "prompt_file": "system_v2.txt"}
    cfg.update(extra)
    return cfg


def test_module_imports_without_mlx(monkeypatch):
    monkeypatch.setitem(sys.modules, "mlx_lm", None)
    monkeypatch.setitem(sys.modules, "huggingface_hub", None)
    adapter = make_adapter("mlx-lm", base_config())
    assert adapter.name == "mlx-lm"
    with pytest.raises(ImportError):
        adapter.open()


def test_open_snapshot_recipe_and_clean(fakes: Fakes):
    adapter = make_adapter("mlx-lm", base_config(gated_download=True, license="Apache-2.0"))
    adapter.open()

    assert fakes.snapshot_calls == [
        {"repo_id": "ReFyneLabs/simplewords-dictation-cleanup-v3", "allow_patterns": list(DEFAULT_ALLOW_PATTERNS)}
    ]
    assert list(DEFAULT_ALLOW_PATTERNS) == ["model*.safetensors", "*.json", "*.jinja", "system_v2.txt"]
    assert fakes.load_calls == [str(fakes.snapshot)]
    assert fakes.sampler_calls == [{"temp": 0.0}]

    out = adapter.clean(make_item())
    call = fakes.tokenizer.calls[-1]
    assert call["messages"] == [{"role": "user", "content": "You clean dictation.\n\num so let's go"}]
    assert call["add_generation_prompt"] is True and call["enable_thinking"] is False and call["tokenize"] is False
    gen = fakes.generate_calls[-1]
    assert gen["tokenizer"] is fakes.tokenizer
    assert gen["prompt"] == "<chat>user:You clean dictation.\n\num so let's go</chat>"
    assert gen["max_tokens"] == 512
    assert gen["sampler"] == ("sampler", (("temp", 0.0),))
    assert gen["verbose"] is False

    assert out.output_text == "Let's go."  # stripped
    assert out.raw == "  Let's go.  \n"  # the unstripped generation
    assert out.outcome == "cleaned"
    assert out.latency_ms is not None and out.latency_ms >= 0

    desc = adapter.describe()
    assert desc.model_revision == "abc123def456"  # snapshots/<commit>
    assert desc.weights_sha256 == sha256_files(sorted(fakes.snapshot.glob("model*.safetensors")))
    assert desc.prompt_text == "You clean dictation."  # stripped, as the app script does
    assert desc.decoding == {"strategy": "greedy", "temperature": 0, "max_tokens": 512, "thinking": False}
    assert desc.hosted is False and desc.gated_download is True and desc.license == "Apache-2.0"
    assert desc.adapter_config["allow_patterns"] == list(DEFAULT_ALLOW_PATTERNS)
    assert desc.adapter_config["snapshot_path"] == fakes.snapshot.as_posix()
    assert desc.vocabulary_policy == {"source": "none", "rendering": ""}


def test_strip_output_false_and_unchanged(fakes: Fakes):
    adapter = make_adapter("mlx-lm", base_config(strip_output=False, max_tokens=64))
    adapter.open()
    out = adapter.clean(make_item())
    assert out.output_text == "  Let's go.  \n" and out.raw == "  Let's go.  \n"
    assert fakes.generate_calls[-1]["max_tokens"] == 64
    fakes.generation = "um so let's go"
    assert adapter.clean(make_item()).outcome == "unchanged"


def test_system_position_and_vocabulary_and_revision(fakes: Fakes):
    adapter = make_adapter(
        "mlx-lm", base_config(prompt_position="system", vocabulary_policy="system-suffix", revision="main")
    )
    adapter.open()
    assert fakes.snapshot_calls[-1]["revision"] == "main"
    adapter.clean(make_item(vocabulary=("Pomvox",)))
    assert fakes.tokenizer.calls[-1]["messages"] == [
        {"role": "system", "content": "You clean dictation.\nVocabulary: Pomvox"},
        {"role": "user", "content": "um so let's go"},
    ]
    assert adapter.describe().model_revision == "abc123def456"  # the resolved snapshot wins over the ref name


def test_model_path_and_inline_prompt(fakes: Fakes):
    cfg = {"model_path": str(fakes.snapshot), "system_prompt": "  inline prompt  "}
    adapter = make_adapter("mlx-lm", cfg)
    adapter.open()
    assert fakes.snapshot_calls == []
    adapter.clean(make_item())
    assert fakes.tokenizer.calls[-1]["messages"][0]["content"] == "inline prompt\n\num so let's go"
    desc = adapter.describe()
    assert desc.model_id == str(fakes.snapshot) and desc.model_revision == "unknown"
    assert desc.weights_sha256 == sha256_files(sorted(fakes.snapshot.glob("model*.safetensors")))


def test_refusals(fakes: Fakes):
    with pytest.raises(AdapterConfigError, match="enable_thinking"):
        make_adapter("mlx-lm", base_config(enable_thinking=True))
    with pytest.raises(AdapterConfigError, match="model_id or model_path"):
        make_adapter("mlx-lm", {"prompt_file": "system_v2.txt"})
    with pytest.raises(AdapterConfigError, match="prompt_file or system_prompt"):
        make_adapter("mlx-lm", {"model_id": "x"})
    with pytest.raises(AdapterConfigError, match="prompt_position"):
        make_adapter("mlx-lm", base_config(prompt_position="suffix"))
    adapter = make_adapter("mlx-lm", base_config(prompt_file="missing.txt"))
    with pytest.raises(AdapterConfigError, match="missing.txt"):
        adapter.open()
