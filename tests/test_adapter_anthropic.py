"""Anthropic Messages adapter against an in-process fake /v1/messages server."""

from __future__ import annotations

import json
import re

import pytest
from conftest import FakeServer, make_item

from cleanupbench.adapters import make_adapter
from cleanupbench.adapters.base import AdapterConfigError, AdapterError

SECRET = "sk-ant-test-secret-value-do-not-leak"


def messages_response(blocks: list[dict], stop: str = "end_turn") -> dict:
    return {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": "fake",
        "content": blocks,
        "stop_reason": stop,
        "usage": {"input_tokens": 1, "output_tokens": 1},
    }


def config(server: FakeServer, **extra) -> dict:
    cfg = {"model": "claude-fake", "base_url": server.base_url, "api_key_env": "FAKE_ANTHROPIC_KEY"}
    cfg["system_prompt"] = "Clean the dictation."
    cfg.update(extra)
    return cfg


def test_request_shape_headers_and_output(fake_server: FakeServer, monkeypatch):
    monkeypatch.setenv("FAKE_ANTHROPIC_KEY", SECRET)
    fake_server.responder = lambda req: (
        200,
        messages_response([{"type": "text", "text": "Let's "}, {"type": "text", "text": "go."}]),
    )
    adapter = make_adapter("anthropic", config(fake_server, control_line="[tone: neutral]", max_tokens=99))
    adapter.open()
    out = adapter.clean(make_item())
    adapter.close()

    req = fake_server.last
    assert req.method == "POST" and req.path == "/v1/messages"
    assert req.headers["x-api-key"] == SECRET
    assert req.headers["anthropic-version"] == "2023-06-01"
    assert req.headers["content-type"] == "application/json"
    assert "authorization" not in req.headers
    body = req.json
    assert body == {
        "model": "claude-fake",
        "max_tokens": 99,
        "temperature": 0,
        "system": "Clean the dictation.\n[tone: neutral]",
        "messages": [{"role": "user", "content": "um so let's go"}],
    }

    assert out.output_text == "Let's go."  # text blocks concatenated
    assert out.outcome == "cleaned"
    assert out.latency_ms is not None and out.latency_ms >= 0
    assert out.raw is not None and json.loads(out.raw)["id"] == "msg_1"

    desc = adapter.describe()
    assert desc.hosted is True and desc.open_weights is False and desc.license == "proprietary"
    assert desc.api_model_id == "claude-fake" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", desc.api_date or "")
    assert desc.params_total is None and desc.params_total_note == "not published"
    assert desc.decoding == {"strategy": "greedy", "temperature": 0, "max_tokens": 99, "thinking": False}
    assert desc.control_line == "[tone: neutral]" and desc.prompt_text == "Clean the dictation.\n[tone: neutral]"
    assert desc.adapter_config["api_key_env"] == "FAKE_ANTHROPIC_KEY"
    assert SECRET not in json.dumps(desc.__dict__, default=str)


def test_default_max_tokens_and_api_key_env(fake_server: FakeServer, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", SECRET)
    fake_server.responder = lambda req: (200, messages_response([{"type": "text", "text": "x"}]))
    cfg = {"model": "claude-fake", "base_url": fake_server.base_url, "system_prompt": "s"}
    adapter = make_adapter("anthropic", cfg)
    adapter.open()
    adapter.clean(make_item())
    assert fake_server.last.headers["x-api-key"] == SECRET
    assert fake_server.last.json["max_tokens"] == 1024
    assert adapter.describe().adapter_config["api_key_env"] == "ANTHROPIC_API_KEY"


def test_vocabulary_and_unchanged(fake_server: FakeServer, monkeypatch):
    monkeypatch.setenv("FAKE_ANTHROPIC_KEY", SECRET)
    fake_server.responder = lambda req: (200, messages_response([{"type": "text", "text": "um so let's go"}]))
    adapter = make_adapter("anthropic", config(fake_server, vocabulary_policy="system-suffix"))
    adapter.open()
    out = adapter.clean(make_item(vocabulary=("Pomvox",)))
    assert fake_server.last.json["system"] == "Clean the dictation.\nVocabulary: Pomvox"
    assert out.outcome == "unchanged"
    assert adapter.describe().vocabulary_policy["source"] == "item"


def test_send_temperature_false_omits_field_but_manifest_records_zero(fake_server: FakeServer, monkeypatch):
    monkeypatch.setenv("FAKE_ANTHROPIC_KEY", SECRET)
    fake_server.responder = lambda req: (200, messages_response([{"type": "text", "text": "x"}]))
    adapter = make_adapter("anthropic", config(fake_server, send_temperature=False))
    adapter.open()
    adapter.clean(make_item())
    assert "temperature" not in fake_server.last.json
    assert adapter.describe().decoding["temperature"] == 0


def test_non_text_blocks_are_ignored_and_stop_reasons_warn(fake_server: FakeServer, monkeypatch):
    monkeypatch.setenv("FAKE_ANTHROPIC_KEY", SECRET)
    fake_server.responder = lambda req: (
        200,
        messages_response([{"type": "thinking", "thinking": ""}, {"type": "text", "text": "Go."}], stop="max_tokens"),
    )
    adapter = make_adapter("anthropic", config(fake_server))
    adapter.open()
    out = adapter.clean(make_item())
    assert out.output_text == "Go."
    assert any("max_tokens" in w for w in out.warnings)


def test_errors(fake_server: FakeServer, monkeypatch):
    monkeypatch.setenv("FAKE_ANTHROPIC_KEY", SECRET)
    adapter = make_adapter("anthropic", config(fake_server))
    adapter.open()
    fake_server.responder = lambda req: (500, {"type": "error", "error": {"type": "api_error", "message": "boom"}})
    with pytest.raises(AdapterError, match="HTTP 500") as exc:
        adapter.clean(make_item())
    assert SECRET not in str(exc.value)
    fake_server.responder = lambda req: (200, b"<html>")
    with pytest.raises(AdapterError, match="not valid JSON"):
        adapter.clean(make_item())
    fake_server.responder = lambda req: (200, {"id": "x"})
    with pytest.raises(AdapterError, match="content"):
        adapter.clean(make_item())


def test_config_and_key_errors(fake_server: FakeServer, monkeypatch):
    with pytest.raises(AdapterConfigError, match="model"):
        make_adapter("anthropic", {"system_prompt": "s"})
    with pytest.raises(AdapterConfigError, match="api_key"):
        make_adapter("anthropic", {"model": "m", "system_prompt": "s", "api_key": "x"})
    with pytest.raises(AdapterConfigError, match="system_prompt"):
        make_adapter("anthropic", {"model": "m"})
    monkeypatch.delenv("FAKE_ANTHROPIC_KEY", raising=False)
    adapter = make_adapter("anthropic", config(fake_server))
    with pytest.raises(AdapterConfigError, match="FAKE_ANTHROPIC_KEY"):
        adapter.open()
    with pytest.raises(AdapterError, match="not open"):
        adapter.clean(make_item())
