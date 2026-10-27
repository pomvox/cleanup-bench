"""Tokenizer and normalizers (docs/spec.md section 6.1).

These are part of every metric's definition. Changing them changes scores, so
they are pinned by hand-worked tests in tests/test_text.py and the
SCORER_VERSION is bumped on any change.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

NEWLINE_TOKEN = "⏎"

_QUOTE_MAP = str.maketrans(
    {
        "’": "'",  # right single quotation mark
        "‘": "'",  # left single quotation mark
        "‛": "'",  # single high-reversed-9 quotation mark
        "“": '"',  # left double quotation mark
        "”": '"',  # right double quotation mark
        "‟": '"',  # double high-reversed-9 quotation mark
    }
)

_HORIZONTAL_WS = re.compile(r"[ \t\f\v ]+")
_LINE_WS = re.compile(r"[ \t\f\v ]*\n[ \t\f\v ]*")


def minimal_normalize(text: str) -> str:
    """The minimal normalizer (decision 2).

    Unicode NFC; typographic single and double quotation marks to ASCII; runs
    of horizontal whitespace to one space; whitespace around line breaks
    removed; CRLF and CR to LF; leading and trailing whitespace removed. Case,
    punctuation, contractions and spelling are untouched.
    """
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_QUOTE_MAP)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _HORIZONTAL_WS.sub(" ", text)
    text = _LINE_WS.sub("\n", text)
    return text.strip()


Kind = Literal["word", "punct", "newline"]


@dataclass(frozen=True, slots=True)
class Token:
    text: str
    kind: Kind


# A word token: letters or digits, optionally joined by apostrophes or hyphens
# ("don't", "o'clock", "twenty-five", "3:30" is two words and a punct).
# Any other non-space character is a punctuation token on its own.
_TOKEN_RE = re.compile(
    r"(?P<newline>\n)"
    r"|(?P<word>[^\W_]+(?:['\-][^\W_]+)*)"
    r"|(?P<punct>[^\s\w]|_)",
    re.UNICODE,
)


def tokenize(text: str) -> list[Token]:
    """Split minimally normalized text into word, punctuation and newline tokens.

    The input is normalized first so that callers never see two tokenizations
    of the same text. Whitespace is not a token.
    """
    out: list[Token] = []
    for m in _TOKEN_RE.finditer(minimal_normalize(text)):
        if m.group("newline") is not None:
            out.append(Token(NEWLINE_TOKEN, "newline"))
        elif m.group("word") is not None:
            out.append(Token(m.group("word"), "word"))
        else:
            out.append(Token(m.group("punct"), "punct"))
    return out


def token_texts(text: str) -> list[str]:
    return [t.text for t in tokenize(text)]


def content_tokens(text: str) -> list[str]:
    """Word tokens, lower-cased, with punctuation and line breaks dropped (section 6.1)."""
    return [t.text.lower() for t in tokenize(text) if t.kind == "word"]


def is_empty_output(text: str) -> bool:
    return minimal_normalize(text) == ""


def phrase_present(phrase: str, text: str) -> bool:
    """Case-insensitive, word-bounded phrase match on minimally normalized text (section 6.6).

    The phrase is itself tokenized so that punctuation and spacing inside it do
    not matter; the match is on the token sequence.
    """
    needle = [t.text.lower() for t in tokenize(phrase) if t.kind == "word"]
    hay = content_tokens(text)
    if not needle:
        return True
    n = len(needle)
    return any(hay[i : i + n] == needle for i in range(len(hay) - n + 1))
