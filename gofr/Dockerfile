# syntax=docker/dockerfile:1
FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY . .
RUN --mount=type=cache,target=/go/pkg/mod \
	--mount=type=cache,target=/root/.cache/go-build \
	cd gofr && go build -o /out/gofr

# Use Ubuntu for better Python package compatibility
FROM ubuntu:22.04
WORKDIR /app

# Install Python and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    && pip3 install --no-cache-dir pdfminer.six python-docx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /out/gofr /usr/local/bin/gofr
# Copy Python extraction helper from repo root context
COPY app/utils /app/app/utils
EXPOSE 8090
ENTRYPOINT ["/usr/local/bin/gofr"]
