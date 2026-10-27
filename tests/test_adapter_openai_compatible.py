"""OpenAI-compatible adapter against an in-process fake chat-completions server."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import FakeServer, make_item

from cleanupbench.adapters import make_adapter
from cleanupbench.adapters.base import AdapterConfigError, AdapterError
from cleanupbench.adapters.openai_compatible import OpenAICompatibleAdapter

SECRET = "sk-test-secret-value-do-not-leak"


def chat_response(text: str | None, finish: str = "stop") -> dict:
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "model": "fake",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": finish}],
    }


def base_config(server: FakeServer, **extra) -> dict:
    cfg = {"base_url": server.base_url + "/v1", "model": "fake-model", "system_prompt": "Clean the dictation."}
    cfg.update(extra)
    return cfg


def test_request_shape_and_output(fake_server: FakeServer, monkeypatch):
    monkeypatch.setenv("FAKE_KEY_ENV", SECRET)
    fake_server.responder = lambda req: (200, chat_response("Let's go."))
    adapter = make_adapter(
        "openai-compatible",
        base_config(
            fake_server,
            api_key_env="FAKE_KEY_ENV",
            control_line="[Styling: semi-formal] [Structure: prose] [Context: general]",
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            max_tokens=77,
            seed=4,
        ),
    )
    assert isinstance(adapter, OpenAICompatibleAdapter)
    adapter.open()
    out = adapter.clean(make_item())
    adapter.close()

    req = fake_server.last
    assert req.method == "POST" and req.path == "/v1/chat/completions"
    assert req.headers["authorization"] == f"Bearer {SECRET}"
    assert req.headers["content-type"] == "application/json"
    body = req.json
    assert body["temperature"] == 0
    assert body["max_tokens"] == 77
    assert body["seed"] == 4
    assert body["model"] == "fake-model"
    assert body["stream"] is False
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert body["messages"] == [
        {
            "role": "system",
            "content": "Clean the dictation.\n[Styling: semi-formal] [Structure: prose] [Context: general]",
        },
        {"role": "user", "content": "um so let's go"},
    ]

    assert out.output_text == "Let's go."
    assert out.outcome == "cleaned"
    assert out.latency_ms is not None and out.latency_ms >= 0
    assert out.raw is not None and json.loads(out.raw)["choices"][0]["message"]["content"] == "Let's go."
    assert out.edits is None and out.warnings == ()

    desc = adapter.describe()
    assert desc.decoding == {"strategy": "greedy", "temperature": 0, "max_tokens": 77, "thinking": False, "seed": 4}
    assert desc.control_line == "[Styling: semi-formal] [Structure: prose] [Context: general]"
    assert desc.prompt_text.endswith("\n[Styling: semi-formal] [Structure: prose] [Context: general]")
    assert desc.hosted is False and desc.open_weights is True
    assert desc.adapter_config["api_key_env"] == "FAKE_KEY_ENV"
    assert SECRET not in json.dumps(desc.adapter_config)
    assert SECRET not in json.dumps(desc.__dict__, default=str)
    assert desc.vocabulary_policy == {"source": "none", "rendering": ""}


def test_output_is_not_stripped_and_unchanged_is_derived(fake_server: FakeServer):
    fake_server.responder = lambda req: (200, chat_response("  um so let's go  "))
    adapter = make_adapter("openai-compatible", base_config(fake_server))
    adapter.open()
    out = adapter.clean(make_item())
    assert out.output_text == "  um so let's go  "  # the scorer normalizes, the adapter does not
    assert out.outcome == "cleaned"
    fake_server.responder = lambda req: (200, chat_response("um so let's go"))
    assert adapter.clean(make_item()).outcome == "unchanged"
    fake_server.responder = lambda req: (200, chat_response(""))
    out = adapter.clean(make_item())
    assert out.output_text == "" and out.outcome == "cleaned"  # empty is a status for the scorer (decision 14)


def test_vocabulary_system_suffix(fake_server: FakeServer):
    fake_server.responder = lambda req: (200, chat_response("x"))
    adapter = make_adapter("openai-compatible", base_config(fake_server, vocabulary_policy="system-suffix"))
    adapter.open()
    adapter.clean(make_item(vocabulary=("Pomvox", "Kubernetes")))
    assert fake_server.last.json["messages"][0]["content"] == "Clean the dictation.\nVocabulary: Pomvox, Kubernetes"
    adapter.clean(make_item())  # no vocabulary: no suffix
    assert fake_server.last.json["messages"][0]["content"] == "Clean the dictation."
    desc = adapter.describe()
    assert desc.vocabulary_policy["source"] == "item"
    assert "Vocabulary: a, b, c" in desc.vocabulary_policy["rendering"]
    assert desc.prompt_text == "Clean the dictation."  # the manifest prompt never carries per-item material


def test_user_template_with_vocabulary(fake_server: FakeServer):
    fake_server.responder = lambda req: (200, chat_response("x"))
    adapter = make_adapter(
        "openai-compatible", base_config(fake_server, user_template="Terms: {vocabulary}\nTranscript: {input}")
    )
    adapter.open()
    adapter.clean(make_item(vocabulary=("Pomvox",)))
    assert fake_server.last.json["messages"][1]["content"] == "Terms: Pomvox\nTranscript: um so let's go"
    assert adapter.describe().vocabulary_policy["source"] == "item"


def test_system_prompt_file(fake_server: FakeServer, tmp_path: Path):
    p = tmp_path / "prompt.txt"
    p.write_text("From a file.\n", "utf-8")
    fake_server.responder = lambda req: (200, chat_response("x"))
    cfg = {"base_url": fake_server.base_url + "/v1", "model": "m", "system_prompt_file": str(p)}
    adapter = make_adapter("openai-compatible", cfg)
    adapter.open()
    adapter.clean(make_item())
    assert fake_server.last.json["messages"][0]["content"] == "From a file.\n"
    assert adapter.describe().prompt_text == "From a file.\n"


def test_no_system_prompt_sends_only_user_turn(fake_server: FakeServer):
    fake_server.responder = lambda req: (200, chat_response("x"))
    adapter = make_adapter("openai-compatible", {"base_url": fake_server.base_url + "/v1", "model": "m"})
    adapter.open()
    adapter.clean(make_item())
    assert fake_server.last.json["messages"] == [{"role": "user", "content": "um so let's go"}]


def test_hosted_defaults(fake_server: FakeServer):
    local = make_adapter("openai-compatible", base_config(fake_server)).describe()
    assert local.hosted is False and local.api_model_id is None and local.weights_sha256 is None
    hosted = make_adapter(
        "openai-compatible", {"base_url": "https://api.example.com/v1", "model": "m", "system_prompt": "s"}
    ).describe()
    assert hosted.hosted is True and hosted.api_model_id == "m" and hosted.api_date is not None
    assert hosted.open_weights is False


def test_errors_become_adapter_errors(fake_server: FakeServer):
    adapter = make_adapter("openai-compatible", base_config(fake_server))
    adapter.open()
    fake_server.responder = lambda req: (500, {"error": "boom"})
    with pytest.raises(AdapterError, match="HTTP 500"):
        adapter.clean(make_item())
    fake_server.responder = lambda req: (200, b"{not json")
    with pytest.raises(AdapterError, match="not valid JSON"):
        adapter.clean(make_item())
    fake_server.responder = lambda req: (200, {"choices": []})
    with pytest.raises(AdapterError, match="choices"):
        adapter.clean(make_item())
    fake_server.stop()
    with pytest.raises(AdapterError, match="cannot reach|transport"):
        adapter.clean(make_item())


def test_null_content_is_empty_with_warning(fake_server: FakeServer):
    fake_server.responder = lambda req: (200, chat_response(None, finish="length"))
    adapter = make_adapter("openai-compatible", base_config(fake_server))
    adapter.open()
    out = adapter.clean(make_item())
    assert out.output_text == ""
    assert any("null" in w for w in out.warnings) and any("max_tokens" in w for w in out.warnings)


def test_config_errors(fake_server: FakeServer, monkeypatch):
    with pytest.raises(AdapterConfigError, match="model"):
        make_adapter("openai-compatible", {"base_url": "http://127.0.0.1:1/v1"})
    with pytest.raises(AdapterConfigError, match="api_key"):
        make_adapter("openai-compatible", {"base_url": "http://127.0.0.1:1/v1", "model": "m", "api_key": "x"})
    with pytest.raises(AdapterConfigError, match="vocabulary_policy"):
        make_adapter("openai-compatible", base_config(fake_server, vocabulary_policy="magic"))
    monkeypatch.delenv("MISSING_KEY_ENV", raising=False)
    adapter = make_adapter("openai-compatible", base_config(fake_server, api_key_env="MISSING_KEY_ENV"))
    with pytest.raises(AdapterConfigError, match="MISSING_KEY_ENV"):
        adapter.open()


def test_secret_never_in_error_message(fake_server: FakeServer, monkeypatch):
    monkeypatch.setenv("FAKE_KEY_ENV", SECRET)
    fake_server.responder = lambda req: (401, {"error": "bad key"})
    adapter = make_adapter("openai-compatible", base_config(fake_server, api_key_env="FAKE_KEY_ENV"))
    adapter.open()
    with pytest.raises(AdapterError) as exc:
        adapter.clean(make_item())
    assert SECRET not in str(exc.value)
