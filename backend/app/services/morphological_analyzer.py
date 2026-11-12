"""Japanese morphological analysis backed by fugashi/MeCab and UniDic."""

from __future__ import annotations

import threading
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
    "代名詞": "PRONOUN",
}

_TAGGER_LOCK = threading.Lock()


def _sanitize_lemma(lemma: str | None) -> str | None:
    """Strip UniDic OOV annotations like '-Keith', '-wall', '-外国'."""
    if not lemma:
        return None
    if "-" in lemma:
        prefix, suffix = lemma.split("-", 1)
        if prefix and (suffix.isascii() or suffix in {"外国", "代名詞", "形状詞", "固有名詞", "断定"}):
            return prefix
    return lemma


@lru_cache(maxsize=1)
def _get_tagger() -> Tagger:
    """Create one reusable analyzer instance after the dictionary is loaded."""
    return Tagger()


def analyze_morphology(text: str) -> list[Token]:
    """Return normalized application tokens for Japanese subtitle text."""
    tokens: list[Token] = []
    with _TAGGER_LOCK:
        parsed_words = list(_get_tagger()(text))

    for word in parsed_words:
        feature = word.feature
        pos1 = feature.pos1
        pos2 = getattr(feature, "pos2", None)

        if pos1 == "名詞" and pos2 == "数詞":
            pos = "NUMERAL"
        elif pos1 == "名詞" and pos2 == "固有名詞":
            pos = "PROPER_NOUN"
        else:
            pos = _POS_MAP.get(pos1, "OTHER")

        if pos == "WHITESPACE":
            continue

        reading = feature.kanaBase or feature.kana or None
        clean_lemma = _sanitize_lemma(feature.lemma)
        clean_orth = _sanitize_lemma(getattr(feature, "orthBase", None))

        if pos == "PUNCTUATION":
            base = word.surface
        else:
            base = clean_orth or clean_lemma or word.surface

        lookup_candidates: list[str] = []
        for cand in (base, clean_lemma, getattr(feature, "orthBase", None), word.surface):
            if cand and cand not in lookup_candidates:
                lookup_candidates.append(cand)

        tokens.append(
            Token(
                surface=word.surface,
                base=base,
                reading=reading,
                pos=pos,
                lookup_forms=lookup_candidates,
            )
        )
    return tokens
