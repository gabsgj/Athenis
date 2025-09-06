# API Reference

Base URL: `/api/v1`

Authentication
- Header: `x-api-key: <your key>` (dev), or `Authorization: Bearer <token>`

Endpoints
- POST `/inference`
  - Body: `{ text: string, task: 'simplify'|'summarize'|'risk'|'full-analysis', language?: string }
  - 200: `{ plain_language?: string, overview?: string, risks_detected?: Array<...> }`

- POST `/stream` (Server-Sent Events)
  - Body: `{ text: string, task: 'simplify', language?: string }`
  - Events: `event: token\n data: <chunk>` until complete

- POST `/upload`
  - Body: `multipart/form-data` with `file`
  - 200: `{ text?: string, chunks?: Array<{ text: string }> }`

- GET `/health`
  - 200: `{ status: 'ok' }`

GoFr Ingestion Service
- POST `${GOFR_BASE_URL}/ingest`: `multipart/form-data` with `file`
- 200: `{ text?: string, chunks?: string[] }`

Notes
- Rate limiting returns 429
- Errors return `{ error, message }` with appropriate HTTP status
