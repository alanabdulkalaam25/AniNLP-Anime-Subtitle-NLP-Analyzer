"""Tests for local JLPT vocabulary classification."""

import json
from pathlib import Path

from app.models.schemas import Token
from app.services.jlpt_classifier import JLPTClassifier, UNKNOWN_LEVEL


def test_classifier_uses_base_forms_and_leaves_grammar_unclassified(tmp_path: Path) -> None:
    (tmp_path / "n5.json").write_text(json.dumps([{"word": "食べる"}]), encoding="utf-8")
    classifier = JLPTClassifier(tmp_path)

    assert classifier.classify("食べる") == "N5"
    assert classifier.classify("架空語") == UNKNOWN_LEVEL
    assert classifier.classify_token(Token(surface="食べ", base="食べる", pos="VERB")).jlpt == "N5"
    assert classifier.classify_token(Token(surface="は", base="は", pos="PARTICLE")).jlpt is None


def test_bundled_openjlpt_vocabulary_has_full_n5_to_n1_coverage() -> None:
    classifier = JLPTClassifier()

    assert {level: len(words) for level, words in classifier._vocabulary.items()} == {
        "N5": 662,
        "N4": 632,
        "N3": 1784,
        "N2": 1793,
        "N1": 3463,
    }
