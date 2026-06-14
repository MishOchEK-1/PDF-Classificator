# AI PDF Document Classification System — Work Plan

## Implementation Status Snapshot — 2026-05-30

- Django project scaffolded in repository root with `manage.py` and `backend/`.
- Frontend strategy changed from React to simple Django-served HTML/CSS/JS.
- GitHub accounting rule added on 2026-05-30:
  - after each major completed block of tasks, create a dedicated git commit;
  - push the updated state to the GitHub repository;
  - reflect the completed block and push status in this plan file.
- GitHub publication status on 2026-05-30:
  - local git history initialized for this project;
  - remote `origin` configured for `https://github.com/MishOchEK-1/PDF-Classificator.git`;
  - initial foundation commit created: `802842b`;
  - follow-up commits created: `729582b` and `48f24c7`;
  - branch `main` successfully pushed to `origin`;
  - GitHub repository is now synchronized with the local project state.
- Stage 1 verified on 2026-05-30:
  - architecture, structure, and API contract checked against the current codebase;
  - synchronous MVP flow confirmed: `POST /api/classify/` returns the classification result directly;
  - no separate result retrieval endpoint is required unless async processing is introduced later.
- Stage 1.1 completed:
  - architecture boundaries documented in `docs/architecture.md`;
  - API request flow mapped to `/api/health/` and `/api/classify/`.
- Stage 1.2 completed:
  - backend module folders created: `api`, `services`, `pdf`, `llm`, `prompts`, `models`;
  - simple web UI scaffold created through `templates/` and `static/`.
- Stage 1.3 completed:
  - API contract documented in `docs/api-contract.md`;
  - Django route stubs added for health check and future classification endpoint.
  - local verification completed for `/api/health/` and `/api/classify/`.
- Stage 2 verified on 2026-05-30:
  - Django project, DRF, CORS, media handling, and temp upload storage verified;
  - backend modules `api`, `services`, `pdf`, `llm`, and `prompts` verified;
  - environment-driven settings added through `.env`/`.env.example`;
  - smoke tests added for health check and classification endpoint shape.
- Stage 2 completed on 2026-05-30:
  - Django settings moved to environment-driven configuration;
  - local media and temp upload directories configured;
  - upload size limit and Ollama connection settings introduced.
- Stage 3.1 completed on 2026-06-05:
  - browser UI template confirmed at `/`;
  - static CSS and JavaScript connected through Django static files;
  - browser JavaScript connected to `/api/health/` and `/api/classify/`;
  - CSRF handling added for same-origin API POST requests.
- Stage 3.2 completed on 2026-06-05:
  - PDF upload form remains available on the homepage;
  - drag-and-drop support added for PDF selection;
  - upload button kept as the primary submission control;
  - loading indicator added during API submission.
- Stage 3.3 completed on 2026-06-05:
  - result interface split into class, confidence, tags, and errors;
  - frontend now renders API responses into dedicated visual blocks instead of raw JSON only.
- Stage 4 completed on 2026-06-05:
  - `/api/classify/` now validates uploaded PDF extension and file size;
  - uploaded PDFs are stored temporarily with unique filenames;
  - old temporary PDF files are cleaned up automatically;
  - text extraction implemented through PyMuPDF;
  - extracted text is cleaned before further processing;
  - corrupted PDFs, empty PDFs, scanned PDFs without text, and unsupported file types are handled with explicit API errors.
- Stage 5 completed on 2026-06-05:
  - prompt template implemented for text-only Gemma classification;
  - prompt now explicitly requires JSON-only output without markdown or explanations;
  - model response validation implemented for JSON syntax, required fields, confidence range, and tag format.
- Stage 6 completed on 2026-06-05:
  - Ollama client implemented for POST requests to the local runtime;
  - raw Ollama responses are parsed into generated text content;
  - timeout handling and retry logic added for unstable requests;
  - unavailable server/model states now raise explicit client errors.
- Stage 7 completed on 2026-06-05:
  - end-to-end backend classification pipeline now chains PDF processing, prompt generation, Ollama inference, and response validation;
  - `/api/classify/` now returns the final `class/tags/confidence` JSON payload on success;
  - pipeline timeout, model availability, and invalid-model-response failures are translated into API errors.
