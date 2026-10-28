# Doc2Any — Python FastAPI + static UI
FROM python:3.13-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DOC2ANY_DATA_DIR=/data \
    DOC2ANY_HOST=0.0.0.0 \
    DOC2ANY_PORT=8000

WORKDIR /app

# System libs for OpenCV / PyMuPDF wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      libgl1 \
      libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
 && pip install -r /app/requirements.txt

COPY backend/app /app/app

# Test-only stage. Not the default image (`docker build` stops at runtime).
FROM base AS test

COPY backend/requirements-dev.txt /app/requirements-dev.txt
RUN pip install -r /app/requirements-dev.txt

COPY backend/tests /app/tests
COPY backend/pytest.ini /app/pytest.ini
COPY backend/.coveragerc /app/.coveragerc

ENV DOC2ANY_ENV=development \
    DOC2ANY_DATA_DIR=/tmp/doc2any-data \
    DOC2ANY_CLEANUP_ENABLED=false

RUN mkdir -p /tmp/doc2any-data

CMD ["python", "-m", "pytest"]

# Default production image. Keep this stage last.
FROM base AS runtime

RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /data/uploads /data/outputs \
 && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${DOC2ANY_PORT}/api/health" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host ${DOC2ANY_HOST} --port ${DOC2ANY_PORT} --proxy-headers --forwarded-allow-ips='*'"]
