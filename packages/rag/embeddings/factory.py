"""
Embedding Factory for creating configured embedding provider instances.
"""

from typing import Optional
from apps.backend.app.core.config import settings
from packages.rag.embeddings.base import BaseEmbeddingProvider
from packages.rag.embeddings.openai_embedding import OpenAIEmbeddingProvider
from packages.rag.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddingProvider,
)


class EmbeddingFactory:
    """Factory for generating embedding provider instances."""

    @staticmethod
    def get_provider(provider_name: Optional[str] = None) -> BaseEmbeddingProvider:
        """Instantiate embedding provider.

        Args:
            provider_name: Optional provider string ('openai', 'bge', 'e5', 'sentence_transformers').

        Returns:
            BaseEmbeddingProvider instance.
        """
        return OpenAIEmbeddingProvider(
            api_key=settings.OPENAI_API_KEY or "",
            dimension=settings.EMBEDDING_DIMENSION,
        )
