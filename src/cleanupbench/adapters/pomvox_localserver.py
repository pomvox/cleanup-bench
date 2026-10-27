"""The Pomvox LocalServer adapter: SimpleWords v3 through the engine's own wire protocol (decision 19, S5, S6).

Talks protocol version 1 (`docs/cloud.md` in the engine repository) to
`Examples/LocalServer`'s `POST /v1/clean`. The engine returns outcomes and
byte-offset edits; both are stored as returned. A guard rejection surfaces as
`fallback` with the engine's `rejectedBy:` warning kept verbatim (S5); the
edits are checked for accountability only (S6). The prompt lives inside the
pack, so the manifest records its in-pack hash instead of its text.
"""

from __future__ import annotations

import os
import urllib.parse
import uuid
from typing import Any

from cleanupbench.adapters._http import request_json
from cleanupbench.adapters.base import Adapter, AdapterConfigError, AdapterError, CleanOutput, SystemDescription
from cleanupbench.items import Item

DEFAULT_ENDPOINT = "http://127.0.0.1:8787/v1/clean"
DEFAULT_TOKEN_ENV = "POMVOX_LOCALSERVER_TOKEN"
DEFAULT_PACK_ID = "simplewords-v3"
DEFAULT_PACK_VERSION = "0.1.0-preview"
DEFAULT_REMAINING_MS = 30000
DEFAULT_MODEL_ID = "abhiram3040/simplewords-dictation-cleanup-v3"
DEFAULT_MODEL_REVISION = "b1f7ac8282ce060e4ad1374cb9a34750e31723c1"
# pack.json digest of model.safetensors
DEFAULT_WEIGHTS_SHA256 = "dbe5a5cdc26d383eaf3f7a009d41a746ec2a99ed262095c1ab9146870090240c"
PROMPT_IN_PACK = "pack:system_v2.txt"
# pack.json digest of system_v2.txt; the bench does not have the text
PROMPT_SHA256_IN_PACK = "86ce80cbb40bb02b69cad54d6a48c2b38f5f08ab4fb0c462f615ce02a7fc2d5b"
DEFAULT_LICENSE = "Apache-2.0"
DEFAULT_PARAMS_NOTE = "2B per the model card; exact count not published"
DEFAULT_TIMEOUT_S = 180.0
PROTOCOL_SCHEMA_VERSION = 1


def _status_endpoint(endpoint: str) -> str:
    parts = urllib.parse.urlsplit(endpoint)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, "/v1/status", "", ""))


