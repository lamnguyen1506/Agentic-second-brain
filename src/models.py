"""Pydantic models for the RAG system."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


# Response models

class SourceSnippet(BaseModel):
    """A snippet of text retrieved from the knowledge base."""

    text: str = Field(description="The retrieved text snippet")
    relevance_score: float = Field(
        description="Similarity score between 0 and 1", ge=0.0, le=1.0
    )
    metadata: dict = Field(
        default_factory=dict, description="Additional metadata about the source"
    )


class AgentResponse(BaseModel):
    """Structured response from the RAG agent."""

    answer: str = Field(description="The agent's answer to the user's question")
    sources: list[SourceSnippet] = Field(
        description="Source snippets used to generate the answer", default_factory=list
    )
    confidence: str = Field(
        description="Confidence level: high, medium, low, or none", default="medium"
    )

    def display(self) -> str:
        """Format the response for display."""
        output = [f"\n{'='*60}"]
        output.append("ANSWER:")
        output.append(f"{self.answer}")
        output.append(f"\nConfidence: {self.confidence.upper()}")

        if self.sources:
            output.append(f"\n{'='*60}")
            output.append("SOURCES:")
            for i, source in enumerate(self.sources, 1):
                output.append(f"\n[{i}] Relevance: {source.relevance_score:.2f}")
                output.append(f"    {source.text[:200]}...")
                if source.metadata:
                    output.append(f"    Metadata: {source.metadata}")

        output.append(f"{'='*60}\n")
        return "\n".join(output)


# Memory models

class MemoryEntry(BaseModel):
    """A memory entry stored in the knowledge base."""

    id: str = Field(description="Unique identifier for the memory")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the memory was created",
    )
    type: Literal["conversation", "preference", "fact"] = Field(
        description="Type of memory: conversation summary, user preference, or important fact"
    )
    content: str = Field(description="The memory content")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
