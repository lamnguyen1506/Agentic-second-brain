"""Knowledge base indexing utilities."""

from pathlib import Path

from src.rag.chunking import TextChunker
from src.rag.embeddings import EmbeddingModel
from src.rag.vector_store import VectorStore


class KnowledgeBaseIndexer:
    """Handles indexing of knowledge base files into the vector store."""

    def __init__(self, embedding_model: EmbeddingModel, vector_store: VectorStore):
        """Initialize the indexer.

        Args:
            embedding_model: The embedding model to use
            vector_store: The vector store to populate
        """
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.chunker = TextChunker()

    def index_file(self, file_path: str) -> int:
        """Index a single file into the vector store.

        Args:
            file_path: Path to the file to index

        Returns:
            Number of chunks indexed
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        print(f"\nIndexing file: {file_path}")

        # Read and chunk the file
        if file_path_obj.suffix == ".md":
            chunks = self.chunker.chunk_markdown_file(file_path)
        else:
            # For other text files
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            chunks = self.chunker.chunk_text(content)
            # Add basic metadata
            for chunk in chunks:
                if "metadata" not in chunk:
                    chunk["metadata"] = {}
                chunk["metadata"]["file"] = file_path_obj.name

        if not chunks:
            print("No chunks created from file.")
            return 0

        print(f"Created {len(chunks)} chunks")

        # Generate embeddings
        print("Generating embeddings...")
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.embedding_model.generate_embeddings(texts)

        # Prepare metadata and IDs
        metadatas = []
        ids = []
        for i, chunk in enumerate(chunks):
            metadata = chunk.get("metadata", {})
            metadata["chunk_id"] = chunk["chunk_id"]
            metadata["file"] = file_path_obj.name
            metadatas.append(metadata)
            ids.append(f"{file_path_obj.stem}_{i}")

        # Add to vector store
        self.vector_store.add_documents(
            documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids
        )

        print(f"Successfully indexed {len(chunks)} chunks!")
        return len(chunks)

    def index_directory(self, directory_path: str, pattern: str = "*.md") -> int:
        """Index all files in a directory matching a pattern.

        Args:
            directory_path: Path to the directory
            pattern: Glob pattern for files to index

        Returns:
            Total number of chunks indexed
        """
        directory = Path(directory_path)

        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Invalid directory: {directory_path}")

        files = list(directory.glob(pattern))

        if not files:
            print(f"No files found matching pattern '{pattern}' in {directory_path}")
            return 0

        print(f"\nFound {len(files)} files to index")

        total_chunks = 0
        for file_path in files:
            chunks = self.index_file(str(file_path))
            total_chunks += chunks

        return total_chunks
