"""Orchestrate SRT parsing, NLP, classification, and statistics."""

from __future__ import annotations

import time

from app.models.schemas import AnalysisResponse, AnalyzedSentence, SubtitleMetadata
from app.services.jlpt_classifier import JLPTClassifier
from app.services.morphological_analyzer import analyze_morphology
from app.services.preprocessor import preprocess_text
from app.services.srt_parser import SRTParseError, parse_srt
from app.services.statistics import (
    build_jlpt_distribution,
    build_pos_distribution,
    build_statistics,
    build_top_words,
)


class AnalysisTimeoutError(TimeoutError):
    """Raised when analysis exceeds the allocated execution time limit."""


class AnalysisPipeline:
    """Run one subtitle file through every backend analysis stage."""

    def __init__(self, classifier: JLPTClassifier | None = None) -> None:
        self.classifier = classifier or JLPTClassifier()

    def analyze(
        self,
        content: str,
        filename: str,
        deadline: float | None = None,
    ) -> AnalysisResponse:
        entries = parse_srt(content)
        sentences: list[AnalyzedSentence] = []
        for entry in entries:
            if deadline is not None and time.monotonic() >= deadline:
                raise AnalysisTimeoutError("Subtitle analysis timed out.")

            cleaned_text = preprocess_text(entry.text)
            if not cleaned_text:
                continue

            tokens = [
                self.classifier.classify_token(token)
                for token in analyze_morphology(cleaned_text)
            ]
            if not tokens:
                continue

            sentences.append(
                AnalyzedSentence(
                    index=entry.index,
                    start=entry.start,
                    end=entry.end,
                    text=cleaned_text,
                    tokens=tokens,
                )
            )

        if not sentences:
            raise SRTParseError("Subtitle file contains no analyzable text.")

        return AnalysisResponse(
            subtitle=SubtitleMetadata(filename=filename, subtitle_count=len(sentences)),
            sentences=sentences,
            statistics=build_statistics(sentences),
            jlpt_distribution=build_jlpt_distribution(sentences),
            pos_distribution=build_pos_distribution(sentences),
            top_words=build_top_words(sentences),
        )


def decode_subtitle_content(content: bytes) -> str:
    """Decode common subtitle encodings while failing clearly for unsupported data."""
    if content.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return content.decode("utf-16")
        except UnicodeDecodeError:
            pass

    for encoding in ("utf-8-sig", "cp932"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Subtitle file must be UTF-8, UTF-16, or CP932 encoded.")
