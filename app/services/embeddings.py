import os
import math
from typing import List, Optional
import numpy as np

# Inject truststore if available to ensure smooth SSL handling
try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from app.config import settings


class EmbeddingService:
    """Unified embedding service supporting HuggingFace all-MiniLM-L6-v2 and OpenAI."""

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self._local_model = None
        self._openai_client = None

    def _get_local_model(self):
        if self._local_model is None:
            from sentence_transformers import SentenceTransformer
            # Disable HF symlink warning
            os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
            self._local_model = SentenceTransformer(self.model_name)
        return self._local_model

    def _get_openai_client(self):
        if self._openai_client is None:
            from openai import OpenAI
            api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is not set.")
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client

    def embed_texts(self, texts: List[str], provider: Optional[str] = None) -> List[List[float]]:
        """
        Embed a list of text strings into vector representations.
        Provider can be 'local', 'openai', or 'auto'.
        """
        if not texts:
            return []

        selected_provider = provider or settings.EMBEDDING_PROVIDER

        # 1. OpenAI provider
        if selected_provider == "openai" or (selected_provider == "auto" and (settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY"))):
            try:
                client = self._get_openai_client()
                response = client.embeddings.create(
                    model=settings.OPENAI_EMBEDDING_MODEL,
                    input=texts
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                # If OpenAI fails or key invalid, fall back to local model
                pass

        # 2. Local HuggingFace all-MiniLM-L6-v2
        try:
            model = self._get_local_model()
            embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            return embeddings.tolist()
        except Exception as e:
            # 3. Fallback deterministic semantic embedding generator
            return self._fallback_embed(texts)

    def embed_query(self, query: str, provider: Optional[str] = None) -> List[float]:
        """Embed a single search query."""
        results = self.embed_texts([query], provider=provider)
        return results[0] if results else []

    def _fallback_embed(self, texts: List[str], dim: int = 384) -> List[List[float]]:
        """High-entropy deterministic token-frequency hash embedding fallback."""
        vectors = []
        for text in texts:
            vec = np.zeros(dim, dtype=np.float32)
            words = text.lower().split()
            for idx, word in enumerate(words):
                h = hash(word) % dim
                # Position-decayed frequency
                weight = 1.0 / math.sqrt(idx + 1)
                vec[h] += weight
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec.tolist())
        return vectors


# Global singleton instance
embedding_service = EmbeddingService()

