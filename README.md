# Presentation Content Builder AI (RAG + LLM Engine)

A production-ready, full-stack Retrieval-Augmented Generation (RAG) Presentation Content Builder. The system ingests multi-format documents, parses and chunks context, performs semantic vector retrieval, and leverages LLM orchestration to synthesize structured, presentation-ready slide decks and downloadable 16:9 widescreen PowerPoint (`.pptx`) presentations.

---

## Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │ Multi-Format Ingestion Pipeline        │
                      │ (PDF, DOCX, Markdown, Text, CSV, JSON) │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │ Recursive Character Text Splitter      │
                      │ (Metadata, Overlap & Context Tracking) │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │ Dual-Mode Vector Storage               │
                      │ - ChromaDB (Local / Persistent VPS)    │
                      │ - Serverless In-Memory (/tmp Vercel)   │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │ Multi-Aspect Semantic RAG Retrieval    │
                      │ (Context, Problem, Pillars, Metrics)   │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │ LLM Orchestration & Synthesis Engine   │
                      │ (OpenAI / Gemini / Local RAG Engine)   │
                      │ Enforces Strict SlideDeck JSON Schema  │
                      └──────────────────┬─────────────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
┌──────────────────────────────────────┐     ┌───────────────────────────────────┐
│ Interactive Slide Deck Studio (Web)  │     │ Programmatic PPTX Export Engine   │
│ - 16:9 Aspect Ratio Slide Canvas     │     │ - Modern Indigo / Executive Navy  │
│ - In-Place Live Editing              │     │ - Card Layouts & Dynamic Shapes   │
│ - Speaker Delivery Notes Pane        │     │ - Embedded Presenter Notes        │
│ - Factual Grounding Citations        │     │ - Downloadable .pptx Presentation │
└──────────────────────────────────────┘     └───────────────────────────────────┘
```

---

## Deploying to Vercel (One-Click / Serverless Ready)

This repository includes first-class support for **Vercel Serverless Functions**:
- **Entrypoint:** `api/index.py`
- **Routing Configuration:** `vercel.json`
- **Optimized Bundle:** Lightweight `requirements.txt` under 50MB (avoids PyTorch bundle size limit of 250MB).
- **Ephemeral Storage:** Automatically uses `/tmp` for temporary chunks and vector indexing on Vercel without throwing read-only filesystem errors.

### Vercel Environment Variables (Optional):
In your Vercel Project Dashboard -> **Settings** -> **Environment Variables**:
- `OPENAI_API_KEY`: *(Optional)* Your OpenAI API key for GPT-4o synthesis and embeddings.
- `GEMINI_API_KEY`: *(Optional)* Your Google Gemini API key.

*(Note: Even with NO API keys configured, the application functions 100% out of the box using its built-in heuristic RAG synthesis engine!)*

---

## Local Development & Installation

### 1. Installation
Install lightweight dependencies:
```bash
pip install -r requirements.txt
```
*(Optional) If you want local sentence-transformers / PyTorch on your workstation:*
```bash
pip install -r requirements-local.txt
```

### 2. Launch Local Server
```bash
python run.py
```
Open **`http://127.0.0.1:8000`** in your browser.
API Swagger Docs: **`http://127.0.0.1:8000/docs`**

---

## Strict SlideDeck JSON Contract

The system guarantees generation strictly conforming to:
```json
{
  "deck_title": "string",
  "target_audience": "string",
  "slides": [
    {
      "slide_number": 1,
      "title": "string",
      "core_takeaway": "string",
      "bullet_points": ["string"],
      "visual_layout_suggestion": "string",
      "speaker_notes": "string",
      "retrieved_sources": ["string"]
    }
  ]
}
```

---

## Running Automated Tests

```bash
pytest -v
```
All 11 unit & integration tests verify:
- Multi-format ingestion (PDF, DOCX, TXT, CSV, JSON)
- Recursive character text chunking
- ChromaDB and Serverless In-Memory vector stores
- SlideDeck JSON schema validation
- 16:9 widescreen PowerPoint `.pptx` generation
- FastAPI REST endpoints
