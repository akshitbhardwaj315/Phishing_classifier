# --- STAGE 1: The Builder ---
FROM python:3.10-slim-bullseye AS builder

WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- STAGE 2: The Final Image ---
FROM python:3.10-slim-bullseye AS final

WORKDIR /app
RUN groupadd -g 1001 appuser && \
    useradd -r -u 1001 -g appuser appuser

COPY --from=builder /opt/venv /opt/venv
COPY . .

RUN chown -R appuser:appuser /app
ENV PATH="/opt/venv/bin:$PATH"
USER appuser

# --- NEW DEPLOYMENT CMD ---
# Use the $PORT variable provided by the platform (like Hugging Face),
# or default to 8000 if it's not set.
ENV PORT=${PORT:-8000}
CMD gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT main:app