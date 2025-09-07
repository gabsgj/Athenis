# Error Codes Documentation

This document describes all error codes returned by the backend API under `app/`.

---

## General Errors

| Code  | Message                        | Description                                                                 |
|-------|--------------------------------|-----------------------------------------------------------------------------|
| 1001  | Missing API key                | The request did not include an API key in the headers.                      |
| 1002  | Invalid API key                | The provided API key is not valid or expired.                               |
| 1003  | Unauthorized                   | The client is not authorized to access this resource.                       |
| 1004  | Invalid request payload        | The request body is malformed or missing required fields.                   |
| 1005  | Unsupported mode               | The `mode` parameter provided is not supported (must be simplify/summarize/translate). |
| 1006  | Internal server error          | A generic error occurred on the backend.                                    |

---

## Document Analysis Errors

| Code  | Message                        | Description                                                                 |
|-------|--------------------------------|-----------------------------------------------------------------------------|
| 2001  | Text not provided              | The request body is missing the `text` field.                               |
| 2002  | Translation language not set   | The request did not specify a target language for translation.              |
| 2003  | Translation failure            | The translation service failed to process the text.                         |
| 2004  | Summarization failure          | The summarization service failed to process the text.                       |
| 2005  | Simplification failure         | The simplification service failed to process the text.                      |

---

## Full Analysis Errors

| Code  | Message                        | Description                                                                 |
|-------|--------------------------------|-----------------------------------------------------------------------------|
| 3001  | Risk analysis module failure   | Error occurred while calling teammate 2’s risk detection logic.             |
| 3002  | Full-analysis processing error | Combined analysis (simplify + summarize + risk) could not complete.         |

---

## Notes
- All error responses follow this JSON structure:

```json
{
  "error": true,
  "code": 1004,
  "message": "Invalid request payload"
}
