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

## Project Overview

Develop a web application for automatic PDF document classification using a local LLM model (Gemma 4 via Ollama).

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
- local Gemma 4 model;
- Ollama runtime.

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

---

### Task 3.2 — Create upload interface

You must implement:
- PDF upload form;
- drag-and-drop support;
- upload button;
- loading indicator.

---

### Task 3.3 — Create result interface

You must implement visualization for:
- document class;
- generated tags;
- confidence score;
- errors.

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

---

### Task 4.2 — Implement temporary storage

You must:
- save uploaded PDFs temporarily;
- generate unique filenames;
- remove old temporary files.

---

### Task 4.3 — Implement PDF parser

You must integrate:
- PyMuPDF or pdfplumber.

Parser requirements:
- extract all textual content;
- preserve readable formatting;
- handle multi-page PDFs.

---

### Task 4.4 — Implement text cleaning

You must:
- remove duplicate spaces;
- normalize line breaks;
- remove empty fragments;
- trim unnecessary symbols.

---

### Task 4.5 — Handle PDF errors

You must handle:
- corrupted PDFs;
- empty PDFs;
- scanned PDFs without text;
- unsupported formats.

---

# Stage 5 — Prompt Engineering

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

---

### Task 5.2 — Enforce JSON-only responses

You must:
- instruct model to return JSON only;
- prohibit explanations;
- prohibit markdown formatting.

---

### Task 5.3 — Implement response validation

You must validate:
- JSON syntax;
- required fields;
- confidence range;
- tag format.

---

# Stage 6 — Ollama Integration

## Goal

Connect Django backend to local Gemma 4 through Ollama.

## Tasks for LLM

### Task 6.1 — Create Ollama service

You must implement:
- send_prompt();
- parse_response();
- error handling.

---

### Task 6.2 — Send requests to Ollama API

You must:
- send POST requests;
- pass generated prompt;
- receive model response.

---

### Task 6.3 — Implement timeout handling

You must:
- handle long requests;
- implement retry logic;
- handle unavailable model states.

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
4. PDF text extracted;
5. Prompt generated;
6. Request sent to Ollama;
7. Gemma returns classification;
8. Backend validates JSON;
9. Backend returns API response;
10. Frontend displays result.

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

---

### Task 8.2 — Implement loading states

You must display:
- upload progress;
- processing state;
- inference state.

---

### Task 8.3 — Implement error visualization

You must display:
- invalid PDF errors;
- parsing errors;
- Ollama errors;
- timeout errors.

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

---

### Task 9.2 — Frontend testing

You must test:
- upload flow;
- loading states;
- result rendering;
- error rendering.

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
