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


def test_analyze_morphology_maps_pronouns_and_numerals() -> None:
    tokens = analyze_morphology("これ は 100 です")
    pos_tags = {token.surface: token.pos for token in tokens}
    assert pos_tags["これ"] == "PRONOUN"
    assert pos_tags["100"] == "NUMERAL"


def test_analyze_morphology_sanitizes_oov_annotations() -> None:
    tokens = analyze_morphology("キース")
    assert tokens[0].base == "キース"
    assert "-" not in tokens[0].base
