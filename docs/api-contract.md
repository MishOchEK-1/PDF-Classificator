# API Contract

## `GET /api/health/`

Used for local health checks by the browser UI and development tooling.

### Response `200 OK`

```json
{
  "status": "ok",
  "service": "pdf-classification-backend",
  "ollama_url": "http://localhost:11434"
}
```

## `POST /api/classify/`

Runs the synchronous end-to-end PDF classification pipeline.

### Request

- Content type: `multipart/form-data`
- Field: `file`
- Accepted file type: PDF
- Validation:
  - file is required
  - extension must be `.pdf`
  - size must not exceed `MAX_UPLOAD_SIZE`

### Success Response `200 OK`

```json
{
  "class": "technical_documentation",
  "tags": [
    "python",
    "backend",
    "api"
  ],
  "confidence": 0.92
}
```

### Error Responses

- `400 Bad Request`
  - missing file
  - invalid extension
  - empty upload
  - file exceeds `MAX_UPLOAD_SIZE`
- `422 Unprocessable Entity`
  - corrupted PDF
  - scanned PDF without extractable text
  - parsed PDF without usable content after cleaning
- `502 Bad Gateway`
  - model returned invalid JSON or invalid classification payload
  - upstream Ollama request failed unexpectedly
- `503 Service Unavailable`
  - Ollama server is unavailable
  - configured model is unavailable
- `504 Gateway Timeout`
  - local inference exceeded configured timeout after retries

### Processing Notes

- Uploaded PDFs are stored temporarily under `TEMP_UPLOAD_ROOT`.
- Text is extracted before any model call.
- Cleaned text is optimized before prompting by:
  - chunking long extracted text
  - limiting the number of chunks
  - truncating the final promptable text payload
- The backend returns the final classification in the same request cycle.
