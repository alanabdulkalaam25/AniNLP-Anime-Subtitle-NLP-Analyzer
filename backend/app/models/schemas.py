"""Pydantic schemas shared by API routes and analysis services."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class SubtitleEntry(BaseModel):
    index: int = Field(ge=1)
    start: str
    end: str
    text: str


class Token(BaseModel):
    surface: str
    base: str
    reading: str | None = None
    pos: str
    jlpt: str | None = None
    lookup_forms: list[str] = Field(default_factory=list, exclude=True)


class AnalyzedSentence(SubtitleEntry):
    tokens: list[Token]


class SubtitleMetadata(BaseModel):
    filename: str
    subtitle_count: int


class Statistics(BaseModel):
    total_sentences: int
    total_tokens: int
    unique_words: int
    average_sentence_length: float


class WordFrequency(BaseModel):
    word: str
    reading: str | None = None
    pos: str
    jlpt: str | None = None
    frequency: int


class AnalysisResponse(BaseModel):
    subtitle: SubtitleMetadata
    sentences: list[AnalyzedSentence]
    statistics: Statistics
    jlpt_distribution: dict[str, int]
    pos_distribution: dict[str, int]
    top_words: list[WordFrequency]


class TranslationRequest(BaseModel):
    sentences: list[str] = Field(min_length=1, max_length=2_000)


class TranslationResponse(BaseModel):
    translations: list[str | None]
    failed_count: int
    provider: str
