"""Tests for the MeCab-compatible Japanese morphology service."""

from app.services.morphological_analyzer import analyze_morphology


def test_analyze_morphology_returns_normalized_dictionary_forms() -> None:
    tokens = analyze_morphology("学校へ行きます。")

    assert [(token.surface, token.base, token.pos) for token in tokens] == [
        ("学校", "学校", "NOUN"),
        ("へ", "へ", "PARTICLE"),
        ("行き", "行く", "VERB"),
        ("ます", "ます", "AUXILIARY"),
        ("。", "。", "PUNCTUATION"),
    ]
    assert tokens[0].reading == "ガッコウ"
    assert tokens[2].reading == "イク"
