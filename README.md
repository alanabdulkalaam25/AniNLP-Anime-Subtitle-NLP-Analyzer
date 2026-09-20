# AniNLP

Anime Subtitle NLP Analyzer processes Japanese `.srt` subtitle files into morphology, JLPT vocabulary labels, and dashboard-ready statistics.

## Backend quick start

```sh
cd backend
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive API documentation is at `/docs`.

## API

- `GET /api/health` returns service availability.
- `POST /api/analyze` accepts one multipart `file` field containing a `.srt` file (maximum 10 MB, UTF-8 or CP932 encoding).

See `docs/api.md` and `docs/nlp-pipeline.md` for response details and analysis behavior.

## Deployment

The repository includes `render.yaml` for the FastAPI service. Deploy it to Render first; when prompted, set `CORS_ORIGINS` to your future Vercel production URL, for example `https://anime-subtitle-nlp-analyzer.vercel.app`.

Then deploy the `frontend` directory as a Vite project on Vercel. In Vercel's environment variables, set `VITE_API_BASE_URL` to your Render URL followed by `/api`, for example `https://aninlp-api.onrender.com/api`. Redeploy the frontend after setting the variable.

## JLPT data and important limitation

JLPT labels are vocabulary-dataset lookups, not official JLPT assessments. The included vocabulary files contain 8,334 entries from [OpenJLPT](https://github.com/evanclan/OpenJLPT): N5 (662), N4 (632), N3 (1,784), N2 (1,793), and N1 (3,463).

The imported data is licensed under CC BY-SA 4.0. Its required attribution and license text are preserved in `backend/data/jlpt/OPENJLPT_NOTICE.md` and `backend/data/jlpt/OPENJLPT_LICENSE.txt`. If you redistribute the dataset or a derivative of it, retain attribution, link to the license, and comply with its ShareAlike terms.

The JLPT organisation does not publish an official exhaustive N5–N1 vocabulary list. OpenJLPT's level assignments are community-derived, so `UNKNOWN` means “not found in this dataset,” not “not Japanese” or “not appropriate for a JLPT level.”
