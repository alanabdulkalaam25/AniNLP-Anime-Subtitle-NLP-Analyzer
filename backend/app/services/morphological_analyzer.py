"""Japanese morphological analysis backed by fugashi/MeCab and UniDic."""

from __future__ import annotations

from functools import lru_cache

from fugashi import Tagger

from app.models.schemas import Token

_POS_MAP = {
    "名詞": "NOUN",
    "動詞": "VERB",
    "形容詞": "ADJECTIVE",
    "形状詞": "ADJECTIVAL_NOUN",
    "副詞": "ADVERB",
    "助詞": "PARTICLE",
    "助動詞": "AUXILIARY",
    "連体詞": "PRENOMINAL",
    "接続詞": "CONJUNCTION",
    "感動詞": "INTERJECTION",
    "接頭辞": "PREFIX",
    "接尾辞": "SUFFIX",
    "補助記号": "PUNCTUATION",
    "記号": "PUNCTUATION",
    "空白": "WHITESPACE",
}


@lru_cache(maxsize=1)
def _get_tagger() -> Tagger:
    """Create one reusable analyzer instance after the dictionary is loaded."""
    return Tagger()


def analyze_morphology(text: str) -> list[Token]:
    """Return normalized application tokens for Japanese subtitle text."""
    tokens: list[Token] = []
    for word in _get_tagger()(text):
        feature = word.feature
        base = feature.lemma or word.surface
        reading = feature.kanaBase or feature.kana or None
        pos = _POS_MAP.get(feature.pos1, "OTHER")
        if pos == "WHITESPACE":
            continue
        tokens.append(Token(surface=word.surface, base=base, reading=reading, pos=pos))
    return tokens
