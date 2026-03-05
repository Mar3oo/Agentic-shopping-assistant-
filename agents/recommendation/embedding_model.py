"""
Embedding service using Sentence Transformers.
Loads model once and exposes clean encode interface.
"""

from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np
import threading


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
        Load embedding model.
        Using all-MiniLM-L6-v2 (384-dim vectors).
        """
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for list of texts.
        Returns numpy array (n, 384).
        """
        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,  # important for cosine similarity
        )


# Global accessor
def get_embedding_model() -> EmbeddingModel:
    return EmbeddingModel()
