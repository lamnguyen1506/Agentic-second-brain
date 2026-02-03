"""Embedding generation using Sentence Transformers."""

from sentence_transformers import SentenceTransformer
from typing import List
import re


class EmbeddingModel:
    """Manages embedding generation for text."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the embedding model.

        Args:
            model_name: Name of the sentence transformer model to use
        """
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("Embedding model loaded successfully!")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding
        """
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return [emb.tolist() for emb in embeddings]


class TextChunker:
    """Handles text chunking for RAG."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """Initialize the text chunker.

        Args:
            chunk_size: Maximum number of characters per chunk
            overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> List[dict]:
        """Split text into overlapping chunks.

        Args:
            text: Text to chunk

        Returns:
            List of dictionaries containing chunk text and metadata
        """
        # Clean the text
        text = re.sub(r'\n+', '\n', text)
        text = text.strip()

        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            # Find end position
            end = start + self.chunk_size

            # If we're not at the end, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundary (., !, ?)
                sentence_end = max(
                    text.rfind('. ', start, end),
                    text.rfind('! ', start, end),
                    text.rfind('? ', start, end),
                    text.rfind('\n', start, end)
                )

                if sentence_end != -1 and sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    space = text.rfind(' ', start, end)
                    if space != -1 and space > start:
                        end = space

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'chunk_id': chunk_id,
                    'start_pos': start,
                    'end_pos': end
                })
                chunk_id += 1

            # Move start position (with overlap)
            start = end - self.overlap if end < len(text) else end

        return chunks

    def chunk_markdown_file(self, file_path: str) -> List[dict]:
        """Read and chunk a markdown file.

        Args:
            file_path: Path to markdown file

        Returns:
            List of chunks with metadata
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by major sections (## headers)
        sections = re.split(r'\n(?=##? )', content)

        all_chunks = []
        for section_idx, section in enumerate(sections):
            # Extract section title if present
            title_match = re.match(r'##? (.+)', section)
            section_title = title_match.group(1).strip() if title_match else "Introduction"

            # Chunk the section
            section_chunks = self.chunk_text(section)

            # Add section metadata to each chunk
            for chunk in section_chunks:
                chunk['metadata'] = {
                    'section': section_title,
                    'section_idx': section_idx
                }
                all_chunks.append(chunk)

        return all_chunks
