# AniNLP

AniNLP turns a Japanese anime subtitle file into a cue-by-cue study sheet: dictionary forms, parts of speech, community-derived JLPT labels, and summary statistics for every line.

Upload an `.srt` file and the app returns a readable breakdown of each cue, the most frequent vocabulary, a part-of-speech ledger, and a JLPT reference spectrum. Nothing is stored; the file is analyzed in memory and discarded.

## What it does

- Parses SubRip cues and preserves their original index and timestamps.
- Removes presentation markup (HTML, ASS tags, line breaks) while keeping the Japanese text intact.
- Tokenizes every cue with MeCab through `fugashi` and the bundled UniDic Lite dictionary.
- Normalizes each token to a stable shape: `surface`, dictionary `base`, `reading`, `pos`, and `jlpt`.
- Matches lexical tokens against the bundled JLPT vocabulary lists, with reading-based fallback matching.
- Aggregates cue counts, token counts, unique lexical words, average cue length, POS distribution, JLPT distribution, and the 25 most frequent vocabulary entries.
- Generates no content of its own. Every label, count, and example comes from the uploaded file and the local reference data.

## Interface

The frontend is built around a "translation desk" visual language: warm paper, sumi ink, a single vermilion accent, and an annotated sample cue instead of a decorative hero image. Light is the default theme; the dark theme follows the operating system preference automatically.

Before analysis, the page shows the upload form and a fully annotated sample cue. After analysis it shows, in order:

1. A summary band (cues, tokens, unique words, average tokens per cue).
2. The JLPT reference spectrum.
3. A parts-of-speech ledger.
4. A note about what the JLPT labels mean.
5. The frequent-vocabulary table.
6. A collapsible cue sheet in which each line expands to show its tokens.

The layout is responsive down to 360 px, and the cue sheet uses native `<details>` elements so it works without JavaScript-only disclosure widgets.

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | React 19, Vite, plain CSS, Bun for install and scripts |
| Backend | FastAPI, Uvicorn, Pydantic |
| NLP | `fugashi` (MeCab) with `unidic-lite` |
| JLPT data | Local JSON vocabulary lists derived from OpenJLPT |
| Deployment | Render for the API (`render.yaml`), any static host for the Vite build |

## Repository layout

```text
backend/
  app/
    api/routes/      health.py, analyze.py
    core/            config.py, rate_limit.py
    models/          schemas.py
    services/        srt_parser, preprocessor, morphological_analyzer,
                     jlpt_classifier, statistics, analysis_pipeline
  data/jlpt/         n5.json through n1.json, OpenJLPT notice and license
  tests/             pytest suite
frontend/
  src/App.jsx        upload flow, results, cue sheet
  src/index.css      "translation desk" design system
  src/services/api.js
docs/                api.md, architecture.md, nlp-pipeline.md
sample-data/
  subtitles/         real and fixture subtitle files
render.yaml          Render blueprint for the API
```

## Getting started

### Prerequisites

- Python 3.12 or newer.
- Bun (latest). The frontend is installed and run with Bun, not npm.

The backend uses a virtual environment inside `backend/`. Commands below use the explicit interpreter path so activation is optional.

### 1. Start the API

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

On macOS or Linux, replace `.venv\Scripts\python.exe` with `.venv/bin/python`.

The API listens on `http://127.0.0.1:8000`. Interactive documentation is at `/docs` and `/redoc`; a JSON schema is at `/openapi.json`.

Check that it is up:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

`GET /api/health` returns immediately without loading the tokenizer. Use `GET /api/ready` when you want to confirm that UniDic and the JLPT files actually loaded.

### 2. Start the frontend

In a second terminal:

```powershell
cd frontend
bun install
bun run dev
```

Open `http://localhost:5173`. Vite is configured to use port 5173, which is also the origin the API allows by default. If Vite falls back to another port, add that origin to `CORS_ORIGINS` before using the app.

The frontend calls `http://127.0.0.1:8000/api` by default. To point it somewhere else, create `frontend/.env`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

### 3. Build the frontend

```powershell
cd frontend
bun run build
bun run preview -- --port 5173
```

`bun run build` writes a production bundle to `frontend/dist/`. The preview command stays on port 5173 so the default CORS allowlist keeps working.

## Configuration

Backend settings are read from the environment (and from `backend/.env` through `python-dotenv`). All values have safe defaults.

