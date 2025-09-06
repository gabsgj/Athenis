# syntax=docker/dockerfile:1
# CUDA base for GPU inference
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
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