- Stage 8 completed on 2026-06-05:
  - browser UI now uploads PDFs to the live classification endpoint and renders the returned classification JSON;
  - frontend displays upload progress together with separate processing and inference states;
  - frontend maps invalid PDF, parsing, Ollama, timeout, and generic API failures into dedicated error messages.
- Stage 9 completed on 2026-06-05:
  - backend tests now cover upload endpoint behavior, PDF parsing, prompt generation, Ollama communication, and JSON validation;
  - frontend-oriented tests now cover upload flow structure, loading state assets, result rendering structure, and error-rendering hooks;
  - classification tests now exercise all supported document classes.

## Project Overview

Develop a web application for automatic PDF document classification using a locally deployed Gemma 4 E4B model running through Ollama.

The model does not receive PDF files directly.

Before classification, every uploaded PDF must be processed through a text extraction pipeline that converts document content into plain text suitable for LLM processing.

System requirements:
- PDF upload;
- text extraction;
- document classification;
- tag generation;
- confidence score generation;
- browser result visualization.

---

# Stage 1 — System Design

## Goal

Design and finalize the architecture, data flow, and project structure before implementation.

## Tasks for LLM

### Task 1.1 — Define overall architecture

You must define the architecture of the application with the following layers:

Frontend:
- simple HTML page served by Django;
- CSS styling;
- vanilla JavaScript for upload and result rendering;
- PDF upload UI;
- result visualization.

Backend:
- Django backend;
- REST API;
- file handling;
- PDF processing;
- prompt generation;
- Ollama communication.

LLM Layer:
- local Gemma 4 E4B model;
- Ollama runtime;
- text-based inference only;
- receives extracted text instead of PDF files.

PDF Layer:
- PDF parsing;
- text extraction.

Expected result:
- finalized architecture diagram;
- service boundaries;
- request flow documentation.

---

### Task 1.2 — Define project structure

You must create a modular project structure.

Expected structure:

```text
project/
│
├── backend/
│   ├── api/
│   ├── services/
│   ├── llm/
│   ├── pdf/
│   ├── prompts/
│   └── models/
│
├── media/
│   └── tmp/
│
├── templates/
├── static/
│   ├── css/
│   └── js/
│
└── docs/
```

---

### Task 1.3 — Define API contract

You must define REST API endpoints.

Required endpoints:
- upload PDF;
- return classification result in the upload response for synchronous MVP;
- health check.

Example endpoint:

```http
POST /api/classify/
```

Expected response:

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

---

# Stage 2 — Backend Setup

## Goal

Prepare Django backend infrastructure.

## Tasks for LLM

### Task 2.1 — Initialize Django project

You must:
- create Django project;
- configure Django REST Framework;
- configure CORS;
- configure media handling;
- configure temporary storage for uploaded PDFs.

Status on 2026-05-30: completed.

---

### Task 2.2 — Create backend modules

You must create modules:
- api;
- services;
- pdf;
- llm;
- prompts.

Status on 2026-05-30: completed.

---

### Task 2.3 — Configure environment variables

You must configure:
- Ollama URL;
- temp storage path;
- max upload size;
- debug mode.

Status on 2026-05-30: completed.

---

# Stage 3 — Frontend Setup

## Goal

Prepare a simple browser UI and static asset skeleton.

## Tasks for LLM

### Task 3.1 — Initialize browser UI

You must:
- create HTML template(s);
- configure static CSS/JS;
- connect browser JavaScript to backend API.

Status on 2026-06-05: completed.

---

### Task 3.2 — Create upload interface

You must implement:
- PDF upload form;
- drag-and-drop support;
- upload button;
- loading indicator.

Status on 2026-06-05: completed.

---

### Task 3.3 — Create result interface

You must implement visualization for:
- document class;
- generated tags;
- confidence score;
- errors.

Status on 2026-06-05: completed.

---

# Stage 4 — PDF Processing Layer

## Goal

Extract clean text from uploaded PDF documents.

## Tasks for LLM

### Task 4.1 — Implement PDF upload endpoint

You must:
- accept multipart/form-data;
- validate PDF extension;
- validate file size;
- reject invalid files.

