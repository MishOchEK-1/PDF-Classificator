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

Reserved endpoint for the full PDF classification pipeline.

### Request

- Content type: `multipart/form-data`
- Field: `file`
- Accepted file type: PDF

### Target Success Response `200 OK`

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

### Stage 1 Temporary Response `501 Not Implemented`

```json
{
  "detail": "Classification pipeline is not implemented yet.",
  "expected_response": {
    "class": "technical_documentation",
    "tags": [
      "python",
      "backend",
      "api"
    ],
    "confidence": 0.92
  }
}
```

## Planned Error Cases

- `400 Bad Request`: missing file, invalid extension, invalid PDF payload.
- `408 Request Timeout`: local inference exceeded configured timeout.
- `422 Unprocessable Entity`: PDF parsed successfully but no usable text was extracted.
- `503 Service Unavailable`: Ollama or the target model is unavailable.
