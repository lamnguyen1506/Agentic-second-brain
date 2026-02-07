"""Retrieval functionality for RAG."""

from typing import Any

from src.config import get_settings
from src.rag.embeddings import EmbeddingModel
from src.rag.vector_store import VectorStore


class Retriever:
    """Retrieves relevant context from the knowledge base."""

    def __init__(self, embedding_model: EmbeddingModel, vector_store: VectorStore):
        """Initialize the retriever.

        Args:
            embedding_model: The embedding model to use
            vector_store: The vector store to query
        """
        self.embedding_model = embedding_model
        self.vector_store = vector_store

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        """Retrieve relevant documents for a query.

        Args:
            query: The search query
            top_k: Number of documents to retrieve.
                  Defaults to settings.agent.retrieval_top_k.

        Returns:
            List of dictionaries containing retrieved documents and metadata
        """
        settings = get_settings()
        top_k = top_k or settings.retrieval_top_k

        # Generate embedding for the query
        query_embedding = self.embedding_model.generate_embedding(query)

        # Query the vector store
        results = self.vector_store.query(query_embedding=query_embedding, n_results=top_k)

        # Format results
        formatted_results = []
        if results and results["documents"] and len(results["documents"]) > 0:
            documents = results["documents"][0]
            distances = results["distances"][0]
            metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(documents)

            for doc, distance, metadata in zip(documents, distances, metadatas):
                # Convert distance to similarity score (ChromaDB uses L2 distance)
                # Normalize to 0-1 range where 1 is most similar
                similarity = 1 / (1 + distance)

                formatted_results.append(
                    {
                        "text": doc,
                        "similarity_score": similarity,
                        "distance": distance,
                        "metadata": metadata,
                    }
                )

        return formatted_results

    def format_context(self, results: list[dict[str, Any]]) -> str:
        """Format retrieval results as context string.

        Args:
            results: List of retrieval results

        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant information found in the knowledge base."

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Source {i}] (Relevance: {result['similarity_score']:.2f})")
            context_parts.append(result["text"])
            context_parts.append("")  # Empty line between sources

        return "\n".join(context_parts)


# Backward compatibility alias
RetrievalTool = Retriever
