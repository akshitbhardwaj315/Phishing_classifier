# ---- STAGE 1: The Builder ----
# This stage installs all dependencies, including LFS
FROM python:3.10-slim AS builder

# Install git and git-lfs (This is the new, important part)
RUN apt-get update && apt-get install -y git git-lfs && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy ALL project files (including LFS pointers and .gitattributes)
COPY . /app

# --- THIS IS THE MAGIC COMMAND ---
# Run git lfs pull to download the *real* model.pkl file from LFS storage
RUN git lfs pull

# [BEST PRACTICE] Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install all dependencies from requirements.txt
# (This caches them in this layer)
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


# ---- STAGE 2: The Final, Clean Image ----
# This stage creates the small, final image for production
FROM python:3.10-slim AS final

# Set the working directory
WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /opt/venv /opt/venv

# Copy the entire application, which now includes the *real* model.pkl
COPY --from=builder /app /app

# Activate the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Set the port from the Hugging Face environment variable
ENV PORT=${PORT:-8000}

# This is the "shell form" command that correctly uses the $PORT variable
# to run your app
CMD gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT main:app