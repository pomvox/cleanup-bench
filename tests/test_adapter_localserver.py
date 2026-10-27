"""Pomvox LocalServer adapter against an in-process fake speaking protocol v1 (engine docs/cloud.md)."""

from __future__ import annotations

import json
import uuid

import pytest
from conftest import FakeServer, Recorded, make_item

from cleanupbench.adapters import make_adapter
from cleanupbench.adapters.base import AdapterConfigError, AdapterError
from cleanupbench.adapters.pomvox_localserver import PROMPT_SHA256_IN_PACK

TOKEN = "localserver-test-token-do-not-leak"
STATUS = {
    "cleanupPack": "simplewords-v3",
    "cleanupPackVersion": "0.1.0-preview",
    "cleanupRuntime": "pomvox-local-server/mlx",
    "diarizerPack": "pyannote-community1-coreml",
    "diarizerPackVersion": "1.0.0",
    "diarizerRuntime": "fluid",
    "speechRecognition": "not loaded",
    "protocols": ["cleanup/1 POST /v1/clean"],
}


def result_for(req: Recorded, text: str, status: dict, edits: list | None = None, warnings: list | None = None):
    body = req.json
    return {
        "schemaVersion": 1,
        "requestID": body["requestID"],
        "result": {
            "text": text,
            "edits": edits or [],
            "status": status,
            "provenance": {
                "packID": body["pack"]["id"],
                "packVersion": body["pack"]["version"],
                "artifactDigest": "d",
                "modelRevision": "r",
                "runtime": "pomvox-local-server/mlx",
                "route": "cloud",
                "settings": {},
            },
            "timings": {"totalMS": 7, "budgetMS": body["remainingMilliseconds"]},
            "warnings": warnings or [],
        },
    }


def responder(clean):
    def respond(req: Recorded):
        if req.method == "GET" and req.path == "/v1/status":
            return 200, STATUS
        if req.method == "POST" and req.path == "/v1/clean":
            return clean(req)
        return 404, {"error": "no route"}

    return respond


def config(server: FakeServer, **extra) -> dict:
    cfg = {"endpoint": server.base_url + "/v1/clean", "token_env": "FAKE_LOCALSERVER_TOKEN"}
    cfg.update(extra)
    return cfg


@pytest.fixture
def token(monkeypatch):
    monkeypatch.setenv("FAKE_LOCALSERVER_TOKEN", TOKEN)
    return TOKEN


def test_open_checks_status_then_clean_request_shape(fake_server: FakeServer, token):
    fake_server.responder = responder(
        lambda req: (
            200,
            result_for(req, "Let's go.", {"cleaned": {}}, edits=[{"start": 0, "end": 14, "replacement": "Let's go."}]),
        )
    )
    adapter = make_adapter("pomvox-localserver", config(fake_server))
    adapter.open()
    assert fake_server.requests[0].method == "GET" and fake_server.requests[0].path == "/v1/status"
    assert "authorization" not in fake_server.requests[0].headers

    out = adapter.clean(make_item(vocabulary=("Pomvox",)))
    req = fake_server.last
    assert req.method == "POST" and req.path == "/v1/clean"
    assert req.headers["authorization"] == f"Bearer {TOKEN}"
    assert req.headers["content-type"] == "application/json"
    body = req.json
    uuid.UUID(body["requestID"])  # a UUID
    assert req.headers["idempotency-key"] == body["requestID"]
    assert body == {
        "schemaVersion": 1,
        "requestID": body["requestID"],
        "pack": {"id": "simplewords-v3", "version": "0.1.0-preview"},
        "text": "um so let's go",
        "vocabulary": ["Pomvox"],
        "context": "",
        "settings": {},
        "remainingMilliseconds": 30000,
    }
    # A fresh requestID per request.
    adapter.clean(make_item())
    assert fake_server.last.json["requestID"] != body["requestID"]

    assert out.output_text == "Let's go." and out.outcome == "cleaned" and out.fallback_reason is None
    assert out.edits == ({"start": 0, "end": 14, "replacement": "Let's go."},)
    assert out.warnings == ()
    assert out.latency_ms is not None and out.latency_ms >= 0
    assert out.raw is not None and json.loads(out.raw)["result"]["text"] == "Let's go."

    desc = adapter.describe()
    assert desc.hosted is False and desc.open_weights is True and desc.gated_download is True
    assert desc.license == "Apache-2.0"
    assert desc.model_id == "abhiram3040/simplewords-dictation-cleanup-v3"
    assert desc.model_revision == "b1f7ac8282ce060e4ad1374cb9a34750e31723c1"
    assert desc.weights_sha256 == "dbe5a5cdc26d383eaf3f7a009d41a746ec2a99ed262095c1ab9146870090240c"
    assert desc.prompt_text == ""
    assert desc.adapter_config["prompt"] == "pack:system_v2.txt"
    assert desc.adapter_config["prompt_sha256_in_pack"] == PROMPT_SHA256_IN_PACK
    assert desc.adapter_config["server_status"] == STATUS
    assert desc.adapter_config["token_env"] == "FAKE_LOCALSERVER_TOKEN"
    assert desc.adapter_config["status_endpoint"] == fake_server.base_url + "/v1/status"
    assert desc.vocabulary_policy == {"source": "item", "rendering": "protocol v1 vocabulary field"}
    assert TOKEN not in json.dumps(desc.__dict__, default=str)


