# Architecture

```text
React frontend
    | HTTP JSON / multipart upload
FastAPI routes
    | 
AnalysisPipeline
    ├── SRT parser
    ├── Preprocessor
    ├── fugashi/MeCab morphology
    ├── JLPT classifier
    └── Statistics builder
    |
AnalysisResponse JSON
```

The backend owns every NLP operation. The frontend must only upload files and present the API response.