Status on 2026-06-05: completed.

---

### Task 4.2 — Implement temporary storage

You must:
- save uploaded PDFs temporarily;
- generate unique filenames;
- remove old temporary files.

Status on 2026-06-05: completed.

---
### Task 4.2.1 — Convert PDF to Text

Gemma 4 E4B cannot process PDF files directly.

You must implement a preprocessing layer that converts uploaded PDF files into plain text before any LLM interaction occurs.

Requirements:
- extract all readable text;
- preserve logical document structure;
- preserve headings when possible;
- merge page content into a single text stream;
- return cleaned text for prompt generation.

Expected result:
- LLM-ready text representation of every uploaded PDF.

Status on 2026-06-14: completed.

---

### Task 4.3 — Implement PDF parser

You must integrate:
- PyMuPDF or pdfplumber.

Parser requirements:
- extract all textual content;
- preserve readable formatting;
- handle multi-page PDFs.

Status on 2026-06-05: completed.

---

### Task 4.4 — Implement text cleaning

You must:
- remove duplicate spaces;
- normalize line breaks;
- remove empty fragments;
- trim unnecessary symbols.

Status on 2026-06-05: completed.

---

### Task 4.5 — Handle PDF errors

You must handle:
- corrupted PDFs;
- empty PDFs;
- scanned PDFs without text;
- unsupported formats.

Status on 2026-06-05: completed.

---

# Stage 5 — Prompt Engineering

Important constraint:

Gemma 4 E4B never receives raw PDF files.

Prompt generation must always use text extracted by the PDF processing layer.

## Goal

Create reliable prompts for Gemma 4 classification.

## Tasks for LLM

### Task 5.1 — Create prompt template

Prompt must:
- contain extracted text;
- contain allowed document classes;
- require strict JSON output.

Allowed classes:
- resume;
- invoice;
- contract;
- academic_paper;
- technical_documentation;
- assignment;
- report;
- unknown.

Status on 2026-06-05: completed.

---

### Task 5.2 — Enforce JSON-only responses

You must:
- instruct model to return JSON only;
- prohibit explanations;
- prohibit markdown formatting.

Status on 2026-06-05: completed.

---

### Task 5.3 — Implement response validation

You must validate:
- JSON syntax;
- required fields;
- confidence range;
- tag format.

Status on 2026-06-05: completed.

---

# Stage 6 — Ollama Integration

## Goal

Connect Django backend to local Gemma 4 E4B through Ollama.

The model receives only extracted text produced by the PDF processing pipeline.

## Tasks for LLM

### Task 6.1 — Create Ollama service

You must implement:
- send_prompt();
- parse_response();
- error handling.

Status on 2026-06-05: completed.

---

### Task 6.2 — Send requests to Ollama API

You must:
- send POST requests;
- pass generated prompt;
- receive model response.

Status on 2026-06-05: completed.

---

### Task 6.3 — Implement timeout handling

You must:
- handle long requests;
- implement retry logic;
- handle unavailable model states.

Status on 2026-06-05: completed.

---

# Stage 7 — Classification Pipeline

## Goal

Implement complete end-to-end document classification.

## Tasks for LLM

### Task 7.1 — Build full pipeline

Pipeline steps:

1. User uploads PDF;
2. Backend receives file;
3. File saved temporarily;
4. PDF parsed;
5. Raw text extracted;
6. Text cleaned and normalized;
7. Prompt generated from extracted text;
8. Request sent to Ollama (Gemma 4 E4B);
9. Classification returned;
10. JSON validated;
11. API response returned;
12. Frontend displays result.

Status on 2026-06-05: completed.

---

### Task 7.2 — Implement API response

Response format:

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

Status on 2026-06-05: completed.

---

# Stage 8 — Frontend Integration

## Goal

Connect frontend to backend API.

## Tasks for LLM

### Task 8.1 — Implement API communication

You must:
- upload PDFs via API;
- receive classification JSON;
- handle errors.

Status on 2026-06-05: completed.

---

### Task 8.2 — Implement loading states

You must display:
- upload progress;
- processing state;
- inference state.

Status on 2026-06-05: completed.

