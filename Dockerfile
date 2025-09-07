# syntax=docker/dockerfile:1
ARG FAST_BUILD=0
ARG DEBIAN_FRONTEND=noninteractive

# Use CPU-only slim base for sandbox fast builds; fall back to CUDA for GPU-capable deployments
FROM python:3.11-slim AS cpu
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-min.txt ./
RUN pip install --no-cache-dir -r requirements-min.txt
COPY app ./app
COPY .env.example ./
ENV PORT=8080
EXPOSE 8080
RUN useradd -m -u 1001 appuser && chown -R 1001:1001 /app
USER appuser
CMD ["python", "-m", "app.app"]

FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 AS gpu

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv git curl libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd -m -u 1001 appuser
WORKDIR /app

# Copy python code
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app ./app
COPY .env.example ./
ENV PORT=8080
EXPOSE 8080
USER appuser
CMD ["python3", "-m", "app.app"]

# Default to CPU stage as final image (Sandbox-friendly). Use --target gpu for GPU builds.
FROM cpu
