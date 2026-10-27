"""The Anthropic Messages adapter: the hosted generic-cloud row (decision 10, S4).

Plain urllib against `POST {base_url}/v1/messages`. The key comes from the
environment variable named by `api_key_env` and is never written anywhere.
Hosted rows carry `api_model_id` and `api_date` instead of a weights hash.
"""

from __future__ import annotations

import os
from typing import Any

from cleanupbench.adapters._http import request_json, today_utc
from cleanupbench.adapters._prompting import (
    check_vocabulary_policy,
    describe_vocabulary_policy,
    load_prompt_text,
    render_user,
    with_control_line,
    with_vocabulary,
)
from cleanupbench.adapters.base import Adapter, AdapterConfigError, AdapterError, CleanOutput, SystemDescription
from cleanupbench.items import Item

DEFAULT_BASE_URL = "https://api.anthropic.com"
DEFAULT_API_KEY_ENV = "ANTHROPIC_API_KEY"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TIMEOUT_S = 120.0
SECRET_KEYS: tuple[str, ...] = ("api_key", "token", "authorization")


class AnthropicAdapter(Adapter):
    name = "anthropic"
    version = "1"

    def __init__(self, config: dict[str, Any]) -> None:
        for key in SECRET_KEYS:
            if key in config:
                raise AdapterConfigError(f"{key!r} must not be in the adapter config; use api_key_env")
        try:
            self.model = str(config["model"])
        except KeyError:
            raise AdapterConfigError("anthropic adapter config is missing 'model'") from None
        self.base_url = str(config.get("base_url", DEFAULT_BASE_URL)).rstrip("/")
        self.api_key_env = str(config.get("api_key_env", DEFAULT_API_KEY_ENV))
        self.user_template = str(config.get("user_template", "{input}"))
        self.control_line: str | None = config.get("control_line")
        self.vocabulary_policy = check_vocabulary_policy(str(config.get("vocabulary_policy", "none")))
        self.max_tokens = int(config.get("max_tokens", DEFAULT_MAX_TOKENS))
        self.timeout_s = float(config.get("timeout_s", DEFAULT_TIMEOUT_S))
        # `temperature: 0` is what the manifest records (schema: const 0). Some model generations reject a
        # non-default temperature; `send_temperature: false` omits the field from the request only.
        self.send_temperature = bool(config.get("send_temperature", True))
        self.extra_body: dict[str, Any] = dict(config.get("extra_body") or {})
        self.license = str(config.get("license", "proprietary"))
        self.model_revision = str(config.get("model_revision", self.model))
        self._config = config
        self._system_prompt_text = load_prompt_text(config, required=True)
        self._api_key: str | None = None

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> AnthropicAdapter:
        return cls(config)

    def open(self) -> None:
        value = os.environ.get(self.api_key_env)
        if not value:
            raise AdapterConfigError(f"environment variable {self.api_key_env} is not set")
        self._api_key = value

    def close(self) -> None:
        self._api_key = None

    @property
    def system_prompt(self) -> str:
        return with_control_line(self._system_prompt_text, self.control_line)

    def request_body(self, item: Item) -> dict[str, Any]:
        body: dict[str, Any] = dict(self.extra_body)
        body.update(
            {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "system": with_vocabulary(self.system_prompt, item, self.vocabulary_policy),
                "messages": [{"role": "user", "content": render_user(self.user_template, item)}],
            }
        )
        if self.send_temperature:
            body["temperature"] = 0
        return body

    def describe(self) -> SystemDescription:
        decoding: dict[str, Any] = {"strategy": "greedy", "temperature": 0, "max_tokens": self.max_tokens}
        thinking = self.extra_body.get("thinking")
        if not isinstance(thinking, dict) or thinking.get("type") in ("disabled", "between_tools"):
            decoding["thinking"] = False
        adapter_config = {k: v for k, v in self._config.items() if k not in SECRET_KEYS}
        adapter_config["endpoint"] = f"{self.base_url}/v1/messages"
        adapter_config["api_key_env"] = self.api_key_env
        adapter_config["anthropic_version"] = ANTHROPIC_VERSION
        return SystemDescription(
            model_id=self.model,
            model_revision=self.model_revision,
            open_weights=False,
            license=self.license,
            params_total=None,
            params_total_note="not published",
            api_model_id=self.model,
            api_date=today_utc(),
            hosted=True,
            prompt_text=self.system_prompt,
            control_line=self.control_line,
            decoding=decoding,
            vocabulary_policy=describe_vocabulary_policy(self.vocabulary_policy, self.user_template),
            adapter_config=adapter_config,
        )

    def clean(self, item: Item) -> CleanOutput:
        if not self._api_key:
            raise AdapterError("adapter is not open (no API key loaded)")
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        result = request_json(
            f"{self.base_url}/v1/messages", body=self.request_body(item), headers=headers, timeout_s=self.timeout_s
        )
        payload = result.json()
        blocks = payload.get("content") if isinstance(payload, dict) else None
        if not isinstance(blocks, list):
            raise AdapterError("response has no content list")
        texts: list[str] = []
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if not isinstance(text, str):
                    raise AdapterError("text block without string text")
                texts.append(text)
        content = "".join(texts)
        warnings: list[str] = []
        stop = payload.get("stop_reason")
        if stop == "max_tokens":
            warnings.append("stop_reason=max_tokens: output hit max_tokens")
        elif stop == "refusal":
            warnings.append("stop_reason=refusal")
        return CleanOutput(
            output_text=content,
            outcome=CleanOutput.derive_outcome(item.input, content),
            warnings=tuple(warnings),
            latency_ms=round(result.latency_ms, 3),
            raw=result.body,
        )
