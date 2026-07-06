# =============================================================================
# Dockerfile — Backend Container (meal-planner-assistant)
# =============================================================================
# Single-stage build for a FastAPI server running under uvicorn on port 8080.
#
# Build args (optional metadata):
#   COMMIT_SHA    — Git commit hash (for tracing deployed versions)
#   AGENT_VERSION — Semantic version of the ADK agent
#
# Runtime env vars (set via Cloud Run, NOT baked in):
#   GOOGLE_API_KEY, AI_ENABLED, DATABASE_URL, FATSECRET_CLIENT_ID, ... see backend-env.json
#
# Deployed to: Cloud Run (us-east1)
# =============================================================================

FROM python:3.12-slim

# uv is a fast Python package manager (replaces pip/poetry)
RUN pip install --no-cache-dir uv==0.8.13

WORKDIR /code

# Copy dependency manifest first (leverage Docker layer caching)
COPY ./pyproject.toml ./README.md ./uv.lock* ./

# Copy application source
COPY ./app ./app

# Install all dependencies (locked versions from uv.lock)
RUN uv sync --frozen

# ---- Optional build metadata (injected by Cloud Build or CI) ----
ARG COMMIT_SHA=""
ENV COMMIT_SHA=${COMMIT_SHA}

ARG AGENT_VERSION=0.0.0
ENV AGENT_VERSION=${AGENT_VERSION}

# Cloud Run expects the container to listen on PORT=8080
EXPOSE 8080

# Start the FastAPI app via uvicorn
#   app.fast_api_app:app  — the ASGI app exported from fast_api_app.py
#   --host 0.0.0.0        — bind on all interfaces inside the container
#   --port 8080           — listen on the expected port
CMD ["uv", "run", "uvicorn", "app.fast_api_app:app", "--host", "0.0.0.0", "--port", "8080"]
