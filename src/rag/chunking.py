"""Text chunking utilities for RAG."""

import re

from src.config import get_settings


class TextChunker:
    """Handles text chunking for RAG."""

    def __init__(self, chunk_size: int | None = None, overlap: int | None = None):
        """Initialize the text chunker.

        Args:
            chunk_size: Maximum number of characters per chunk.
                       Defaults to settings.embedding.chunk_size.
            overlap: Number of characters to overlap between chunks.
                    Defaults to settings.embedding.chunk_overlap.
        """
        settings = get_settings()
        self.chunk_size = chunk_size or settings.chunk_size
        self.overlap = overlap or settings.chunk_overlap

    def chunk_text(self, text: str) -> list[dict]:
        """Split text into overlapping chunks.

        Args:
            text: Text to chunk

        Returns:
            List of dictionaries containing chunk text and metadata
        """
        # Clean the text
        text = re.sub(r"\n+", "\n", text)
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
                    text.rfind(". ", start, end),
                    text.rfind("! ", start, end),
                    text.rfind("? ", start, end),
                    text.rfind("\n", start, end),
                )

                if sentence_end != -1 and sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    space = text.rfind(" ", start, end)
                    if space != -1 and space > start:
                        end = space

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    {"text": chunk_text, "chunk_id": chunk_id, "start_pos": start, "end_pos": end}
                )
                chunk_id += 1

            # Move start position (with overlap)
            start = end - self.overlap if end < len(text) else end

        return chunks

    def chunk_markdown_file(self, file_path: str) -> list[dict]:
        """Read and chunk a markdown file.

        Args:
            file_path: Path to markdown file

        Returns:
            List of chunks with metadata
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split by major sections (## headers)
        sections = re.split(r"\n(?=##? )", content)

        all_chunks = []
        for section_idx, section in enumerate(sections):
            # Extract section title if present
            title_match = re.match(r"##? (.+)", section)
            section_title = title_match.group(1).strip() if title_match else "Introduction"

            # Chunk the section
            section_chunks = self.chunk_text(section)

            # Add section metadata to each chunk
            for chunk in section_chunks:
                chunk["metadata"] = {"section": section_title, "section_idx": section_idx}
                all_chunks.append(chunk)

        return all_chunks