def test_status_mapping_unchanged_and_fallback_rejected(fake_server: FakeServer, token):
    fake_server.responder = responder(lambda req: (200, result_for(req, req.json["text"], {"unchanged": {}})))
    adapter = make_adapter("pomvox-localserver", config(fake_server))
    adapter.open()
    out = adapter.clean(make_item())
    assert out.outcome == "unchanged" and out.output_text == "um so let's go" and out.edits == ()

    fake_server.responder = responder(
        lambda req: (
            200,
            result_for(
                req, req.json["text"], {"fallback": {"_0": "rejected"}}, warnings=["rejectedBy:shortWordOverlap"]
            ),
        )
    )
    out = adapter.clean(make_item())
    assert out.outcome == "fallback" and out.fallback_reason == "rejected"
    assert out.output_text == "um so let's go"
    assert out.warnings == ("rejectedBy:shortWordOverlap",)  # verbatim (decision S5)
    assert out.edits == ()

    timed_out = {"fallback": {"_0": "timedOut"}}
    fake_server.responder = responder(lambda req: (200, result_for(req, req.json["text"], timed_out)))
    out = adapter.clean(make_item())
    assert out.outcome == "fallback" and out.fallback_reason == "timedOut"


def test_protocol_errors(fake_server: FakeServer, token):
    fake_server.responder = responder(lambda req: (200, result_for(req, "x", {"cleaned": {}})))
    adapter = make_adapter("pomvox-localserver", config(fake_server))
    adapter.open()

    def wrong_id(req):
        r = result_for(req, "x", {"cleaned": {}})
        r["requestID"] = "00000000-0000-0000-0000-000000000000"
        return 200, r

    fake_server.responder = responder(wrong_id)
    with pytest.raises(AdapterError, match="requestID"):
        adapter.clean(make_item())

    def wrong_schema(req):
        r = result_for(req, "x", {"cleaned": {}})
        r["schemaVersion"] = 2
        return 200, r

    fake_server.responder = responder(wrong_schema)
    with pytest.raises(AdapterError, match="schemaVersion"):
        adapter.clean(make_item())

    fake_server.responder = responder(lambda req: (200, result_for(req, "x", {"invented": {}})))
    with pytest.raises(AdapterError, match="status"):
        adapter.clean(make_item())

    fake_server.responder = responder(lambda req: (500, {"error": "boom"}))
    with pytest.raises(AdapterError, match="HTTP 500") as exc:
        adapter.clean(make_item())
    assert TOKEN not in str(exc.value)

    fake_server.responder = responder(lambda req: (200, b"{truncated"))
    with pytest.raises(AdapterError, match="not valid JSON"):
        adapter.clean(make_item())

    fake_server.responder = responder(lambda req: (400, "this server serves pack other 9.9.9"))
    with pytest.raises(AdapterError, match="HTTP 400"):
        adapter.clean(make_item())


def test_open_refuses_wrong_pack(fake_server: FakeServer, token):
    other = dict(STATUS, cleanupPack="other-pack")
    fake_server.responder = lambda req: (200, other)
    adapter = make_adapter("pomvox-localserver", config(fake_server))
    with pytest.raises(AdapterConfigError, match="other-pack"):
        adapter.open()
    fake_server.responder = lambda req: (200, dict(STATUS, cleanupPackVersion="0.2.0"))
    with pytest.raises(AdapterConfigError, match="0.2.0"):
        adapter.open()
    adapter2 = make_adapter("pomvox-localserver", config(fake_server, pack_version="0.2.0"))
    adapter2.open()  # the config can name the served pack
    assert adapter2.describe().adapter_config["pack_version"] == "0.2.0"


def test_open_requires_token_and_reachable_server(fake_server: FakeServer, monkeypatch):
    monkeypatch.delenv("FAKE_LOCALSERVER_TOKEN", raising=False)
    adapter = make_adapter("pomvox-localserver", config(fake_server))
    with pytest.raises(AdapterConfigError, match="FAKE_LOCALSERVER_TOKEN"):
        adapter.open()
    monkeypatch.setenv("FAKE_LOCALSERVER_TOKEN", TOKEN)
    fake_server.stop()
    with pytest.raises(AdapterConfigError, match="status check failed"):
        adapter.open()
    with pytest.raises(AdapterConfigError, match="token"):
        make_adapter("pomvox-localserver", {"token": "x"})