| Variable | Default | Purpose |
| --- | --- | --- |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated browser origins allowed to call the API |
| `CORS_ORIGIN_REGEX` | unset | Optional regex for origins you cannot list explicitly, such as Vercel preview deployments |
| `MAX_UPLOAD_SIZE_BYTES` | `10485760` (10 MB) | Maximum raw upload size |
| `MAX_SUBTITLE_TEXT_CHARS` | `500000` | Maximum decoded text characters |
| `ANALYSIS_TIMEOUT_SECONDS` | `30` | Per-request analysis deadline |
| `MAX_CONCURRENT_ANALYSES` | `1` | Analyses allowed to run in parallel per process |
| `RATE_LIMIT_REQUESTS` | `10` | Requests allowed per client per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate-limit window length |

Frontend:

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000/api` | Base URL of the API, including `/api` |

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness check; returns `{"status": "ok"}` without initializing NLP resources |
| `GET` | `/api/ready` | Readiness check; loads the tokenizer and JLPT datasets |
| `POST` | `/api/analyze` | Accepts one multipart `file` field and returns the full analysis |

`POST /api/analyze` accepts `.srt` files only, up to 10 MB, 500,000 decoded characters, and 2,000 cues. The response contains:

- `subtitle`: sanitized filename and analyzed cue count.
- `sentences`: cleaned cues with timestamps and tokens.
- `statistics`: cue count, token count, unique lexical words, and average tokens per cue.
- `jlpt_distribution`: `N5` through `N1` plus `UNKNOWN`.
- `pos_distribution`: token counts by part of speech.
- `top_words`: up to 25 frequent lexical base forms with reading, POS, JLPT label, and frequency.

Errors are returned as `{"detail": "..."}`:

- `400`: wrong extension, empty file, or a size or text limit exceeded.
- `408`: the analysis deadline expired.
- `422`: malformed SRT or unsupported text encoding.
- `429`: rate limit exceeded; the response includes `Retry-After`.
- `500`: unexpected NLP failure.

Full response shapes and examples are in [`docs/api.md`](docs/api.md).

## How analysis works

1. Decode the upload as UTF-8 (including BOM), UTF-16 (with BOM), or CP932.
2. Parse cues, tolerating comma or period milliseconds, single-digit hours, and indexless SRT blocks. Cue indexes must be at least 1, and end times may not precede start times.
3. Remove HTML, ASS tags, ASS line breaks, and HTML entities; normalize whitespace.
4. Tokenize with `fugashi` and UniDic Lite.
5. Normalize tokens and strip UniDic out-of-vocabulary annotations from lemmas.
6. Classify lexical tokens against `backend/data/jlpt/n5.json` through `n1.json`, then aggregate statistics.
7. Return one JSON response. No upload, intermediate text, or result is persisted.

Particles, auxiliaries, punctuation, whitespace, prefixes, suffixes, numerals, and proper nouns are intentionally left without a JLPT label. Other lexical tokens that do not match the dataset are marked `UNKNOWN`.

More detail: [`docs/nlp-pipeline.md`](docs/nlp-pipeline.md) and [`docs/architecture.md`](docs/architecture.md).

## Sample data

`sample-data/subtitles/` contains real Japanese subtitle files for manual testing:

| File | Notes |
| --- | --- |
| `AOT_S1_E1.srt` | Attack on Titan, season 1 episode 1 |
| `AOT_S1_E2.srt` | Season 1 episode 2 |
| `AOT_S1_E3.srt` | Season 1 episode 3 |
| `AOT_S1_E5.srt` | Season 1 episode 5 |
| `AOT_S1_S4.srt` | Season 1 special 4 |
| `Mononoke Hime.jp.srt` | Feature film, larger file |
| `sample.srt` | Small fixture with HTML and ASS markup for parser checks |

`AOT_S1_E1.srt` analyzes to 303 cues, 2,491 tokens, 453 unique lexical words, and 8.22 tokens per cue. Its first cue is `（アルミン）その日 人類は思い出した` at `00:00:26,426 → 00:00:30,263`.

## Tests

```powershell
cd backend
.venv\Scripts\python.exe -m pytest
```

The suite covers SRT parsing, preprocessing, morphology, JLPT classification, statistics, the full pipeline, and the HTTP endpoints, including CORS, upload limits, filename sanitization, and rate limiting. The first run loads the real UniDic dictionary and can take a few seconds longer than later runs.

## Deployment

The app needs no database. Deploy the backend first so you have its public URL, then point the frontend at it.

### Backend on Render

The repository includes `render.yaml`, so you can create a Blueprint from the repo or configure a Web Service manually with these values:

| Setting | Value |
| --- | --- |
| Runtime | Python 3 |
| Root directory | `backend` |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"` |
| Health check path | `/api/ready` |
| Python version | `3.12.8` (set the `PYTHON_VERSION` env var) |

