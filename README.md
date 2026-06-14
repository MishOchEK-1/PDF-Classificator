# PDF Classificator

Local-first web application for PDF document classification with Django, PyMuPDF, and Ollama.

The app accepts a PDF upload, extracts text locally, sends the cleaned text to a local Gemma model through Ollama, and returns a structured classification response with:

- document class
- tags
- confidence score

## Features

- local PDF upload UI served by Django
- drag-and-drop upload with live pipeline progress
- synchronous `/api/classify/` endpoint
- PDF text extraction with PyMuPDF
- text cleaning, chunking, and truncation for large PDFs
- strict JSON-oriented prompting for stable model output
- Ollama integration with retry, timeout, and availability handling
- frontend rendering for success and error states
- unit, service, API, and frontend smoke tests
- live end-to-end verification command for local Ollama runtime

## Tech Stack

- Python
- Django
- Django REST Framework
- vanilla HTML/CSS/JavaScript
- PyMuPDF
- Ollama
- Gemma 4

## How It Works

1. User uploads a PDF from the browser UI.
2. Django validates and stores the file temporarily.
3. PyMuPDF extracts readable text.
4. The backend cleans and optimizes extracted text.
5. A strict classification prompt is built for the local model.
6. Ollama runs the prompt against Gemma.
7. The backend validates the JSON response.
8. The frontend displays class, tags, confidence, and any errors.

## Current Defaults

- model: `gemma4:e2b`
- Ollama timeout: `90` seconds
- retries: `2`
- keep-alive after last request: `5m`

## Quick Start

### 1. Clone and enter the project

```bash
git clone https://github.com/MishOchEK-1/PDF-Classificator.git
cd PDF-Classificator
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Important variables:

- `OLLAMA_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`
- `OLLAMA_KEEP_ALIVE`
- `MAX_UPLOAD_SIZE`

### 5. Pull the model in Ollama

```bash
ollama pull gemma4:e2b
```

### 6. Start Ollama

```bash
ollama serve
```

If you see `address already in use`, Ollama is already running and you can keep using the existing instance.

### 7. Start Django

```bash
.venv/bin/python manage.py runserver
```

Open:

- `http://127.0.0.1:8000/`

## API

### `GET /api/health/`

Health-check endpoint used by the UI and verification tooling.

Example response:

```json
{
  "status": "ok",
  "service": "pdf-classification-backend",
  "ollama_url": "http://localhost:11434"
}
```

### `POST /api/classify/`

Synchronous classification endpoint.

Request:

- content type: `multipart/form-data`
- field: `file`
- accepted type: PDF

Example success response:

```json
{
  "class": "technical_documentation",
  "tags": ["python", "backend", "api"],
  "confidence": 0.92
}
```

Common error statuses:

- `400` invalid upload
- `422` unreadable or empty PDF content
- `502` invalid upstream model response
- `503` Ollama or model unavailable
- `504` local inference timeout

## Verification

Run the test suite:

```bash
.venv/bin/python manage.py test backend.api.tests --verbosity 1
```

Run live end-to-end verification against your local Ollama runtime:

```bash
.venv/bin/python manage.py verify_live_classification
```

Strict mode:

```bash
.venv/bin/python manage.py verify_live_classification --strict
```

## Project Structure

```text
backend/
  api/          HTTP endpoints, serializers, tests, management commands
  llm/          Ollama client
  pdf/          PDF storage, extraction, cleaning, optimization
  prompts/      prompt templates and response validation
  services/     classification orchestration
static/         frontend CSS and JavaScript
templates/      Django HTML templates
docs/           architecture, API, setup, and verification docs
```

## Limitations

- classification is synchronous
- scanned PDFs without extractable text are not OCR-processed
- there is no auth, upload history, or async job queue yet
- output quality depends on the local Ollama runtime and selected model

## Documentation

- [Architecture](docs/architecture.md)
- [API Contract](docs/api-contract.md)
- [Backend Setup](docs/backend-setup.md)
- [Verification Baseline](docs/verification-baseline.md)
- [Project Structure](docs/project-structure.md)

## Roadmap Ideas

- OCR for scanned PDFs
- multi-label classification
- document summarization
- vector search and RAG
- authentication and upload history
