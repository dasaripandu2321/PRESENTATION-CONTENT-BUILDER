import os
import uuid
import re
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models.schemas import (
    SlideDeck,
    DocumentInfo,
    IngestResponse,
    SearchRequest,
    SearchResponse,
    GenerateDeckRequest,
    ExportPPTXRequest,
)
from app.services import (
    DocumentParser,
    DocumentChunker,
    vector_store_service,
    slide_deck_generator,
    pptx_builder,
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready RAG + LLM Presentation Content Builder API"
)

# CORS middleware for open frontends/integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static web UI files
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_root():
    """Serves the main presentation builder web interface."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Presentation Content Builder AI is Running</h1><p>API docs at <a href='/docs'>/docs</a></p>")


@app.get("/api/health")
async def health_check():
    """Health check and vector store statistics."""
    stats = vector_store_service.get_stats()
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "vector_store": stats
    }


@app.get("/api/documents", response_model=List[DocumentInfo])
async def list_documents():
    """Returns all ingested documents and their chunk statistics."""
    return vector_store_service.list_documents()


@app.post("/api/documents/upload", response_model=IngestResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    chunk_size: Optional[int] = Form(settings.DEFAULT_CHUNK_SIZE),
    chunk_overlap: Optional[int] = Form(settings.DEFAULT_CHUNK_OVERLAP)
):
    """
    Ingests and parses multi-format documents (PDF, DOCX, TXT, MD, CSV, JSON),
    chunks them with metadata, and indexes them in ChromaDB.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided for upload.")

    chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    ingested_docs: List[DocumentInfo] = []
    total_new_chunks = 0

    upload_folder = Path(settings.UPLOAD_DIRECTORY)
    upload_folder.mkdir(parents=True, exist_ok=True)

    for file in files:
        filename = file.filename or "uploaded_document"
        doc_id = str(uuid.uuid4())[:12]
        file_suffix = Path(filename).suffix.lower()
        saved_path = upload_folder / f"{doc_id}_{filename}"

        # Write uploaded file to disk
        content_bytes = await file.read()
        with open(saved_path, "wb") as f:
            f.write(content_bytes)

        file_size = len(content_bytes)

        try:
            # Parse document
            parsed_pages = DocumentParser.parse_file(str(saved_path), original_filename=filename)
            
            # Chunk document
            chunks = chunker.chunk_document(
                doc_id=doc_id,
                parsed_pages=parsed_pages,
                source_filename=filename,
                file_type=file_suffix.lstrip(".") or "text"
            )

            # Index in vector store
            doc_info = vector_store_service.add_document_chunks(
                doc_id=doc_id,
                filename=filename,
                file_type=file_suffix.lstrip(".") or "text",
                file_size_bytes=file_size,
                chunks=chunks
            )

            ingested_docs.append(doc_info)
            total_new_chunks += len(chunks)

        except Exception as e:
            # Continue processing remaining files if one fails
            print(f"Error processing file '{filename}': {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process '{filename}': {str(e)}"
            )

    return IngestResponse(
        status="success",
        documents=ingested_docs,
        total_chunks_created=total_new_chunks,
        message=f"Successfully ingested {len(ingested_docs)} document(s) with {total_new_chunks} chunk(s)."
    )


@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Deletes a document and its associated chunks from the vector database."""
    success = vector_store_service.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document with ID '{doc_id}' not found.")
    return {"status": "success", "message": f"Document '{doc_id}' deleted."}


@app.post("/api/documents/clear")
async def clear_all_documents():
    """Wipes all knowledge base documents and vector embeddings."""
    success = vector_store_service.clear_all()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear vector store.")
    return {"status": "success", "message": "All documents and vectors cleared."}


@app.post("/api/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """Executes semantic similarity search over the knowledge base."""
    results = vector_store_service.similarity_search(
        query=request.query,
        top_k=request.top_k,
        doc_id=request.doc_id
    )
    return SearchResponse(query=request.query, results=results)


@app.post("/api/generate-deck", response_model=SlideDeck)
async def generate_slide_deck(request: GenerateDeckRequest):
    """
    RAG Slide Generation Engine:
    Performs multi-query semantic retrieval over ingested documents,
    orchestrates LLM synthesis, and strictly returns the SlideDeck JSON contract.
    """
    try:
        deck = slide_deck_generator.generate_deck(request)
        return deck
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Slide deck generation failed: {str(e)}"
        )


@app.post("/api/export-pptx")
async def export_presentation_pptx(request: ExportPPTXRequest):
    """
    Renders the SlideDeck JSON contract into a beautiful, downloadable PowerPoint (.pptx) file.
    """
    try:
        theme = request.theme or "modern_indigo"
        pptx_stream = pptx_builder.build_presentation(request.deck, theme_name=theme)

        safe_title = re.sub(r'[^a-zA-Z0-9_\- ]', '', request.deck.deck_title).strip() or "Presentation"
        safe_title = safe_title.replace(" ", "_")[:40]
        filename = f"{safe_title}.pptx"

        return StreamingResponse(
            pptx_stream,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export PowerPoint presentation: {str(e)}"
        )

