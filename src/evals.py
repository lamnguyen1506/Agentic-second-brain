"""Evaluation framework using pydantic-evals."""

from dataclasses import dataclass

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EvaluationReason, Evaluator, EvaluatorContext

from src.agent import RAGAgent
from src.memory import MemoryStore
from src.models import AgentResponse
from src.observability import log, setup_logging
from src.rag import EmbeddingModel, KnowledgeBaseIndexer, Retriever, VectorStore


# Custom evaluators


@dataclass
class TopicCoverage(Evaluator[str, AgentResponse, dict]):
    """Check if expected keywords appear in the agent's answer."""

    def evaluate(self, ctx: EvaluatorContext[str, AgentResponse, dict]) -> EvaluationReason:
        topics = ctx.metadata.get("expected_topics", []) if ctx.metadata else []
        if not topics:
            return EvaluationReason(value=True, reason="No topics to check")

        answer_lower = ctx.output.answer.lower()
        found = [t for t in topics if t.lower() in answer_lower]
        coverage = len(found) / len(topics)

        return EvaluationReason(
            value=coverage >= 0.5,
            reason=f"Found {len(found)}/{len(topics)} topics ({coverage:.0%})",
        )


@dataclass
class ConfidenceCheck(Evaluator[str, AgentResponse, dict]):
    """Check if the confidence level matches expectations."""

    def evaluate(self, ctx: EvaluatorContext[str, AgentResponse, dict]) -> EvaluationReason:
        expected = ctx.metadata.get("expected_confidence") if ctx.metadata else None
        if not expected:
            return EvaluationReason(value=True, reason="No confidence expectation")

        actual = ctx.output.confidence
        # Accept the expected level, or higher confidence as OK
        acceptable = {expected}
        if expected == "medium":
            acceptable.add("high")
        elif expected == "low":
            acceptable |= {"medium", "high"}
        elif expected == "none":
            acceptable.add("low")

        passed = actual in acceptable
        return EvaluationReason(
            value=passed,
            reason=f"Expected {expected}, got {actual}",
        )


# Task function (initialized lazily)

_agent: RAGAgent | None = None


def _get_agent() -> RAGAgent:
    global _agent
    if _agent is None:
        raise RuntimeError("Agent not initialized. Call run_evaluations() first.")
    return _agent


async def task(question: str) -> AgentResponse:
    """Task function: ask the agent a question and return the response."""
    agent = _get_agent()
    return await agent.ask(question)


# Dataset

dataset = Dataset[str, AgentResponse, dict](
    name="second-brain-evals",
    cases=[
        Case(
            name="retrieval_q1_features",
            inputs="What features are planned for Q1 2024?",
            metadata={
                "expected_topics": ["Advanced Search", "API Rate Limiting", "Bulk Export"],
                "expected_confidence": "high",
            },
        ),
        Case(
            name="retrieval_api_limits",
            inputs="What are the API rate limits for the free tier?",
            metadata={
                "expected_topics": ["100 requests", "minute", "free"],
                "expected_confidence": "high",
            },
        ),
        Case(
            name="retrieval_search_owner",
            inputs="Who is responsible for the Advanced Search feature?",
            metadata={
                "expected_topics": ["Mike Johnson"],
                "expected_confidence": "high",
            },
        ),
        Case(
            name="retrieval_database",
            inputs="What database is used for the backend?",
            metadata={
                "expected_topics": ["PostgreSQL"],
                "expected_confidence": "high",
            },
        ),
        Case(
            name="retrieval_search_latency",
            inputs="What is the target search latency for the new search feature?",
            metadata={
                "expected_topics": ["200ms", "p95"],
                "expected_confidence": "high",
            },
        ),
        Case(
            name="synthesis_pain_points",
            inputs="What are the main customer pain points and how are they being addressed?",
            metadata={
                "expected_topics": ["search", "slow", "mobile", "crash"],
                "expected_confidence": "medium",
            },
        ),
        Case(
            name="synthesis_architecture",
            inputs="Summarize the technical architecture of the system",
            metadata={
                "expected_topics": ["React", "Node.js", "PostgreSQL", "Redis", "AWS"],
                "expected_confidence": "medium",
            },
        ),
        Case(
            name="synthesis_security",
            inputs="What security measures are in place for the system?",
            metadata={
                "expected_topics": ["authentication", "encryption", "session"],
                "expected_confidence": "medium",
            },
        ),
        Case(
            name="edge_weather",
            inputs="What is the weather today?",
            metadata={
                "expected_topics": [],
                "expected_confidence": "none",
            },
        ),
        Case(
            name="edge_quantum",
            inputs="Tell me about quantum computing",
            metadata={
                "expected_topics": [],
                "expected_confidence": "none",
            },
        ),
    ],
    evaluators=[TopicCoverage(), ConfidenceCheck()],
)


# Entry point

async def run_evaluations(data_dir: str = "data") -> None:
    """Run the full evaluation suite using pydantic-evals."""
    global _agent

    setup_logging(log_level="WARNING")
    log.info("Initializing evaluation environment...")

    embedding_model = EmbeddingModel()
    vector_store = VectorStore()
    memory_store = MemoryStore()

    if vector_store.count() == 0:
        indexer = KnowledgeBaseIndexer(embedding_model, vector_store)
        indexer.index_directory(data_dir, "*.md")

    retriever = Retriever(embedding_model, vector_store)
    _agent = RAGAgent(
        retriever=retriever,
        memory_store=memory_store,
        use_memory=True,
    )

    report = await dataset.evaluate(task)
    report.print(include_input=True, include_reasons=True)
