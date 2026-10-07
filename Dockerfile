# FlameGuard AI API (the website is deployed separately, see docs/deployment.md).
#   docker build -t flameguard-api .
#   docker run -p 8000:8000 -e FLAMEGUARD_LLM_API_KEY=... flameguard-api
# Works on any container host (Hugging Face Spaces, Render, Fly.io, Cloud Run); it listens on $PORT.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FLAMEGUARD_ROOT=/app \
    FLAMEGUARD_EMBED_CACHE=/app/.cache/fastembed \
    PORT=8000

WORKDIR /app

# Dependencies first, so code changes do not reinstall them
COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

# The flameguard science library
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-deps .

# Embedding model for Ask FlameGuard, fetched at build time so start-up needs no download
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5', cache_dir='/app/.cache/fastembed')"

# API code and the committed artefacts it serves (no raw data, notebooks or PDFs)
COPY backend/app ./backend/app
COPY data/processed ./data/processed
COPY data/knowledge ./data/knowledge
COPY models/final_model.joblib models/final_model.json ./models/
COPY reports ./reports

RUN useradd --create-home --uid 1000 app && chown -R app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/api/health', timeout=4)"

CMD ["sh", "-c", "uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
