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
- Will be implemented under `backend/pdf/`.

### Prompt Layer

- Builds strict JSON-oriented prompts for Gemma 4.
- Encapsulates allowed document classes and response instructions.
- Will be implemented under `backend/prompts/`.

### LLM Layer

- Wraps communication with the local Ollama runtime.
- Sends prompts to Gemma 4 and returns raw model output.
- Will be implemented under `backend/llm/`.

### Service Layer

- Orchestrates the full classification workflow.
- Coordinates parser, prompt builder, response validation, and API payload assembly.
- Will be implemented under `backend/services/`.

## Request Flow

1. User uploads a PDF from the browser UI rendered by Django.
2. JavaScript sends `multipart/form-data` to `POST /api/classify/`.
3. Django API validates the request and stores the file temporarily.
4. PDF parser extracts and cleans text.
5. Prompt builder creates a strict JSON-only classification prompt.
6. Ollama client sends the prompt to local Gemma 4.
7. Backend validates the model response.
8. Backend returns normalized JSON to the frontend.
9. The browser UI displays class, tags, confidence, and any errors.

## Current Stage 1 Implementation

- Root Django project scaffolded with `manage.py` and `backend/` settings package.
- Simple browser UI scaffolded with Django templates and static files.
- API routes reserved for `/api/health/` and `/api/classify/`.
- Layer directories created for `api`, `services`, `pdf`, `llm`, `prompts`, and shared schemas.
- Detailed implementation of parsing and inference is intentionally deferred to later stages.
