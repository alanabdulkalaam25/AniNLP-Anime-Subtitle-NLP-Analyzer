# Architecture

```text
React frontend
    | HTTP JSON / multipart upload
FastAPI routes
    |
    ├── AnalysisPipeline
    │   ├── SRT parser
    │   ├── Preprocessor
    │   ├── fugashi/MeCab morphology
    │   ├── JLPT classifier
    │   └── Statistics builder
    |
    └── SubtitleTranslator (separate /api/translate call)
        | batched, deduplicated cue text
        └── Google web translation or DeepL
    |
AnalysisResponse JSON
```

The backend owns every NLP operation. The frontend must only upload files and present the API response. Translation is a separate best-effort request, so the Japanese analysis is never blocked by an external provider.
