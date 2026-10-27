"""Prompt and vocabulary rendering shared by the prompt-driven adapters.

One prompt per system, fixed across all items (docs/spec.md section 2.4). The
only per-item material is the transcript and, when the policy says so, the
item's own vocabulary list (`vocabulary_policy` in the manifest, section 9).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cleanupbench.adapters.base import AdapterConfigError
from cleanupbench.items import Item

VOCABULARY_POLICIES: tuple[str, ...] = ("none", "system-suffix")
VOCABULARY_LINE_PREFIX = "Vocabulary: "


def load_prompt_text(config: dict[str, Any], *, required: bool = True) -> str:
    """The system prompt from `system_prompt` or `system_prompt_file` (relative to the working directory)."""
    text = config.get("system_prompt")
    path = config.get("system_prompt_file")
    if text is not None and path is not None:
        raise AdapterConfigError("set either system_prompt or system_prompt_file, not both")
    if text is not None:
        if not isinstance(text, str):
            raise AdapterConfigError("system_prompt must be a string")
        return text
    if path is not None:
        try:
            return Path(path).read_text("utf-8")
        except OSError as exc:
            raise AdapterConfigError(f"system_prompt_file {path!r} cannot be read: {exc}") from exc
    if required:
        raise AdapterConfigError("a system_prompt or system_prompt_file is required")
    return ""


def vocabulary_line(item: Item) -> str:
    """`Vocabulary: a, b, c`; empty when the item has no vocabulary."""
    if not item.vocabulary:
        return ""
    return VOCABULARY_LINE_PREFIX + ", ".join(item.vocabulary)


def check_vocabulary_policy(policy: str) -> str:
    if policy not in VOCABULARY_POLICIES:
        raise AdapterConfigError(f"vocabulary_policy must be one of {', '.join(VOCABULARY_POLICIES)}, not {policy!r}")
    return policy


def with_control_line(system_prompt: str, control_line: str | None) -> str:
    """The fixed system prompt with the control line appended on its own line (decision 12)."""
    if not control_line:
        return system_prompt
    if system_prompt == "":
        return control_line
    return system_prompt.rstrip("\n") + "\n" + control_line


def with_vocabulary(system_prompt: str, item: Item, policy: str) -> str:
    """Per item: the prompt with the vocabulary line appended when the policy is `system-suffix`."""
    if policy != "system-suffix":
        return system_prompt
    line = vocabulary_line(item)
    if not line:
        return system_prompt
    if system_prompt == "":
        return line
    return system_prompt.rstrip("\n") + "\n" + line


def render_user(template: str, item: Item) -> str:
    """The user turn: `{input}` is the transcript; `{vocabulary}` is the comma-joined list (empty when none)."""
    try:
        return template.format(input=item.input, vocabulary=", ".join(item.vocabulary))
    except (KeyError, IndexError, ValueError) as exc:
        raise AdapterConfigError(f"user_template {template!r} is not valid: {exc}") from exc


def describe_vocabulary_policy(policy: str, user_template: str = "{input}") -> dict[str, str]:
    """The manifest's `vocabulary_policy` object."""
    renderings: list[str] = []
    if policy == "system-suffix":
        renderings.append(
            f"'{VOCABULARY_LINE_PREFIX}a, b, c' appended to the system prompt on its own line "
            "when the item has vocabulary"
        )
    if "{vocabulary}" in user_template:
        renderings.append("the comma-joined list substituted for {vocabulary} in the user template")
    if not renderings:
        return {"source": "none", "rendering": ""}
    return {"source": "item", "rendering": "; ".join(renderings)}
