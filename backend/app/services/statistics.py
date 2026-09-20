"""Aggregate subtitle analysis results into dashboard-ready statistics."""

from __future__ import annotations

from collections import Counter

from app.models.schemas import AnalyzedSentence, Statistics, Token, WordFrequency
from app.services.jlpt_classifier import JLPT_LEVELS, UNKNOWN_LEVEL

_EXCLUDED_VOCABULARY_POS = {"PUNCTUATION", "WHITESPACE", "PARTICLE", "AUXILIARY"}


def build_statistics(sentences: list[AnalyzedSentence]) -> Statistics:
    tokens = [token for sentence in sentences for token in sentence.tokens]
    lexical_tokens = [token for token in tokens if token.pos not in _EXCLUDED_VOCABULARY_POS]
    total_sentences = len(sentences)
    return Statistics(
        total_sentences=total_sentences,
        total_tokens=len(tokens),
        unique_words=len({token.base for token in lexical_tokens}),
        average_sentence_length=round(len(tokens) / total_sentences, 2) if total_sentences else 0.0,
    )


def build_jlpt_distribution(sentences: list[AnalyzedSentence]) -> dict[str, int]:
    distribution = {level: 0 for level in (*JLPT_LEVELS, UNKNOWN_LEVEL)}
    for token in (token for sentence in sentences for token in sentence.tokens):
        if token.jlpt is not None:
            distribution[token.jlpt] += 1
    return distribution


def build_pos_distribution(sentences: list[AnalyzedSentence]) -> dict[str, int]:
    counts = Counter(token.pos for sentence in sentences for token in sentence.tokens)
    return dict(sorted(counts.items()))


def build_top_words(sentences: list[AnalyzedSentence], limit: int = 25) -> list[WordFrequency]:
    occurrences: dict[str, list[Token]] = {}
    for token in (token for sentence in sentences for token in sentence.tokens):
        if token.pos not in _EXCLUDED_VOCABULARY_POS:
            occurrences.setdefault(token.base, []).append(token)

    ordered_words = sorted(occurrences.items(), key=lambda item: (-len(item[1]), item[0]))[:limit]
    return [
        WordFrequency(
            word=base,
            reading=tokens[0].reading,
            pos=tokens[0].pos,
            jlpt=tokens[0].jlpt,
            frequency=len(tokens),
        )
        for base, tokens in ordered_words
    ]
