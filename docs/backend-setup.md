# Backend Setup

## Stage 2 Scope

This project uses a Django backend with:

- Django REST Framework for JSON APIs
- `django-cors-headers` for local browser access configuration
- local media storage for uploaded PDF files
- environment-driven settings for Ollama and upload constraints

## Environment Variables

Create a local `.env` file based on `.env.example`.

Supported variables:

- `DJANGO_DEBUG`: enables or disables debug mode
- `DJANGO_SECRET_KEY`: Django secret key
- `DJANGO_ALLOWED_HOSTS`: comma-separated allowed hosts
- `CORS_ALLOWED_ORIGINS`: comma-separated allowed origins
- `OLLAMA_URL`: base URL for the local Ollama server
- `OLLAMA_MODEL`: default Ollama model name
- `MEDIA_ROOT`: root directory for stored media files
- `TEMP_UPLOAD_ROOT`: temporary directory for uploaded PDFs
- `MAX_UPLOAD_SIZE`: maximum accepted upload size in bytes

## Current Backend Conventions

- Browser UI is rendered by Django templates.
- API endpoints are exposed under `/api/`.
- Uploaded files will be staged under `media/tmp/`.
- Classification remains synchronous in the current MVP design.
