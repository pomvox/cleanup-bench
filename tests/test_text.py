"""Pinned tests for the tokenizer and normalizers (docs/spec.md section 6.1).

Expected values are written out by hand. A change here changes scores and
must bump SCORER_VERSION.
"""

from __future__ import annotations

from cleanupbench.scorer.text import (
    NEWLINE_TOKEN,
    content_tokens,
    is_empty_output,
    minimal_normalize,
    phrase_present,
    token_texts,
    tokenize,
)


def test_minimal_normalize_whitespace_and_quotes():
    assert minimal_normalize("  Hello,   world \t ") == "Hello, world"
    assert minimal_normalize("don’t “quote”") == "don't \"quote\""
    assert minimal_normalize("a \n  b\r\nc\rd") == "a\nb\nc\nd"


def test_minimal_normalize_keeps_case_punctuation_and_contractions():
    text = "I'm gonna go, OK? It's FINE."
    assert minimal_normalize(text) == text


def test_minimal_normalize_nfc():
    decomposed = "é"  # e + combining acute
    assert minimal_normalize(decomposed) == "é"


def test_tokenize_words_punct_newlines():
    toks = tokenize("Let's meet at 3:30 pm, OK?\nNew line.")
    assert [(t.text, t.kind) for t in toks] == [
        ("Let's", "word"),
        ("meet", "word"),
        ("at", "word"),
        ("3", "word"),
        (":", "punct"),
        ("30", "word"),
        ("pm", "word"),
        (",", "punct"),
        ("OK", "word"),
        ("?", "punct"),
        (NEWLINE_TOKEN, "newline"),
        ("New", "word"),
        ("line", "word"),
        (".", "punct"),
    ]


def test_tokenize_hyphens_apostrophes_and_symbols():
    assert token_texts("twenty-five o'clock $20 john@example.com") == [
        "twenty-five",
        "o'clock",
        "$",
        "20",
        "john",
        "@",
        "example",
        ".",
        "com",
    ]
    # A trailing apostrophe or hyphen is punctuation, not part of the word.
    assert token_texts("rock 'n' roll -") == ["rock", "'", "n", "'", "roll", "-"]


def test_tokenize_normalizes_first():
    assert token_texts("don’t") == ["don't"]


def test_content_tokens_lowercase_no_punct():
    assert content_tokens("Never merge, a Change like THIS.\nOkay") == [
        "never",
        "merge",
        "a",
        "change",
        "like",
        "this",
        "okay",
    ]
    assert content_tokens("") == []
    assert content_tokens("...") == []


def test_is_empty_output():
    assert is_empty_output("")
    assert is_empty_output("  \n ")
    assert not is_empty_output(".")


def test_phrase_present_word_bounded():
    assert phrase_present("never", "Never merge this.")
    assert not phrase_present("ever", "Never merge this.")
    assert phrase_present("like a charm", "It works like a charm, honestly.")
    assert not phrase_present("like a charm", "It works like charm.")
    assert phrase_present("um", "Um, hello")
    assert not phrase_present("um", "Umbrella")
    assert phrase_present("3:30 pm", "at 3:30 PM")
    assert phrase_present("", "anything")
