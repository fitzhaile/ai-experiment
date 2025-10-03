## Overview

This is a minimal Flask app that exposes a tiny UI and an API to generate text with OpenAI.

- The root route `/` serves a small, inline HTML page with an input and a submit button.
- The API route `/api/haiku` accepts a prompt (query param `input`) and returns JSON with the model's response.
- You can also open `static/index.html` directly; it calls the same API running locally.

### Architecture

```text
┌───────────────────────┐           GET /            ┌──────────────────────┐
│  Browser (UI)         │────────────────────────────▶│  Flask app (app.py)  │
│  - / (inline HTML)    │                             │  - serves inline UI  │
│  - static/index.html  │◀────────────────────────────│  - CORS enabled      │
└──────────┬────────────┘          HTML               └─────────┬───────────┘
           │                                                 │
           │ fetch /api/haiku?input=... (JSON)               │ OpenAI SDK
           ▼                                                 ▼
     JSON { text }                                  ┌──────────────────────┐
                                                    │   OpenAI API         │
                                                    └──────────────────────┘
```

### Configuration

- `OPENAI_API_KEY` is required. Put it in `.env` locally or as an env var in deployment.
- `OPENAI_MODEL` (optional) defaults to `gpt-5-mini` with a fallback to `gpt-4o-mini`.
- `OPENAI_PROJECT` (optional) for project-scoped keys.
- `FLASK_DEBUG` (optional) enables auto-reload locally.
- `PORT` (optional) when running `python app.py`.

## Deploying this app (ai-experiments)

- Push this folder to a Git repo (GitHub/GitLab/Bitbucket).
- On Render: New → Web Service → Use existing repo.
- Settings:
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `gunicorn app:app`
- Add env var `OPENAI_API_KEY` (or use `.env` via Render Secrets).
- Deploy. Root `/` serves UI; API at `/api/haiku`.

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "OPENAI_API_KEY=sk-REPLACE_ME" > .env  # then edit with your key
# optionally enable debug: echo "FLASK_DEBUG=1" >> .env
python app.py
```

Open http://127.0.0.1:5060/.
