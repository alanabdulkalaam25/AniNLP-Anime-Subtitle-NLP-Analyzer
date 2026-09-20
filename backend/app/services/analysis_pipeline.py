"""Orchestrate SRT parsing, NLP, classification, and statistics."""

from __future__ import annotations

from app.models.schemas import AnalysisResponse, AnalyzedSentence, SubtitleMetadata
from app.services.jlpt_classifier import JLPTClassifier
from app.services.morphological_analyzer import analyze_morphology
from app.services.preprocessor import preprocess_text
from app.services.srt_parser import parse_srt
from app.services.statistics import (
    build_jlpt_distribution,
    build_pos_distribution,
    build_statistics,
    build_top_words,
)


class AnalysisPipeline:
    """Run one subtitle file through every backend analysis stage."""

    def __init__(self, classifier: JLPTClassifier | None = None) -> None:
        self.classifier = classifier or JLPTClassifier()

    def analyze(self, content: str, filename: str) -> AnalysisResponse:
        entries = parse_srt(content)
        sentences: list[AnalyzedSentence] = []
        for entry in entries:
            cleaned_text = preprocess_text(entry.text)
            tokens = [self.classifier.classify_token(token) for token in analyze_morphology(cleaned_text)]
            sentences.append(
                AnalyzedSentence(
                    index=entry.index,
                    start=entry.start,
                    end=entry.end,
                    text=cleaned_text,
                    tokens=tokens,
                )
            )

        return AnalysisResponse(
            subtitle=SubtitleMetadata(filename=filename, subtitle_count=len(entries)),
            sentences=sentences,
            statistics=build_statistics(sentences),
            jlpt_distribution=build_jlpt_distribution(sentences),
            pos_distribution=build_pos_distribution(sentences),
            top_words=build_top_words(sentences),
        )


def decode_subtitle_content(content: bytes) -> str:
    """Decode common subtitle encodings while failing clearly for unsupported data."""
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Subtitle file must be UTF-8 or CP932 encoded.")
