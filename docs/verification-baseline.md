# Verification Baseline

## Purpose

Keep a clear verification baseline in place before Stage 10.2 and Stage 10.3 work.

## Verification Types

### Mocked and Unit Verification

Use the Django test suite for fast local checks of:

- request validation
- PDF parsing and text cleaning
- prompt generation rules
- Ollama client retry and error translation
- frontend smoke structure

Primary command:

```bash
.venv/bin/python manage.py test backend.api.tests --verbosity 1
```

This coverage is valuable, but it does not prove that the current local Ollama runtime is reachable or that the configured model can return a valid classification response end-to-end.

### Live Runtime Verification

Use the management command below to exercise the real `/api/classify/` endpoint path in-process against the current local configuration:

```bash
.venv/bin/python manage.py verify_live_classification
```

What this command verifies:

- `GET /api/health/` responds successfully
- a real sample PDF is generated and posted to `POST /api/classify/`
- the request passes through the actual PDF processing, prompt generation, Ollama call, and response validation layers

If the local Ollama runtime is unavailable, the command reports a skipped live verification instead of failing the baseline by default.

Use strict mode when live runtime availability is required:

```bash
.venv/bin/python manage.py verify_live_classification --strict
```

## Baseline Rule Before Stage 10.2 and 10.3

Before prompt-stability or performance changes:

1. Run the unit and mocked verification suite.
2. Run `verify_live_classification`.
3. Record whether the live run passed or was skipped due to unavailable local runtime.
