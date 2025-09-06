# Legal Jargon / Global Document Simplifier

A production-capable Flask web app backed by a GPU LLM for simplifying legal documents, with a Go microservice for document ingestion (PDF/DOCX/TXT → text, chunking, language detection). Includes streaming SSE, risk detection (hybrid heuristics + LLM), caching, embeddings-based context selection, metrics, and Akash GPU deployment artifacts.

## Architecture

```mermaid
flowchart LR
  U[User Browser] -- HTTP/S + SSE --> F[Flask API + UI]
  subgraph Pod
    F <-- REST (internal) --> G[Go Ingestion Service]
    F --> M[(LRU/Redis Cache)]
    F --> E[Embeddings Index]
    F --> LLM[Transformers Model\n(GPU w/ bitsandbytes)]
  end
  F --> P[Prometheus /metrics]
```

- Flask serves the UI and API, performs inference, risk analysis, streaming, metrics, and caching.
- Go service ingests PDFs/DOCX/TXT, chunks text, detects language, and returns structured chunks.
- Embeddings (sentence-transformers) + vector search select relevant context for long docs.
- Optional Redis for cache; LRU fallback in-memory.
- Deployable to Akash GPU with the provided SDL and CI pipeline.

## Akash Deployment Checklist

- Container Registry
  - Set GHCR/DockerHub repo and credentials as GitHub secrets: `REGISTRY`, `REGISTRY_USERNAME`, `REGISTRY_PASSWORD`, `IMAGE_REPO`.
- Environment Variables
  - API_KEY: Required client API key for all endpoints.
  - MODEL_NAME: Default `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (open). Set to larger model (e.g., `meta-llama/Llama-2-7b-chat-hf`) for production.
  - QUANTIZE: `8bit` | `4bit` | `none` (default `8bit` if bitsandbytes is present).
  - REDIS_URL: Optional `redis://host:port/0` for cache.
  - EXTERNAL_LLM_API_URL: Optional fallback LLM endpoint if local model fails.
  - GOFR_URL: Internal URL of the Go service (default `http://gofr:8090`).
  - RATE_LIMIT_PER_MIN: Requests per minute per API key/IP (default 60).
  - CORS_ORIGINS: Optional comma-separated origins for UI.
- GPU
  - Request 1 GPU. Prefer A100/3090/V100.
  - Ensure CUDA 11/12 compatible nodes. Dockerfile uses CUDA 12 runtime.
  - If using bitsandbytes 4/8-bit, verify compute capability supported by node.
- bitsandbytes
  - QUANTIZE=8bit typically works out-of-the-box with CUDA base image.
  - If it fails on a given GPU, set QUANTIZE=none.
- Akash Console Steps
  1. Connect your GitHub repo.
  2. Build images via CI (or Akash Console build).
  3. Set environment variables in the deployment.
  4. Use provided `akash.yaml`.
  5. Expose TCP 8080 for Flask; keep Go service internal.

## Local Development

- Prereqs: Docker, optional NVIDIA GPU + drivers + nvidia-container-toolkit.
- Clone and run:

```bash
make dev
```

- Open http://localhost:8080
- API key (for dev): set `API_KEY` in a `.env` file or via environment.

### Using docker-compose directly

```bash
docker compose up --build
```

To enable GPU locally, run (Windows PowerShell):

```powershell
docker compose --profile gpu up --build
```

## How it works

- Upload a document or paste text.
- Go service extracts text, chunks, and detects language.
- Flask embeds chunks, summarizes, and runs the final prompt with relevant context.
- Risk detector uses regex heuristics first, then LLM validates and adds structured risk objects.
- Streaming SSE sends tokens as they are generated.

## Endpoints

- POST /api/v1/inference
- POST /api/v1/stream (SSE)
- POST /api/v1/upload (forwards to Go service)
- GET /api/v1/health
- GET /metrics

See example payloads in the bottom of this README.

## Configuration (.env)

See `.env.example` for all variables.

## Testing

```bash
make test
```

## Build images

```bash
make build
```

## Deploy to Akash

- Ensure `akash` CLI and provider access as per Akash docs.
- Fill secrets in GitHub Actions to push images.
- Use `akash.yaml` (SDL) in Akash Console or CLI.

## Example Requests

- Simplify
```bash
curl -X POST http://localhost:8080/api/v1/inference \
  -H "Content-Type: application/json" \
  -H "x-api-key: $env:API_KEY" \
  -d '{"text":"This Non-Disclosure Agreement ...","task":"simplify","language":"auto"}'
```

- Stream
```bash
curl -N -X POST http://localhost:8080/api/v1/stream \
  -H "x-api-key: $env:API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text":"...","task":"simplify","language":"auto"}'
```

- Upload
```bash
curl -X POST http://localhost:8080/api/v1/upload \
  -H "x-api-key: $env:API_KEY" \
  -F file=@samples/nda.txt
```

## Troubleshooting

- Health: GET /api/v1/health
- Metrics: GET /metrics
- Logs: Structured JSON via structlog. Check container logs.
- Fallback Mode: If GPU model fails, set `EXTERNAL_LLM_API_URL` to a hosted LLM endpoint; requests will fallback automatically.

## License

MIT

---

This repository is designed to be practical and runnable locally with a small open model. For production, swap to a larger model and enable GPU.
