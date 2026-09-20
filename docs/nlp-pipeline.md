# NLP Pipeline

1. **Decode** the uploaded bytes as UTF-8/BOM or CP932.
2. **Parse** SRT cues into an index, timestamps, and raw text.
3. **Preprocess** conservatively: remove HTML and ASS presentation tags, decode HTML entities, and normalize whitespace. Japanese punctuation and grammar are retained.
4. **Analyze morphology** with `fugashi`, a Python interface to MeCab, using the bundled UniDic Lite dictionary.
5. **Normalize tokens** into the stable API fields: `surface`, dictionary `base`, base-form `reading`, and application POS label.
6. **Classify lexical tokens** using local `backend/data/jlpt/n5.json` through `n1.json` files. Particles, auxiliaries, whitespace, and punctuation have no JLPT label. Other unmatched lexical tokens are `UNKNOWN`.
7. **Aggregate** token counts, unique lexical vocabulary, POS counts, JLPT counts, and the 25 most frequent lexical base forms.

## POS labels

The backend translates UniDic Japanese labels to frontend-friendly values such as `NOUN`, `VERB`, `ADJECTIVE`, `ADVERB`, `PARTICLE`, `AUXILIARY`, and `PUNCTUATION`.

## JLPT data

The local files are the OpenJLPT vocabulary dataset, imported from `data/json/vocab/{n5,n4,n3,n2,n1}.json` in the [OpenJLPT repository](https://github.com/evanclan/OpenJLPT). They contain 8,334 vocabulary entries: 662 N5, 632 N4, 1,784 N3, 1,793 N2, and 3,463 N1.

OpenJLPT is licensed under CC BY-SA 4.0. The source attribution and full license are included alongside the data as `backend/data/jlpt/OPENJLPT_NOTICE.md` and `backend/data/jlpt/OPENJLPT_LICENSE.txt`. Any redistribution of this data or derivatives must meet those attribution and ShareAlike requirements.

The JLPT organisation does not publish an official exhaustive N5–N1 vocabulary list. OpenJLPT's levels are community-derived, reliable reference labels—not official JLPT determinations. Therefore, `UNKNOWN` means only that a lexical token is not present in this dataset.
