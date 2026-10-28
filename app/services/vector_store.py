import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.models.schemas import DocumentChunk, DocumentInfo, SearchResult
from app.services.embeddings import embedding_service


class VectorStoreService:
    """Production vector store abstraction using ChromaDB persistent client."""

    COLLECTION_NAME = "presentation_knowledge"
    REGISTRY_FILE = "documents_registry.json"

    def __init__(self, persist_directory: str = settings.CHROMA_DIRECTORY):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.persist_directory / self.REGISTRY_FILE

        # Initialize ChromaDB persistent client with telemetry disabled
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"description": "Presentation Content Builder Knowledge Chunks"}
        )
        self._load_registry()

    def _load_registry(self) -> Dict[str, Dict[str, Any]]:
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    self.registry = json.load(f)
            except Exception:
                self.registry = {}
        else:
            self.registry = {}
        return self.registry

    def _save_registry(self):
        try:
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(self.registry, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save registry: {e}")

    def add_document_chunks(
        self,
        doc_id: str,
        filename: str,
        file_type: str,
        file_size_bytes: int,
        chunks: List[DocumentChunk]
    ) -> DocumentInfo:
        """Embeds and indexes document chunks into ChromaDB."""
        if not chunks:
            info = DocumentInfo(
                doc_id=doc_id,
                filename=filename,
                file_type=file_type,
                file_size_bytes=file_size_bytes,
                chunk_count=0,
                total_characters=0,
                upload_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            self.registry[doc_id] = info.model_dump()
            self._save_registry()
            return info

        texts = [chunk.content for chunk in chunks]
        embeddings = embedding_service.embed_texts(texts)
        ids = [chunk.chunk_id for chunk in chunks]
        metadatas = [
            {
                "doc_id": chunk.doc_id,
                "source_filename": chunk.source_filename,
                "file_type": chunk.file_type,
                "page_number": int(chunk.page_number or 1),
                "chunk_index": int(chunk.chunk_index),
                "char_count": int(chunk.char_count)
            }
            for chunk in chunks
        ]

        # ChromaDB batch upsert
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        total_chars = sum(len(c.content) for c in chunks)
        doc_info = DocumentInfo(
            doc_id=doc_id,
            filename=filename,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            chunk_count=len(chunks),
            total_characters=total_chars,
            upload_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        self.registry[doc_id] = doc_info.model_dump()
        self._save_registry()
        return doc_info

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        doc_id: Optional[str] = None
    ) -> List[SearchResult]:
        """Performs semantic similarity search against indexed knowledge chunks."""
        count = self.collection.count()
        if count == 0:
            return []

        effective_k = min(top_k, count)
        query_vector = embedding_service.embed_query(query)

        where_filter = {"doc_id": doc_id} if doc_id else None

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=effective_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        search_results: List[SearchResult] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return []

        ids = results["ids"][0]
        docs = results["documents"][0] if "documents" in results else []
        metas = results["metadatas"][0] if "metadatas" in results else []
        distances = results["distances"][0] if "distances" in results else []

        for idx in range(len(ids)):
            meta = metas[idx] or {}
            dist = distances[idx] if idx < len(distances) else 1.0
            
            # Chroma returns L2 squared distance by default (or cosine distance depending on space)
            # Normalize to 0.0 - 1.0 similarity score
            similarity = max(0.0, min(1.0, 1.0 - (dist / 2.0))) if dist <= 2.0 else max(0.0, 1.0 / (1.0 + dist))

            search_results.append(
                SearchResult(
                    chunk_id=ids[idx],
                    doc_id=meta.get("doc_id", "unknown"),
                    source_filename=meta.get("source_filename", "unknown"),
                    page_number=meta.get("page_number", 1),
                    chunk_index=meta.get("chunk_index", 0),
                    content=docs[idx] if idx < len(docs) else "",
                    similarity_score=round(similarity, 4)
                )
            )

        return search_results

    def list_documents(self) -> List[DocumentInfo]:
        """Lists all registered documents."""
        self._load_registry()
        return [DocumentInfo(**data) for data in self.registry.values()]

    def delete_document(self, doc_id: str) -> bool:
        """Deletes a document and its chunks from ChromaDB and registry."""
        try:
            self.collection.delete(where={"doc_id": doc_id})
            if doc_id in self.registry:
                del self.registry[doc_id]
                self._save_registry()
            return True
        except Exception as e:
            print(f"Error deleting document {doc_id}: {e}")
            return False

    def clear_all(self) -> bool:
        """Wipes the entire vector store collection and registry."""
        try:
            self.client.delete_collection(name=self.COLLECTION_NAME)
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "Presentation Content Builder Knowledge Chunks"}
            )
            self.registry = {}
            self._save_registry()
            return True
        except Exception as e:
            print(f"Error clearing vector store: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics on the vector store."""
        self._load_registry()
        total_chunks = self.collection.count()
        total_docs = len(self.registry)
        total_chars = sum(d.get("total_characters", 0) for d in self.registry.values())
        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "total_characters": total_chars,
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "persist_directory": str(self.persist_directory)
        }


# Global singleton instance
vector_store_service = VectorStoreService()

