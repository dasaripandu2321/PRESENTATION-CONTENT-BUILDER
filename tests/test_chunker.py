import pytest
from app.services.chunker import DocumentChunker

def test_document_chunker():
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    
    parsed_pages = [
        {
            "page_number": 1,
            "text": "This is a detailed paragraph explaining Retrieval Augmented Generation and presentation building for modern AI applications. It has enough length to trigger chunking."
        }
    ]

    chunks = chunker.chunk_document(
        doc_id="doc_123",
        parsed_pages=parsed_pages,
        source_filename="test.txt",
        file_type="txt"
    )

    assert len(chunks) >= 2
    assert chunks[0].doc_id == "doc_123"
    assert chunks[0].source_filename == "test.txt"
    assert chunks[0].page_number == 1
    assert chunks[0].chunk_index == 0
    assert len(chunks[0].content) > 0

