# Project Structure

## Target Layout

```text
PDFConvertor/
├── .env.example
├── .venv/
├── ProjectContext/
├── backend/
│   ├── api/
│   ├── llm/
│   ├── models/
│   ├── pdf/
│   ├── prompts/
│   ├── services/
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── docs/
├── manage.py
├── media/
│   └── tmp/
├── static/
│   ├── css/
│   └── js/
├── templates/
└── requirements.txt
```

## Layer Intent

- `backend/api/`: REST views, serializers, route registration, and HTTP-facing validation.
- `backend/services/`: orchestration of the classification pipeline.
- `backend/pdf/`: file handling and text extraction helpers.
- `backend/llm/`: Ollama client and response parsing.
- `backend/prompts/`: prompt templates and builders.
- `backend/models/`: shared domain schemas for classification results.
- `media/`: local runtime storage for uploaded documents and temporary files.
- `templates/`: HTML templates rendered by Django.
- `static/`: browser-facing CSS and JavaScript assets.
- `.env.example`: local configuration template for backend environment variables.
- `docs/`: living implementation docs for architecture and contracts.
- `ProjectContext/`: persistent handoff context for future chats and agents.