class PomvoxLocalServerAdapter(Adapter):
    name = "pomvox-localserver"
    version = "1"

    def __init__(self, config: dict[str, Any]) -> None:
        if "token" in config:
            raise AdapterConfigError("'token' must not be in the adapter config; name an env var in token_env")
        self.endpoint = str(config.get("endpoint", DEFAULT_ENDPOINT))
        self.status_endpoint = str(config.get("status_endpoint") or _status_endpoint(self.endpoint))
        self.token_env = str(config.get("token_env", DEFAULT_TOKEN_ENV))
        self.pack_id = str(config.get("pack_id", DEFAULT_PACK_ID))
        self.pack_version = str(config.get("pack_version", DEFAULT_PACK_VERSION))
        self.remaining_ms = int(config.get("remaining_ms", DEFAULT_REMAINING_MS))
        self.timeout_s = float(config.get("timeout_s", max(DEFAULT_TIMEOUT_S, self.remaining_ms / 1000.0 + 30.0)))
        self.model_id = str(config.get("model_id", DEFAULT_MODEL_ID))
        self.model_revision = str(config.get("model_revision", DEFAULT_MODEL_REVISION))
        self.weights_sha256 = str(config.get("weights_sha256", DEFAULT_WEIGHTS_SHA256))
        self.license = str(config.get("license", DEFAULT_LICENSE))
        self.gated_download = bool(config.get("gated_download", True))
        self.params_total: int | None = config.get("params_total")
        self.params_total_note = str(config.get("params_total_note", DEFAULT_PARAMS_NOTE))
        self.prompt_sha256_in_pack = str(config.get("prompt_sha256_in_pack", PROMPT_SHA256_IN_PACK))
        self._config = config
        self._token: str | None = None
        self._server_status: dict[str, Any] | None = None

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> PomvoxLocalServerAdapter:
        return cls(config)

    # -- lifecycle -----------------------------------------------------------------------------------------------

    def open(self) -> None:
        token = os.environ.get(self.token_env)
        if not token:
            raise AdapterConfigError(f"environment variable {self.token_env} is not set (the LocalServer prints it)")
        self._token = token
        try:
            status = request_json(self.status_endpoint, method="GET", timeout_s=self.timeout_s).json()
        except AdapterError as exc:
            raise AdapterConfigError(f"LocalServer status check failed: {exc}") from None
        if not isinstance(status, dict):
            raise AdapterConfigError(f"{self.status_endpoint}: status is not a JSON object")
        served = (status.get("cleanupPack"), status.get("cleanupPackVersion"))
        if served != (self.pack_id, self.pack_version):
            raise AdapterConfigError(
                f"LocalServer serves pack {served[0]} {served[1]}; this row is configured for "
                f"{self.pack_id} {self.pack_version}"
            )
        self._server_status = status

    def close(self) -> None:
        self._token = None

    # -- the interface -------------------------------------------------------------------------------------------

    def describe(self) -> SystemDescription:
        adapter_config = {k: v for k, v in self._config.items() if k != "token"}
        adapter_config.update(
            {
                "endpoint": self.endpoint,
                "status_endpoint": self.status_endpoint,
                "token_env": self.token_env,
                "pack_id": self.pack_id,
                "pack_version": self.pack_version,
                "remaining_ms": self.remaining_ms,
                "prompt": PROMPT_IN_PACK,
                "prompt_sha256_in_pack": self.prompt_sha256_in_pack,
                "decoding_note": "fixed by the pack and the engine; not configurable through protocol v1",
                "transforms": "none",
                "server_status": self._server_status,
            }
        )
        return SystemDescription(
            model_id=self.model_id,
            model_revision=self.model_revision,
            open_weights=True,
            license=self.license,
            params_total=self.params_total,
            params_total_note=self.params_total_note,
            weights_sha256=self.weights_sha256,
            hosted=False,
            gated_download=self.gated_download,
            prompt_text="",
            decoding={"strategy": "greedy", "temperature": 0, "max_tokens": None},
            vocabulary_policy={"source": "item", "rendering": "protocol v1 vocabulary field"},
            adapter_config=adapter_config,
        )

    def request_body(self, item: Item, request_id: str) -> dict[str, Any]:
        return {
            "schemaVersion": PROTOCOL_SCHEMA_VERSION,
            "requestID": request_id,
            "pack": {"id": self.pack_id, "version": self.pack_version},
            "text": item.input,
            "vocabulary": list(item.vocabulary),
            "context": "",
            "settings": {},
            "remainingMilliseconds": self.remaining_ms,
        }

    def clean(self, item: Item) -> CleanOutput:
        if not self._token:
            raise AdapterError("adapter is not open (no token loaded)")
        request_id = str(uuid.uuid4())
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Idempotency-Key": request_id,
        }
        result = request_json(
            self.endpoint, body=self.request_body(item, request_id), headers=headers, timeout_s=self.timeout_s
        )
        payload = result.json()
        if not isinstance(payload, dict):
            raise AdapterError("response is not a JSON object")
        if payload.get("schemaVersion") != PROTOCOL_SCHEMA_VERSION:
            raise AdapterError(f"response schemaVersion {payload.get('schemaVersion')!r} != {PROTOCOL_SCHEMA_VERSION}")
        if payload.get("requestID") != request_id:
            raise AdapterError("response requestID does not match the request")
        res = payload.get("result")
        if not isinstance(res, dict):
            raise AdapterError("response has no result object")
        try:
            text = res["text"]
            status = res["status"]
        except KeyError as exc:
            raise AdapterError(f"result is missing {exc.args[0]!r}") from None
        if not isinstance(text, str):
            raise AdapterError("result.text is not a string")
        outcome, reason = _map_status(status)
        edits = tuple(_edit(e) for e in (res.get("edits") or []))
        warnings = tuple(str(w) for w in (res.get("warnings") or []))
        return CleanOutput(
            output_text=text,
            outcome=outcome,
            fallback_reason=reason,
            edits=edits,
            warnings=warnings,
            latency_ms=round(result.latency_ms, 3),
            raw=result.body,
        )


def _map_status(status: Any) -> tuple[str, str | None]:
    """{"cleaned": {}} -> cleaned; {"unchanged": {}} -> unchanged; {"fallback": {"_0": reason}} -> fallback."""
    if not isinstance(status, dict) or len(status) != 1:
        raise AdapterError(f"unrecognized result.status {status!r}")
    (kind, detail), = status.items()
    if kind == "cleaned":
        return "cleaned", None
    if kind == "unchanged":
        return "unchanged", None
    if kind == "fallback":
        reason = detail.get("_0") if isinstance(detail, dict) else None
        return "fallback", str(reason) if reason is not None else "unspecified"
    raise AdapterError(f"unrecognized result.status kind {kind!r}")


def _edit(edit: Any) -> dict[str, Any]:
    try:
        return {"start": int(edit["start"]), "end": int(edit["end"]), "replacement": str(edit["replacement"])}
    except (KeyError, TypeError, ValueError) as exc:
        raise AdapterError(f"malformed edit {edit!r}: {exc.__class__.__name__}") from None
