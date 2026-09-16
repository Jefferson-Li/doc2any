# Doc2Any — Python FastAPI + static UI
FROM python:3.13-slim-bookworm

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

RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /data/uploads /data/outputs \
 && chown -R appuser:appuser /app /data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${DOC2ANY_PORT}/api/health" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host ${DOC2ANY_HOST} --port ${DOC2ANY_PORT} --proxy-headers --forwarded-allow-ips='*'"]
