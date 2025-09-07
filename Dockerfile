# syntax=docker/dockerfile:1

ARG TARGET=cpu
ARG DEBIAN_FRONTEND=noninteractive

# CPU Stage (for fast builds and Sandbox)
FROM python:3.11-slim AS cpu
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl gunicorn && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

RUN useradd -m -u 1001 appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8080
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:8080", "app.wsgi:application"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8080/api/v1/health || exit 1

# GPU Stage (for future production)
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 AS gpu
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:64
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-pip git curl libgl1-mesa-glx gunicorn && \
    rm -rf /var/lib/apt/lists/* && \
    ln -s /usr/bin/python3.11 /usr/bin/python && \
    ln -s /usr/bin/pip /usr/bin/pip3

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

RUN useradd -m -u 1001 appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8080
CMD ["gunicorn", "-w", "2", "-k", "gthread", "-b", "0.0.0.0:8080", "app.wsgi:application"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8080/api/v1/health || exit 1

# Final stage
FROM ${TARGET}
