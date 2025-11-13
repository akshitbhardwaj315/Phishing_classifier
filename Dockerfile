# ---- STAGE 1: The Builder ----
# This stage just installs dependencies
FROM python:3.10-slim AS builder

WORKDIR /app
COPY requirements.txt .

# [BEST PRACTICE] Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install all dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


# ---- STAGE 2: The Final, Clean Image ----
# This stage creates the small, final image
FROM python:3.10-slim AS final

WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /opt/venv /opt/venv

# --- THIS IS THE KEY ---
# Copy ALL project files. Hugging Face has already
# placed the *real* model.pkl file here for us.
COPY . .

# Activate the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Set the port from the Hugging Face environment variable
ENV PORT=${PORT:-8000}

# The "shell form" command that correctly uses the $PORT variable
CMD gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT main:app