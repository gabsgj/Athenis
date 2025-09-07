# syntax=docker/dockerfile:1
FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY . .
RUN --mount=type=cache,target=/go/pkg/mod \
	--mount=type=cache,target=/root/.cache/go-build \
	cd gofr && go build -o /out/gofr

FROM alpine:3.20
WORKDIR /app
RUN apk add --no-cache python3 py3-pip && \
	pip3 install --no-cache-dir pdfminer.six python-docx
COPY --from=builder /out/gofr /usr/local/bin/gofr
# Copy Python extraction helper from repo root context
COPY app/utils /app/app/utils
EXPOSE 8090
ENTRYPOINT ["/usr/local/bin/gofr"]
