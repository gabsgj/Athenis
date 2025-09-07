# API Documentation

This document provides details for the Athenis API, which offers text analysis services including simplification, summarization, translation, and comprehensive analysis.

---

## Authentication

All `/api/*` endpoints require an API key to be passed in the `X-API-Key` header.

**Example:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" ...
```

---

## Endpoints

### Health Check

- **GET** `/api/v1/health`
  - **Description:** Checks the health of the service.
  - **Response:**
    ```json
    {
      "ok": true,
      "status": "ready",
      "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
      "device": "cpu"
    }
    ```

### Metrics

- **GET** `/metrics`
  - **Description:** Returns Prometheus-compatible metrics. Requires API key.
  - **Response:** (Content-Type: `text/plain`)
    ```
    # HELP python_gc_objects_collected_total Objects collected during gc
    # TYPE python_gc_objects_collected_total counter
    python_gc_objects_collected_total{generation="0"} 10.0
    ...
    ```

### Simplify

- **POST** `/api/simplify`
  - **Description:** Simplifies the provided text.
  - **Request Body:**
    ```json
    {
      "text": "The party of the first part..."
    }
    ```
  - **Response:**
    ```json
    {
      "ok": true,
      "result": "The first party..."
    }
    ```

### Summarize

- **POST** `/api/summarize`
  - **Description:** Summarizes the provided text.
  - **Request Body:**
    ```json
    {
      "text": "This is a long document..."
    }
    ```
  - **Response:**
    ```json
    {
      "ok": true,
      "result": "This is a short summary."
    }
    ```

### Translate

- **POST** `/api/translate`
  - **Description:** Translates the text to the target language.
  - **Request Body:**
    ```json
    {
      "text": "Hello world",
      "target_lang": "hi"
    }
    ```
  - **Response:**
    ```json
    {
      "ok": true,
      "result": "नमस्ते दुनिया"
    }
    ```

### Full Analysis

- **POST** `/api/full-analysis`
  - **Description:** Provides a comprehensive analysis of the text.
  - **Request Body:**
    ```json
    {
      "text": "This agreement automatically renews..."
    }
    ```
  - **Response:**
    ```json
    {
      "ok": true,
      "result": {
        "simplified": "This agreement will renew by itself...",
        "summary": "A summary of the agreement.",
        "risk": [
          {
            "id": "auto_renew-1",
            "type": "auto_renew",
            ...
          }
        ]
      }
    }
    ```

### Generic Inference (with Streaming)

- **POST** `/api/v1/inference`
  - **Description:** A generic endpoint for all tasks, with support for Server-Sent Events (SSE) streaming.
  - **Request Body:**
    ```json
    {
      "text": "This is a test.",
      "task": "simplify", // "summarize", "translate"
      "target_lang": "en", // optional
      "stream": true // optional, default: false
    }
    ```
  - **Non-Stream Response:**
    ```json
    {
      "ok": true,
      "result": "This is a test."
    }
    ```
  - **SSE Stream Response:**
    ```
    event: chunk
    data: This 

    event: chunk
    data: is a 

    event: chunk
    data: test.

    event: done
    data: {}
    ```

