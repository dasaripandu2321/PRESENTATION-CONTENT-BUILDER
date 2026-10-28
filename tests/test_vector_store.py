import pytest
from app.services.vector_store import VectorStoreService
from app.models.schemas import DocumentChunk

def test_vector_store_operations(tmp_path):
    # Isolated test vector store
    store = VectorStoreService(persist_directory=str(tmp_path / "test_chroma"))

    chunks = [
        DocumentChunk(
            chunk_id="doc1_c0",
            doc_id="doc1",
            source_filename="whitepaper.pdf",
            file_type="pdf",
            page_number=1,
            chunk_index=0,
            content="Agentic RAG architecture enables autonomous multi-hop vector retrieval.",
            char_count=71
        ),
        DocumentChunk(
            chunk_id="doc1_c1",
            doc_id="doc1",
            source_filename="whitepaper.pdf",
            file_type="pdf",
            page_number=2,
            chunk_index=1,
            content="Cloud financial earnings reached 4.82 billion dollars in Q3 fiscal year.",
            char_count=73
        )
    ]

    doc_info = store.add_document_chunks(
        doc_id="doc1",
        filename="whitepaper.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        chunks=chunks
    )

    assert doc_info.chunk_count == 2
    assert doc_info.doc_id == "doc1"

    # Search query 1
    results = store.similarity_search("RAG architecture and retrieval", top_k=2)
    assert len(results) > 0
    assert results[0].doc_id == "doc1"
    assert "RAG" in results[0].content or "Agentic" in results[0].content

    # Stats
    stats = store.get_stats()
    assert stats["total_documents"] == 1
    assert stats["total_chunks"] == 2

    # Delete
    deleted = store.delete_document("doc1")
    assert deleted is True
    assert len(store.list_documents()) == 0

