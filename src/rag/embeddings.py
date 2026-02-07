"""Embedding generation using Sentence Transformers."""

from sentence_transformers import SentenceTransformer

from src.config import get_settings


class EmbeddingModel:
    """Manages embedding generation for text."""

    def __init__(self, model_name: str | None = None):
        """Initialize the embedding model.

        Args:
            model_name: Name of the sentence transformer model to use.
                       Defaults to settings.embedding.model_name.
        """
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model

        print(f"Loading embedding model: {self.model_name}...")
        self.model = SentenceTransformer(self.model_name)
        print("Embedding model loaded successfully!")

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding
        """
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return [emb.tolist() for emb in embeddings]
