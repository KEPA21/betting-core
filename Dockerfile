# === Builder ===
FROM python:3.11-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# Skapa EN venv och lägg den i PATH
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Installera deps
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Kopiera koden
COPY app app
COPY db db
COPY scripts scripts
COPY alembic.ini alembic.ini

# === Runtime ===
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# Ta med venv + app
COPY --from=builder /venv /venv
COPY --from=builder /app /app

# Kör som non-root (valfritt)
RUN useradd -u 10001 -m appuser
USER 10001

EXPOSE 8000
ENTRYPOINT ["/venv/bin/python","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
