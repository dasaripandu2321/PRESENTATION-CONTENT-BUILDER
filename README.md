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
                      │ ChromaDB Persistent Vector Store       │
                      │ (all-MiniLM-L6-v2 / text-embedding-3)  │
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

## Key Features

1. **Multi-Format Ingestion:**
   - PDF parsing via `pdfplumber` (layout & tables) with fallback to `PyPDF2`.
   - Word documents (`.docx`) with headings and table parsing.
   - Markdown (`.md`), Plain Text (`.txt`), CSV, and JSON.
   - Recursive character text chunking with configurable chunk sizes, overlaps, and source metadata tracking.

2. **Persistent Vector Store & Semantic Retrieval:**
   - Local persistent storage with `ChromaDB` (`./data/chroma_db`).
   - Embedding models: Local HuggingFace `all-MiniLM-L6-v2` (384-d dense vectors) or OpenAI `text-embedding-3-small`.
   - Multi-query aspect expansion: Decomposes prompts across overview, pillars, metrics, roadmap, and recommendations.

3. **Strict SlideDeck JSON Contract:**
   - Guaranteed output validation via Pydantic matching the exact user specification:
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

4. **Multi-Provider LLM Orchestration:**
   - **OpenAI:** GPT-4o / GPT-4o-mini structured outputs.
   - **Google Gemini:** Gemini 2.0 Flash JSON mode.
   - **Local Heuristic RAG Synthesis Engine:** 100% functional out of the box with zero external API keys required!

5. **Programmatic 16:9 PowerPoint Export (`python-pptx`):**
   - Widescreen 16:9 aspect ratio (`13.333" x 7.5"`).
   - Designer visual themes:
     - **Modern Indigo** (Dark Tech Slate & Electric Indigo)
     - **Executive Navy & Gold** (Boardroom Navy & Amber)
     - **Emerald Horizon** (Clean Forest & Vivid Mint)
     - **Nordic Light** (Minimalist High-Contrast Light)
   - Intelligent visual layout mapping: `title_hero`, `split_2_column`, `3_pillar_cards`, `kpi_highlight`, `timeline_flow`, `bullet_list`.
   - Speaker notes embedded into PowerPoint's native presenter notes pane.
   - Subtle citation footers on every slide attributing source documents and pages.

6. **Interactive Presentation Studio (Web UI):**
   - Modern Tailwind CSS & Lucide icons dashboard.
   - Real-time slide stage with live text editing.
   - Knowledge Base file manager (drag-and-drop, chunk statistics, delete).
   - RAG Semantic Explorer to test similarity queries against indexed chunks.
   - One-click `.PPTX` and `.JSON` downloads.

---

## Getting Started

### 1. Installation
Install project dependencies:
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your optional LLM API keys:
```ini
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
```
*(Note: If no API keys are provided, the system seamlessly uses the built-in local RAG synthesis engine.)*

### 3. Launching the Application
Run the startup script:
```bash
python run.py
```
Or start via Uvicorn:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser at: **`http://127.0.0.1:8000`**

Interactive Swagger API Documentation: **`http://127.0.0.1:8000/docs`**

---

## API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the full-stack Web Presentation Studio |
| `GET` | `/api/health` | Health status and ChromaDB vector statistics |
| `GET` | `/api/documents` | Lists all ingested documents and chunk counts |
| `POST` | `/api/documents/upload` | Uploads and indexes multi-format documents |
| `DELETE` | `/api/documents/{doc_id}` | Removes a document and its chunks from vector store |
| `POST` | `/api/documents/clear` | Wipes the entire vector store and registry |
| `POST` | `/api/search` | Executes semantic vector similarity search |
| `POST` | `/api/generate-deck` | Synthesizes a slide deck conforming to SlideDeck JSON schema |
| `POST` | `/api/export-pptx` | Programmatically exports SlideDeck JSON into a downloadable `.pptx` file |

---

## Running the Automated Test Suite

Run the full pytest suite:
```bash
pytest -v
```
All 11 unit and integration tests verify:
- Multi-format document parsing (PDF, DOCX, TXT, CSV, JSON)
- Recursive character chunking & metadata retention
- ChromaDB indexing, semantic search, and document deletion
- SlideDeck generation and strict JSON schema contract validation
- 16:9 widescreen PowerPoint `.pptx` generation and speaker notes embedding
- FastAPI REST endpoints (`/api/health`, `/api/generate-deck`, `/api/export-pptx`, etc.)

