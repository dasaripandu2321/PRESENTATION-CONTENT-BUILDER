import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from app.config import settings
from app.models.schemas import DocumentChunk, DocumentInfo, SearchResult
from app.services.embeddings import embedding_service


class VectorStoreService:
    """Production vector store supporting ChromaDB with seamless In-Memory/Serverless fallback."""

    COLLECTION_NAME = "presentation_knowledge"
    REGISTRY_FILE = "documents_registry.json"
    STORE_FILE = "vector_store_chunks.json"

    def __init__(self, persist_directory: str = settings.CHROMA_DIRECTORY):
        self.persist_directory = Path(persist_directory)
        try:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        self.registry_path = self.persist_directory / self.REGISTRY_FILE
        self.store_path = self.persist_directory / self.STORE_FILE
        self.chroma_client = None
        self.collection = None
        self.in_memory_chunks: List[Dict[str, Any]] = []

        # Attempt to initialize ChromaDB if available
        self._init_chroma()
        self._load_registry()

    def _init_chroma(self):
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self.chroma_client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"description": "Presentation Content Builder Knowledge Chunks"}
            )
            print("VectorStore: ChromaDB initialized successfully.")
        except Exception as e:
            print(f"VectorStore: ChromaDB unavailable ({e}). Using Serverless / In-Memory vector store.")
            self.chroma_client = None
            self.collection = None
            self._load_memory_chunks()

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

    def _load_memory_chunks(self):
        if self.store_path.exists():
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    self.in_memory_chunks = json.load(f)
            except Exception:
                self.in_memory_chunks = []
        else:
            self.in_memory_chunks = []

    def _save_memory_chunks(self):
        try:
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(self.in_memory_chunks, f)
        except Exception as e:
            print(f"Warning: Failed to save chunks: {e}")

    def add_document_chunks(
        self,
        doc_id: str,
        filename: str,
        file_type: str,
        file_size_bytes: int,
        chunks: List[DocumentChunk]
    ) -> DocumentInfo:
        """Embeds and indexes document chunks into ChromaDB or In-Memory store."""
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

        if not chunks:
            self.registry[doc_id] = doc_info.model_dump()
            self._save_registry()
            return doc_info

        texts = [chunk.content for chunk in chunks]
        embeddings = embedding_service.embed_texts(texts)

        if self.collection is not None:
            # ChromaDB flow
            try:
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
                self.collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas
                )
            except Exception as e:
                print(f"Chroma upsert failed ({e}), switching to in-memory fallback.")
                self.collection = None

        if self.collection is None:
            # Serverless / In-Memory flow
            for idx, chunk in enumerate(chunks):
                self.in_memory_chunks.append({
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "source_filename": chunk.source_filename,
                    "file_type": chunk.file_type,
                    "page_number": int(chunk.page_number or 1),
                    "chunk_index": int(chunk.chunk_index),
                    "content": chunk.content,
                    "embedding": embeddings[idx] if idx < len(embeddings) else []
                })
            self._save_memory_chunks()

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
        query_vector = embedding_service.embed_query(query)
        if not query_vector:
            return []

        # 1. ChromaDB Search
        if self.collection is not None:
            try:
                count = self.collection.count()
                if count == 0:
                    return []

                effective_k = min(top_k, count)
                where_filter = {"doc_id": doc_id} if doc_id else None

                results = self.collection.query(
                    query_embeddings=[query_vector],
                    n_results=effective_k,
                    where=where_filter,
                    include=["documents", "metadatas", "distances"]
                )

                if results and results.get("ids") and results["ids"][0]:
                    ids = results["ids"][0]
                    docs = results["documents"][0] if "documents" in results else []
                    metas = results["metadatas"][0] if "metadatas" in results else []
                    distances = results["distances"][0] if "distances" in results else []

                    search_results = []
                    for idx in range(len(ids)):
                        meta = metas[idx] or {}
                        dist = distances[idx] if idx < len(distances) else 1.0
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
            except Exception as e:
                print(f"Chroma query failed ({e}), falling back to memory search.")

        # 2. Serverless In-Memory Cosine Similarity Search
        candidates = [c for c in self.in_memory_chunks if (not doc_id or c["doc_id"] == doc_id)]
        if not candidates:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            q_norm = 1.0

        scored = []
        for c in candidates:
            c_vec = np.array(c.get("embedding", []), dtype=np.float32)
            c_norm = np.linalg.norm(c_vec)
            if c_norm > 0:
                cos_sim = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
            else:
                cos_sim = 0.0
            similarity = max(0.0, min(1.0, (cos_sim + 1.0) / 2.0))
            scored.append((similarity, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_candidates = scored[:top_k]

        return [
            SearchResult(
                chunk_id=c["chunk_id"],
                doc_id=c["doc_id"],
                source_filename=c["source_filename"],
                page_number=c["page_number"],
                chunk_index=c["chunk_index"],
                content=c["content"],
                similarity_score=round(sim, 4)
            )
            for sim, c in top_candidates
        ]

    def list_documents(self) -> List[DocumentInfo]:
        """Lists all registered documents."""
        self._load_registry()
        return [DocumentInfo(**data) for data in self.registry.values()]

    def delete_document(self, doc_id: str) -> bool:
        """Deletes a document and its chunks."""
        deleted = False
        if self.collection is not None:
            try:
                self.collection.delete(where={"doc_id": doc_id})
                deleted = True
            except Exception:
                pass

        if self.in_memory_chunks:
            self.in_memory_chunks = [c for c in self.in_memory_chunks if c.get("doc_id") != doc_id]
            self._save_memory_chunks()
            deleted = True

        if doc_id in self.registry:
            del self.registry[doc_id]
            self._save_registry()
            deleted = True

        return deleted

    def clear_all(self) -> bool:
        """Wipes the entire vector store collection and registry."""
        if self.collection is not None:
            try:
                self.chroma_client.delete_collection(name=self.COLLECTION_NAME)
                self.collection = self.chroma_client.get_or_create_collection(
                    name=self.COLLECTION_NAME,
                    metadata={"description": "Presentation Content Builder Knowledge Chunks"}
                )
            except Exception:
                pass

        self.in_memory_chunks = []
        self._save_memory_chunks()
        self.registry = {}
        self._save_registry()
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics on the vector store."""
        self._load_registry()
        total_chunks = self.collection.count() if self.collection is not None else len(self.in_memory_chunks)
        total_docs = len(self.registry)
        total_chars = sum(d.get("total_characters", 0) for d in self.registry.values())
        backend_name = "ChromaDB Persistent Client" if self.collection is not None else "Serverless In-Memory Vector Store"
        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "total_characters": total_chars,
            "backend": backend_name,
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "persist_directory": str(self.persist_directory)
        }


# Global singleton instance
vector_store_service = VectorStoreService()
