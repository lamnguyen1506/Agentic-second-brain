"""Vector store implementation using ChromaDB."""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path


class VectorStore:
    """Manages vector storage and retrieval using ChromaDB."""

    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "knowledge_base"):
        """Initialize the vector store.

        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection to use
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # Create persist directory if it doesn't exist
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistence
        print(f"Initializing ChromaDB at {persist_directory}...")
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Personal knowledge base for RAG"}
        )

        print(f"Vector store initialized. Collection '{collection_name}' ready.")

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """Add documents to the vector store.

        Args:
            documents: List of text documents
            embeddings: List of embedding vectors
            metadatas: Optional list of metadata dictionaries
            ids: Optional list of document IDs (auto-generated if not provided)
        """
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        if metadatas is None:
            metadatas = [{} for _ in documents]

        print(f"Adding {len(documents)} documents to vector store...")

        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        print(f"Successfully added {len(documents)} documents!")

    def query(
        self,
        query_embedding: List[float],
        n_results: int = 3,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query the vector store for similar documents.

        Args:
            query_embedding: Embedding vector of the query
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            Dictionary containing results with documents, distances, and metadatas
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )

        return results

    def count(self) -> int:
        """Get the number of documents in the collection.

        Returns:
            Number of documents
        """
        return self.collection.count()

    def clear(self) -> None:
        """Clear all documents from the collection."""
        # Delete and recreate the collection
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Personal knowledge base for RAG"}
        )
        print("Collection cleared!")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store.

        Returns:
            Dictionary with statistics
        """
        count = self.count()

        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "persist_directory": self.persist_directory
        }
