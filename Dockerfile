# syntax=docker/dockerfile:1.6

# ---------- Stage 1: builder ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# System deps needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment inside the image
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install CPU-only torch (much smaller than CUDA build)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies into the venv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ---------- Stage 2: runtime ----------
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy the whole virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY src/ ./src/
COPY dashboard/ ./dashboard/
COPY pyproject.toml ./

# Non-root user (security best practice)
RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /app/data/raw /app/data/exports \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]