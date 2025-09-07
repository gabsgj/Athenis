# 📘 Ingest Microservice (Go + Python)

This service ingests legal documents (TXT, PDF, DOCX), extracts text, splits into chunks (~500 words), detects language, and returns JSON.

---

## ▶ Start the Service

### Local (without Docker)
```powershell
cd gofr
go run main.go
