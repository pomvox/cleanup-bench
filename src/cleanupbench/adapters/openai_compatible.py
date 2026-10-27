"""The OpenAI-compatible chat adapter (decision 19).

Covers `llama-server`, `mlx_lm.server`, Ollama, LM Studio and any hosted
provider that speaks `POST {base_url}/chat/completions`. Plain urllib, no
SDK. Temperature is always 0; `extra_body` carries server-specific switches
such as `{"chat_template_kwargs": {"enable_thinking": false}}` (S1-mini,
decision 12). The adapter stores the raw response body and never applies a
guard (decision S5).
"""

from __future__ import annotations

import os
from typing import Any

from cleanupbench.adapters._http import is_loopback, request_json, today_utc
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

DEFAULT_MAX_TOKENS = 512
DEFAULT_TIMEOUT_S = 120.0
SECRET_KEYS: tuple[str, ...] = ("api_key", "token", "authorization")


def _reject_inline_secrets(config: dict[str, Any]) -> None:
    for key in SECRET_KEYS:
        if key in config:
            raise AdapterConfigError(f"{key!r} must not be in the adapter config; name an environment variable instead")


def _thinking_disabled(extra_body: dict[str, Any]) -> bool:
    kwargs = extra_body.get("chat_template_kwargs")
    if isinstance(kwargs, dict) and kwargs.get("enable_thinking") is False:
        return True
    return extra_body.get("enable_thinking") is False


class OpenAICompatibleAdapter(Adapter):
    name = "openai-compatible"
    version = "1"

    def __init__(self, config: dict[str, Any]) -> None:
        _reject_inline_secrets(config)
        try:
            self.base_url = str(config["base_url"]).rstrip("/")
            self.model = str(config["model"])
        except KeyError as exc:
            raise AdapterConfigError(f"openai-compatible adapter config is missing {exc.args[0]!r}") from None
        self.api_key_env: str | None = config.get("api_key_env")
        self.user_template: str = str(config.get("user_template", "{input}"))
        self.control_line: str | None = config.get("control_line")
        self.vocabulary_policy = check_vocabulary_policy(str(config.get("vocabulary_policy", "none")))
        self.max_tokens = int(config.get("max_tokens", DEFAULT_MAX_TOKENS))
        self.extra_body: dict[str, Any] = dict(config.get("extra_body") or {})
        self.timeout_s = float(config.get("timeout_s", DEFAULT_TIMEOUT_S))
        self.seed: int | None = config.get("seed")
        self.hosted = bool(config.get("hosted", not is_loopback(self.base_url)))
        self.model_revision = str(config.get("model_revision", "unknown"))
        self.weights_sha256: str | None = config.get("weights_sha256")
        self.open_weights = bool(config.get("open_weights", not self.hosted))
        self.license = str(config.get("license", "unknown"))
        self.params_total: int | None = config.get("params_total")
        default_note = "" if self.params_total is not None else "unknown"
        self.params_total_note = str(config.get("params_total_note", default_note))
        self.gated_download = bool(config.get("gated_download", False))
        self._config = config
        self._system_prompt_text = load_prompt_text(config, required=False)
        self._api_key: str | None = None

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> OpenAICompatibleAdapter:
        return cls(config)

    # -- lifecycle -----------------------------------------------------------------------------------------------

    def open(self) -> None:
        if self.api_key_env:
            value = os.environ.get(self.api_key_env)
            if not value:
                raise AdapterConfigError(f"environment variable {self.api_key_env} is not set")
            self._api_key = value

    def close(self) -> None:
        self._api_key = None

    # -- prompt --------------------------------------------------------------------------------------------------

    @property
    def system_prompt(self) -> str:
        """The fixed system prompt with the control line appended (what the manifest records)."""
        return with_control_line(self._system_prompt_text, self.control_line)

    def messages_for(self, item: Item) -> list[dict[str, str]]:
        system = with_vocabulary(self.system_prompt, item, self.vocabulary_policy)
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": render_user(self.user_template, item)})
        return messages

    def request_body(self, item: Item) -> dict[str, Any]:
        body: dict[str, Any] = dict(self.extra_body)
        body.update(
            {
                "model": self.model,
                "messages": self.messages_for(item),
                "temperature": 0,
                "max_tokens": self.max_tokens,
                "stream": False,
            }
        )
        if self.seed is not None:
            body["seed"] = int(self.seed)
        return body

    # -- the interface -------------------------------------------------------------------------------------------

    def describe(self) -> SystemDescription:
        decoding: dict[str, Any] = {"strategy": "greedy", "temperature": 0, "max_tokens": self.max_tokens}
        if _thinking_disabled(self.extra_body):
            decoding["thinking"] = False
        if self.seed is not None:
            decoding["seed"] = int(self.seed)
        adapter_config = {k: v for k, v in self._config.items() if k not in SECRET_KEYS}
        adapter_config["endpoint"] = f"{self.base_url}/chat/completions"
        return SystemDescription(
            model_id=self.model,
            model_revision=self.model_revision,
            open_weights=self.open_weights,
            license=self.license,
            params_total=self.params_total,
            params_total_note=self.params_total_note,
            weights_sha256=self.weights_sha256,
            api_model_id=self.model if self.hosted else None,
            api_date=today_utc() if self.hosted else None,
            hosted=self.hosted,
            gated_download=self.gated_download,
            prompt_text=self.system_prompt,
            control_line=self.control_line,
            decoding=decoding,
            vocabulary_policy=describe_vocabulary_policy(self.vocabulary_policy, self.user_template),
            adapter_config=adapter_config,
        )

    def clean(self, item: Item) -> CleanOutput:
        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        result = request_json(
            f"{self.base_url}/chat/completions", body=self.request_body(item), headers=headers, timeout_s=self.timeout_s
        )
        payload = result.json()
        warnings: list[str] = []
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AdapterError(f"response has no choices[0].message.content ({exc.__class__.__name__})") from None
        if content is None:
            content = ""
            warnings.append("message.content was null; recorded as empty output")
        if not isinstance(content, str):
            raise AdapterError("message.content is not a string")
        try:
            finish = payload["choices"][0].get("finish_reason")
        except AttributeError:
            finish = None
        if finish == "length":
            warnings.append("finish_reason=length: output hit max_tokens")
        return CleanOutput(
            output_text=content,
            outcome=CleanOutput.derive_outcome(item.input, content),
            warnings=tuple(warnings),
            latency_ms=round(result.latency_ms, 3),
            raw=result.body,
        )
