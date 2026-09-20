# AniNLP API

Base URL: `http://127.0.0.1:8000`

## `GET /api/health`

Returns API availability.

```json
{"status": "ok"}
```

## `POST /api/analyze`

Uploads and analyzes a Japanese SubRip subtitle file.

- Content type: `multipart/form-data`
- Field: `file`
- Accepted extension: `.srt`
- Maximum size: 10 MB
- Text encoding: UTF-8 (including BOM) or CP932

The response contains subtitle metadata, cleaned subtitle cues with normalized tokens, statistics, POS/JLPT distributions, and up to 25 frequent lexical words.

```json
{
  "subtitle": {"filename": "episode.srt", "subtitle_count": 1},
  "sentences": [{
    "index": 1,
    "start": "00:00:01,000",
    "end": "00:00:03,000",
    "text": "学校へ行きます。",
    "tokens": [{
      "surface": "行き",
      "base": "行く",
      "reading": "イク",
      "pos": "VERB",
      "jlpt": "N5"
    }]
  }],
  "statistics": {
    "total_sentences": 1,
    "total_tokens": 5,
    "unique_words": 2,
    "average_sentence_length": 5.0
  },
  "jlpt_distribution": {"N5": 2, "N4": 0, "N3": 0, "N2": 0, "N1": 0, "UNKNOWN": 0},
  "pos_distribution": {"NOUN": 1, "VERB": 1},
  "top_words": []
}
```

Errors use JSON `{ "detail": "..." }`:

- `400`: invalid extension, empty file, or size limit exceeded
- `422`: invalid SRT or unsupported text encoding
- `500`: unexpected NLP-processing failure
