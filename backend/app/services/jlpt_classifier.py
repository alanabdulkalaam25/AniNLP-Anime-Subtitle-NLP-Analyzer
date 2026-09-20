"""Vocabulary-dataset based JLPT classification."""

from __future__ import annotations

import json
from pathlib import Path

from app.models.schemas import Token

JLPT_LEVELS = ("N5", "N4", "N3", "N2", "N1")
UNKNOWN_LEVEL = "UNKNOWN"


class JLPTClassifier:
    """Load local vocabulary lists and classify tokens by dictionary form."""

    def __init__(self, data_directory: Path | None = None) -> None:
        self.data_directory = data_directory or Path(__file__).parents[2] / "data" / "jlpt"
        self._vocabulary = self._load_vocabulary()

    def _load_vocabulary(self) -> dict[str, set[str]]:
        vocabulary = {level: set() for level in JLPT_LEVELS}
        for level in JLPT_LEVELS:
            file_path = self.data_directory / f"{level.lower()}.json"
            if not file_path.exists():
                continue
            with file_path.open(encoding="utf-8") as source:
                entries = json.load(source)
            if not isinstance(entries, list):
                raise ValueError(f"JLPT dataset {file_path} must contain a JSON array.")
            for entry in entries:
                if isinstance(entry, str):
                    vocabulary[level].add(entry)
                elif isinstance(entry, dict) and isinstance(entry.get("word"), str):
                    vocabulary[level].add(entry["word"])
                else:
                    raise ValueError(f"Invalid vocabulary entry in {file_path}.")
        return vocabulary

    def classify(self, base_form: str) -> str:
        for level in JLPT_LEVELS:
            if base_form in self._vocabulary[level]:
                return level
        return UNKNOWN_LEVEL

    def classify_token(self, token: Token) -> Token:
        """Return a copy with a dataset-derived JLPT level for lexical tokens."""
        if token.pos in {"PUNCTUATION", "WHITESPACE", "PARTICLE", "AUXILIARY"}:
            return token.model_copy(update={"jlpt": None})
        return token.model_copy(update={"jlpt": self.classify(token.base)})
