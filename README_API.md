# API Reference

## Auth
- Send `x-api-key: <API_KEY>` header with every request.

## POST /api/v1/inference
- Body: `{ "text": "...", "task": "simplify|risk|summarize", "language": "auto|en|..." }`
- Response: `{ overview, plain_language, clause_explanations[], risks_detected[], meta }`

## POST /api/v1/stream (SSE)
- Body same as inference.
- Events:
  - `event: progress` data: `{ stage: start|finish }`
  - `event: token` data: partial text token
  - `event: done`
  - `event: error`

## POST /api/v1/upload
- Multipart form: `file=@path` or `text=<string>`
- Response: `{ upload_id, text?, chunks[] }`

## GET /api/v1/health
- Response: `{ status, gpu, model }`

## GET /metrics
- Prometheus exposition
