"""
Embedding service using Sentence Transformers.
Loads model once and exposes clean encode interface.
"""

from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np
import threading
import logging

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """
    Singleton wrapper around SentenceTransformer.
    Ensures model loads only once.
    Thread-safe for production usage.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        """
        Load embedding model once.
        """
        logger.info("[Embedding] Loading model...")

        # You can switch model here easily later
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        # simple in-memory cache
        self.cache = {}

        logger.info("[Embedding] Model loaded successfully")

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for list of texts.
        Uses caching for repeated inputs.
        """

        results = []

        for text in texts:
            if text in self.cache:
                results.append(self.cache[text])
                continue

            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )

            self.cache[text] = embedding
            results.append(embedding)

        return np.array(results)


# Global accessor
def get_embedding_model() -> EmbeddingModel:
    return EmbeddingModel()
