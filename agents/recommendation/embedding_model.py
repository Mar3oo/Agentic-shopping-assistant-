"""
Embedding service using multilingual E5 Sentence Transformers.
Supports Arabic + English semantic retrieval.
"""

from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np
import threading


class EmbeddingModel:
    """
    Singleton wrapper around SentenceTransformer.
    Thread-safe model loader.
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
        Load multilingual embedding model.
        """
        self.model = SentenceTransformer("intfloat/multilingual-e5-base")

    def encode_documents(self, texts: List[str]) -> np.ndarray:
        """
        Encode product documents/passages.
        """

        formatted = [f"passage: {text}" for text in texts]

        return self.model.encode(
            formatted,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    def encode_queries(self, texts: List[str]) -> np.ndarray:
        """
        Encode user queries.
        """

        formatted = [f"query: {text}" for text in texts]

        return self.model.encode(
            formatted,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )


def get_embedding_model() -> EmbeddingModel:
    return EmbeddingModel()