Environment variables:

| Variable | Value |
| --- | --- |
| `CORS_ORIGINS` | `https://your-app.vercel.app` (comma-separated, no trailing slash) |
| `CORS_ORIGIN_REGEX` | Optional, for preview deployments; keep it scoped to your project |
| `PYTHON_VERSION` | `3.12.8` |

The start command must include `--proxy-headers --forwarded-allow-ips="*"` so uvicorn trusts Render's forwarded client IP. The rate limiter keys on that IP; without it, every visitor shares one bucket.

After Render deploys, confirm `https://your-service.onrender.com/api/ready` returns `{"status":"ready"}`. That path loads and verifies UniDic plus the JLPT data, so Render only routes traffic after the NLP stack is usable. `/api/health` remains a cheap liveness check that does not load the tokenizer.

### Frontend on Vercel

Import the repository into Vercel and use these project settings:

| Setting | Value |
| --- | --- |
| Root directory | `frontend` |
| Framework preset | Vite |
| Install command | `bun install` |
| Build command | `bun run build` |
| Output directory | `dist` |

`frontend/vercel.json` declares the build settings. Add this environment variable in Vercel:

| Variable | Value | Environments |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `https://your-service.onrender.com/api` | Production (and Preview if needed) |

Vite inlines `VITE_API_BASE_URL` at build time. After adding or changing it, redeploy the frontend; editing the variable alone does not update an existing build.

Then copy the Vercel production origin (for example `https://your-app.vercel.app`) into the backend's `CORS_ORIGINS` on Render and let Render restart the service. The origin is scheme plus host only: no path, no trailing slash. Add any custom domains too. For Vercel preview deployments, either add a stable preview domain to `CORS_ORIGINS` or set `CORS_ORIGIN_REGEX` to a pattern scoped to your project.

Order matters:

1. Deploy the backend and note its `https://*.onrender.com` URL.
2. Set `VITE_API_BASE_URL` on Vercel and redeploy the frontend.
3. Copy the Vercel origin into `CORS_ORIGINS` on Render.
4. Restart/redeploy the backend, then test one upload from the deployed frontend.

### Deployed-environment notes

- Render free instances sleep; the first request after a pause can take 30–60 seconds.
- The rate limiter is in-process. Keep one Render instance unless you move counters to a shared store.
- Upload limits are enforced by the API (`MAX_UPLOAD_SIZE_BYTES`, `MAX_SUBTITLE_TEXT_CHARS`), not by Render or Vercel.

### Common deployment errors

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Failed to fetch` on the deployed site | `VITE_API_BASE_URL` missing, wrong, or still localhost | Set it to the Render URL plus `/api`, then redeploy Vercel |
| CORS error in the browser console | Origin not exactly listed in `CORS_ORIGINS` | Add scheme + host with no trailing slash, then restart Render |
| 404 when clicking Analyze | API URL is missing `/api` | Use `https://your-service.onrender.com/api` |
| 429 immediately | Shared proxy IP because forwarded headers are not trusted | Keep `--proxy-headers --forwarded-allow-ips="*"` in the start command |
| First request is very slow | Render free instance woke from sleep | Wait for the cold start; use a paid instance to avoid it |

## JLPT data and limitations

JLPT labels are vocabulary-dataset lookups, not official JLPT assessments. The bundled files contain 8,334 entries from [OpenJLPT](https://github.com/evanclan/OpenJLPT): N5 (662), N4 (632), N3 (1,784), N2 (1,793), and N1 (3,463).

The JLPT organization does not publish an exhaustive official N5-N1 vocabulary list. OpenJLPT's level assignments are community-derived, so `UNKNOWN` means "not found in this dataset", not "not Japanese" or "not appropriate for a JLPT level". Treat the labels as study hints.

OpenJLPT is licensed under CC BY-SA 4.0. Its required attribution and full license text are preserved in `backend/data/jlpt/OPENJLPT_NOTICE.md` and `backend/data/jlpt/OPENJLPT_LICENSE.txt`. If you redistribute the dataset or a derivative, retain the attribution, link to the license, and comply with the ShareAlike terms.

## License

This repository, including the bundled OpenJLPT data and derivatives of it, is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). See [`LICENSE`](LICENSE).
