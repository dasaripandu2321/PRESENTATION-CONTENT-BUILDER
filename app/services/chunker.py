import uuid
from typing import List, Dict, Any, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models.schemas import DocumentChunk
from app.config import settings


class DocumentChunker:
    """Recursive character-based document chunker with context and metadata preservation."""

    def __init__(
        self,
        chunk_size: int = settings.DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = settings.DEFAULT_CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n### ", "\n\n## ", "\n\n# ", "\n\n", "\n", ". ", "; ", ", ", " "],
            keep_separator=True,
        )

    def chunk_document(
        self,
        doc_id: str,
        parsed_pages: List[Dict[str, Any]],
        source_filename: str,
        file_type: str
    ) -> List[DocumentChunk]:
        """
        Splits parsed page contents into semantic chunks while maintaining page and source context.
        """
        chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        for page in parsed_pages:
            page_text = page.get("text", "").strip()
            page_number = page.get("page_number", 1)

            if not page_text:
                continue

            raw_splits = self.splitter.split_text(page_text)

            for split_text in raw_splits:
                clean_split = split_text.strip()
                if not clean_split:
                    continue

                chunk_id = f"{doc_id}_c{global_chunk_idx}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        source_filename=source_filename,
                        file_type=file_type,
                        page_number=page_number,
                        chunk_index=global_chunk_idx,
                        content=clean_split,
                        char_count=len(clean_split),
                    )
                )
                global_chunk_idx += 1

        return chunks