---

### Task 8.3 — Implement error visualization

You must display:
- invalid PDF errors;
- parsing errors;
- Ollama errors;
- timeout errors.

Status on 2026-06-05: completed.

---

# Stage 9 — Testing

## Goal

Validate system stability.

## Tasks for LLM

### Task 9.1 — Backend testing

You must test:
- upload endpoint;
- PDF parsing;
- prompt generation;
- Ollama communication;
- JSON validation.

Status on 2026-06-05: completed.

---

### Task 9.2 — Frontend testing

You must test:
- upload flow;
- loading states;
- result rendering;
- error rendering.

Status on 2026-06-05: completed.

---

### Task 9.3 — Classification testing

You must test all supported document types:
- resume;
- invoice;
- contract;
- academic_paper;
- technical_documentation;
- assignment;
- report;
- unknown.

Status on 2026-06-05: completed.

---

# Stage 10 — Optimization

## Goal

Improve stability and scalability of the MVP.

## Tasks for LLM

### Task 10.1 — Optimize large PDF handling

You must:
- limit input size;
- implement chunking;
- truncate unnecessary text.

Status on 2026-06-14: completed.

---

## Pre-Stage 10.2 — Remediation Plan

## Goal

Remove known project inconsistencies before implementing prompt-stability and performance work.

## Reason for this block

As of 2026-06-14, the codebase implements a working synchronous `/api/classify/` pipeline, but several project sources are out of sync with the actual implementation state.

Known issues to resolve before Stage 10.2:
- `docs/api-contract.md` still documents a temporary `501 Not Implemented` response for `/api/classify/`;
- `docs/architecture.md` still describes several implemented layers as future work;
- `docs/backend-setup.md` does not yet reflect the current extracted-text optimization settings;
- local git history contains unpushed commits because GitHub authentication is not currently available in the environment;
- current test coverage is strong at unit/service level, but live verification against a running local Ollama instance is still a separate validation step.

### Task R1 — Synchronize implementation docs

You must:
- update `docs/api-contract.md` to match the real synchronous classification API;
- update `docs/architecture.md` to describe the implemented pipeline rather than deferred work;
- update `docs/backend-setup.md` with the current text-optimization and environment settings.

Expected result:
- documentation matches the current codebase and no longer describes removed temporary behavior.

Status on 2026-06-14: completed.

---

### Task R2 — Reconcile repository publication state

You must:
- verify which local commits are ahead of `origin/main`;
- push pending commits after GitHub authentication is available;
- record the updated publication state in this work plan.

Expected result:
- local repository state and GitHub repository state are synchronized again.

Repository publication check on 2026-06-14:
- local branch `main` is ahead of `origin/main` by 3 commits;
- pending local commits verified:
  - `45b4f2b` — `Implement PDF-to-text preprocessing`
  - `be55647` — `Optimize large PDF handling`
  - `3a8fee6` — `Synchronize implementation docs`
- push attempts from the current environment still fail with GitHub HTTPS authentication error:
  - `fatal: could not read Username for 'https://github.com': No such device or address`

Status on 2026-06-14: blocked by missing GitHub authentication in the current environment.

---

### Task R3 — Strengthen pre-optimization verification baseline

You must:
- define and run a live verification path for `/api/classify/` against a local Ollama runtime when available;
- document the distinction between mocked/unit coverage and live runtime verification;
- keep this verification baseline in place before Stage 10.2 and Stage 10.3 changes.

Expected result:
- prompt-stability and performance work starts from a clearly verified baseline.

Status: planned.

---

### Task 10.2 — Improve prompt stability

You must:
- improve formatting;
- reduce hallucinations;
- improve JSON consistency.

---

### Task 10.3 — Improve performance

You must:
- reduce response latency;
- optimize parsing;
- optimize API communication.

---

# Future Improvements

## OCR Support
Support scanned PDFs.

## Multi-label Classification
Allow multiple classes.

## Document Summarization
Generate summaries.

## Vector Database
Semantic document search.

## RAG Pipeline
Context-aware document analysis.

## Fine-Tuning
Custom model training.

## Authentication
User accounts and permissions.

## Upload History
Store previous uploaded files and results.
