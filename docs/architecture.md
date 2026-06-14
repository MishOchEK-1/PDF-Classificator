# PDF Classification Architecture

## Goal

Provide a modular local-first pipeline for PDF document classification using Django, plain HTML/CSS/JS, and Gemma 4 via Ollama.

## Service Boundaries

### Web UI

- Responsible for PDF upload UX, loading states, and result visualization.
- Talks only to the Django REST API.
- Lives in Django templates and static assets.

### Backend API

- Owns request validation and HTTP response formatting.
- Exposes health check and classification endpoints.
- Delegates all business logic to internal services.

### PDF Processing Layer

- Handles temporary file storage, PDF validation, and text extraction.
- Produces normalized text for prompt generation.
- Applies pre-prompt text optimization for large PDFs through chunking and truncation.
- Implemented under `backend/pdf/`.

### Prompt Layer

- Builds strict JSON-oriented prompts for Gemma 4.
- Encapsulates allowed document classes and response instructions.
- Implemented under `backend/prompts/`.

### LLM Layer

- Wraps communication with the local Ollama runtime.
- Sends prompts to Gemma 4 and returns raw model output.
- Handles retries, timeout translation, and unavailable runtime states.
- Implemented under `backend/llm/`.

### Service Layer

- Orchestrates the full classification workflow.
- Coordinates parser, prompt builder, response validation, and API payload assembly.
- Implemented under `backend/services/`.

## Request Flow

1. User uploads a PDF from the browser UI rendered by Django.
2. JavaScript sends `multipart/form-data` to `POST /api/classify/`.
3. Django API validates the request and stores the file temporarily.
4. PDF parser extracts readable text from all pages.
5. Text cleaner normalizes spacing and line breaks.
6. Text optimizer limits large extracted text by chunking and truncation.
7. Prompt builder creates a strict JSON-only classification prompt.
8. Ollama client sends the prompt to local Gemma through Ollama.
9. Backend validates the model response against the classification schema.
10. Backend returns normalized JSON to the frontend.
11. The browser UI displays class, tags, confidence, progress states, and errors.

## Implemented Components

- Django-served homepage at `/` with upload and result UI.
- API endpoints at `/api/health/` and `/api/classify/`.
- Temporary PDF storage with automatic cleanup of expired files.
- PDF text extraction through PyMuPDF.
- Structured text cleaning and prompt-ready text optimization.
- Prompt generation with strict JSON-only instructions.
- Ollama integration with timeout and retry handling.
- Response validation for class, tags, and confidence.
- Synchronous end-to-end classification response flow.
