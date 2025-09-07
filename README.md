# ATHENIS – Legal Jargon / Global Document Simplifier

## 🚀 Deploy on Akash Sandbox

1. Push repo to GitHub main branch.  
2. Wait for GitHub Actions to finish.  
3. Your Docker image will be available at:  
```
ghcr.io/gabsgj/hackodisha/athenis:latest
```
4. Open [Akash Sandbox Console](https://console.akash.network/sandbox).  
5. Deploy app → set **Image** = URL above.  
6. Set **Port = 8080**.  
7. (Optional) Add env vars like `API_KEY=secret123`.  
8. Deploy → you'll get a public URL 🎉.

---

A **production-ready Flask web app** powered by GPU-based LLMs for simplifying legal documents.
Backed by a **Go microservice** for document ingestion (PDF/DOCX/TXT → text, chunking, language detection).

✨ Features:

* Simplification & summarization of contracts in plain language
* Risk detection (regex + LLM hybrid)
* Streaming token responses (SSE)
* Caching (Redis + LRU fallback)
* Embeddings-based context selection for long docs
* Metrics with Prometheus
* GPU deployment artifacts for **Akash Network**

---

## 🏗️ Architecture

              ┌─────────────────┐
              │   User Browser  │
              └────────┬────────┘
                       │ HTTP/S + SSE
                       ▼
              ┌─────────────────┐
              │ Flask API + UI  │
              └───────┬─────────┘
      ┌──────────────┼───────────────┐
      │              │               │
      ▼              ▼               ▼
      ┌─────────────────┐ ┌─────────────┐ ┌─────────────────────────┐
      │ Go Ingestion │ │ LRU/Redis │ │ Embeddings Index │
      │ Service │ │ Cache │ │ (sentence-transformers) │
      └─────────────────┘ └─────────────┘ └─────────────────────────┘
      │
      ▼
      ┌─────────────────────────────┐
      │ Transformers Model (GPU) │
      │ with bitsandbytes │
      └─────────────────────────────┘

Flask API also exposes metrics to Prometheus:

              ┌─────────────────┐
              │  Prometheus     │
              │   /metrics      │
              └─────────────────┘

* **Flask** → API, UI, inference, risk analysis, streaming, metrics
* **Go service** → ingestion of PDFs/DOCX/TXT, chunking, language detection
* **Embeddings** → relevant context selection (sentence-transformers)
* **Cache** → Redis (optional) or in-memory fallback
* **Deployment** → Akash GPU-ready (CUDA 12, bitsandbytes 4/8-bit)

---

## 🚀 Quick Start (Local)

### Requirements

* Docker & Docker Compose
* (Optional) NVIDIA GPU + nvidia-container-toolkit

### Run

```bash
make dev
```

Then open: **[http://localhost:8080](http://localhost:8080)**

Or directly with Compose:

```bash
docker compose up --build
```

Enable GPU (PowerShell example):

```powershell
docker compose --profile gpu up --build
```

---

## ⚙️ Configuration

Set variables via `.env` or CI/CD secrets.

| Variable               | Description                       | Default                              |
| ---------------------- | --------------------------------- | ------------------------------------ |
| `API_KEY`              | Required API key for clients      | –                                    |
| `MODEL_NAME`           | LLM model name                    | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` |
| `QUANTIZE`             | `8bit` / `4bit` / `none`          | `8bit`                               |
| `REDIS_URL`            | Redis cache URL                   | –                                    |
| `EXTERNAL_LLM_API_URL` | Optional fallback LLM endpoint    | –                                    |
| `GOFR_URL`             | Go ingestion service              | `http://gofr:8090`                   |
| `RATE_LIMIT_PER_MIN`   | Requests per minute per client    | `60`                                 |
| `CORS_ORIGINS`         | Allowed origins (comma-separated) | –                                    |

See `.env.example` for full list.

---

## 📡 Endpoints

* `POST /api/v1/inference` – run tasks (`simplify`, `summarize`, `translate`)
* `POST /api/v1/stream` – streaming version (SSE)
* `POST /api/v1/upload` – upload docs (forwards to Go service)
* `GET /api/v1/health` – health check
* `GET /metrics` – Prometheus metrics

---

## 🔍 Example Requests

### Simplify

```bash
curl -X POST http://localhost:8080/api/v1/inference \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text":"This NDA ...","task":"simplify","language":"auto"}'
```

### Stream (SSE)

```bash
curl -N -X POST http://localhost:8080/api/v1/stream \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text":"...","task":"simplify"}'
```

### Upload

```bash
curl -X POST http://localhost:8080/api/v1/upload \
  -H "x-api-key: $API_KEY" \
  -F file=@samples/nda.txt
```

---

## 🧪 Testing

```bash
make test
```

---

## 📦 Building Images

```bash
make build
```

---

## ☁️ Deploy to Akash

1. Set up registry secrets in GitHub (`REGISTRY`, `REGISTRY_USERNAME`, `REGISTRY_PASSWORD`, `IMAGE_REPO`).
2. Run CI/CD (see `.github/workflows/ci.yml`).
3. Use `akash.yaml` to deploy.
4. Expose TCP port `8080` (Flask). Keep Go service internal.

---

## 🛠️ Troubleshooting

* **Health check** → `GET /api/v1/health`
* **Metrics** → `GET /metrics`
* **Logs** → check container logs (JSON via structlog)
* **GPU fails** → set `QUANTIZE=none` or use `EXTERNAL_LLM_API_URL` fallback

## Privacy & Ethical Standards

This project strictly adheres to ethical and privacy standards:

- **User Data Handling:** Uploaded documents (PDF, DOCX, TXT) are processed in-memory and not stored persistently unless explicitly cached for performance. Users can clear their session cache at any time.
- **Data Security:** All API requests require a valid API key. Sensitive data is not logged in plaintext.
- **Compliance:** No personally identifiable information (PII) is shared with third parties. All processing happens within the container or via optional, user-configured     LLM endpoints.
- **Responsible AI:** Risk detection and simplification outputs are generated for informational purposes. They do not constitute legal advice.
- **Transparency:** The system logs and metrics are structured to provide operational insights without exposing user data.

---

## 📜 License

MIT

---

✨ This repo runs locally with **TinyLlama** but is production-ready with larger models + GPUs.

---
