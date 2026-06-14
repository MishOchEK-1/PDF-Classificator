# Backend Setup

## Stage 2 Scope

This project uses a Django backend with:

- Django REST Framework for JSON APIs
- `django-cors-headers` for local browser access configuration
- local media storage for uploaded PDF files
- environment-driven settings for Ollama and upload constraints
- extracted-text optimization settings for large PDF handling

## Environment Variables

Create a local `.env` file based on `.env.example`.

Supported variables:

- `DJANGO_DEBUG`: enables or disables debug mode
- `DJANGO_SECRET_KEY`: Django secret key
- `DJANGO_ALLOWED_HOSTS`: comma-separated allowed hosts
- `CORS_ALLOWED_ORIGINS`: comma-separated allowed origins
- `OLLAMA_URL`: base URL for the local Ollama server
- `OLLAMA_MODEL`: default Ollama model name
- `OLLAMA_TIMEOUT_SECONDS`: request timeout for local inference
- `OLLAMA_MAX_RETRIES`: retry count for transient local runtime failures
- `OLLAMA_RETRY_DELAY_SECONDS`: delay between retries
- `MEDIA_ROOT`: root directory for stored media files
- `TEMP_UPLOAD_ROOT`: temporary directory for uploaded PDFs
- `MAX_UPLOAD_SIZE`: maximum accepted upload size in bytes
- `PDF_TEXT_CHUNK_SIZE`: target chunk size for optimized extracted text
- `PDF_TEXT_MAX_CHUNKS`: maximum number of chunks forwarded to prompting
- `PDF_TEXT_MAX_CHARACTERS`: maximum final character budget for extracted text

## Current Backend Conventions

- Browser UI is rendered by Django templates.
- API endpoints are exposed under `/api/`.
- Uploaded files are staged under `media/tmp/`.
- Classification remains synchronous in the current MVP design.
- Extracted text is cleaned before prompting.
- Large extracted text is reduced before prompting through chunking and truncation.
- The model never receives raw PDF files directly.

## Runtime Flow Summary

1. Upload request arrives at `POST /api/classify/`.
2. Request serializer validates file presence, extension, and size.
3. Uploaded PDF is stored temporarily under `TEMP_UPLOAD_ROOT`.
4. PyMuPDF extracts text from the stored file.
5. Extracted text is cleaned and optimized for prompt size.
6. Prompt is sent to the configured Ollama model.
7. Model response is validated and returned as API JSON.
