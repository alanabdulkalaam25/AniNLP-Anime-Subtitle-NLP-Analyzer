"""Vocabulary-dataset based JLPT classification."""

from __future__ import annotations

import json
from pathlib import Path
import re

from app.models.schemas import Token

JLPT_LEVELS = ("N5", "N4", "N3", "N2", "N1")
UNKNOWN_LEVEL = "UNKNOWN"

_UNCLASSIFIED_POS = {
    "PUNCTUATION",
    "WHITESPACE",
    "PARTICLE",
    "AUXILIARY",
    "PREFIX",
    "SUFFIX",
    "NUMERAL",
    "PROPER_NOUN",
}

_READING_DELIMITERS = re.compile(r"[/、,]")


def _kata_to_hira(text: str) -> str:
    """Convert Katakana characters to Hiragana for uniform reading comparisons."""
    return "".join(
        chr(ord(char) - 0x60) if "\u30a1" <= char <= "\u30f6" else char
        for char in text
    )


class JLPTClassifier:
    """Load local vocabulary lists and classify tokens by dictionary form."""

    def __init__(
        self,
        data_directory: Path | None = None,
        require_all_levels: bool | None = None,
    ) -> None:
        self.data_directory = (
            data_directory or Path(__file__).parents[2] / "data" / "jlpt"
        )
        # By default, require all levels if using the bundled data directory
        if require_all_levels is None:
            self.require_all_levels = data_directory is None
        else:
            self.require_all_levels = require_all_levels

        self._reading_index: dict[str, set[str]] = {}
        self._vocabulary: dict[str, set[str]] = self._load_vocabulary()

    def _load_vocabulary(self) -> dict[str, set[str]]:
        vocabulary = {level: set() for level in JLPT_LEVELS}
        for level in JLPT_LEVELS:
            file_path = self.data_directory / f"{level.lower()}.json"
            if not file_path.exists():
                if self.require_all_levels:
                    raise FileNotFoundError(f"Missing required JLPT dataset: {file_path}")
                continue

            with file_path.open(encoding="utf-8") as source:
                entries = json.load(source)
            if not isinstance(entries, list):
                raise ValueError(f"JLPT dataset {file_path} must contain a JSON array.")

            for entry in entries:
                if isinstance(entry, str):
                    vocabulary[level].add(entry)
                elif isinstance(entry, dict) and isinstance(entry.get("word"), str):
                    word = entry["word"].strip()
                    if word:
                        vocabulary[level].add(word)

                    # Index reading variants for fallback matching
                    reading_val = entry.get("reading")
                    if isinstance(reading_val, str) and reading_val.strip():
                        for variant in _READING_DELIMITERS.split(reading_val):
                            clean_variant = _kata_to_hira(variant.strip())
                            if clean_variant:
                                self._reading_index.setdefault(clean_variant, set()).add(level)
                else:
                    raise ValueError(f"Invalid vocabulary entry in {file_path}.")
        return vocabulary

    def classify(self, base_form: str) -> str:
        """Classify a single base form, checking vocabulary first, then reading index."""
        for level in JLPT_LEVELS:
            if base_form in self._vocabulary[level]:
                return level

        hira_form = _kata_to_hira(base_form)
        reading_matches = self._reading_index.get(hira_form)
        if reading_matches:
            return min(reading_matches, key=JLPT_LEVELS.index)

        return UNKNOWN_LEVEL

    def classify_token(self, token: Token) -> Token:
        """Return a copy with a dataset-derived JLPT level for lexical tokens."""
        if token.pos in _UNCLASSIFIED_POS:
            return token.model_copy(update={"jlpt": None})

        # Candidates to try against vocabulary
        candidates: list[str] = []
        for form in [token.base, *getattr(token, "lookup_forms", []), token.surface]:
            if form and form not in candidates:
                candidates.append(form)

        # 1. Exact vocabulary match
        matching_levels: set[str] = set()
        for cand in candidates:
            for level in JLPT_LEVELS:
                if cand in self._vocabulary[level]:
                    matching_levels.add(level)

        if matching_levels:
            return token.model_copy(
                update={"jlpt": min(matching_levels, key=JLPT_LEVELS.index)}
            )

        # 2. Reading index fallback
        reading_candidates: list[str] = []
        if token.reading:
            reading_candidates.append(token.reading)
        for form in candidates:
            if form not in reading_candidates:
                reading_candidates.append(form)

        for rcand in reading_candidates:
            hira = _kata_to_hira(rcand)
            if hira in self._reading_index:
                matching_levels.update(self._reading_index[hira])

        if matching_levels:
            return token.model_copy(
                update={"jlpt": min(matching_levels, key=JLPT_LEVELS.index)}
            )

        return token.model_copy(update={"jlpt": UNKNOWN_LEVEL})
