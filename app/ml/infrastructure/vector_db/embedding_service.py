"""Embedding service for generating vector embeddings."""

import logging
from typing import List

from sentence_transformers import SentenceTransformer

from app.config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using sentence transformers."""

    _model: SentenceTransformer = None
    _model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """Get or initialize the embedding model."""
        if cls._model is None:
            logger.info(f"Loading embedding model: {cls._model_name}")
            cls._model = SentenceTransformer(cls._model_name)
            logger.info("Embedding model loaded successfully")
        return cls._model

    @classmethod
    def generate_embedding(cls, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Input text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        model = cls.get_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    @classmethod
    def generate_embeddings(cls, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors.
        """
        model = cls.get_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

