"""RAG Agent with memory capabilities."""

from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from src.config import get_settings
from src.guardrails import redact_pii
from src.models import AgentResponse, SourceSnippet
from src.observability import log


SYSTEM_PROMPT = """You are a knowledgeable assistant that helps users find information from their personal knowledge base. You have access to both a vector-based knowledge retrieval system and a persistent memory system.

Your responsibilities:
1. Use the retrieve_context tool to search for relevant information before answering questions
2. Use recall_memory to check for relevant past conversations or user preferences
3. Use save_memory to store important facts, user preferences, or conversation summaries
4. Use summarize when dealing with long text or multiple retrieved chunks
5. Base your answers primarily on the retrieved context and relevant memories
6. Cite your sources by referencing the information from the context
7. If the context doesn't contain enough information to answer confidently, acknowledge this
8. Be concise but thorough in your responses

When providing answers:
- Set confidence to "high" if the context strongly supports your answer
- Set confidence to "medium" if the context partially supports your answer
- Set confidence to "low" if you're uncertain or extrapolating beyond the context
- Set confidence to "none" if no relevant context was found

Always include the source snippets you used in your response.

Memory Guidelines:
- Save user preferences when they express them (e.g., "I prefer concise answers")
- Save important facts that might be useful later
- Recall memories when the user asks about previous conversations or their preferences"""


@dataclass
class AgentDeps:
    """Dependencies for the RAG agent."""

    retriever: "Retriever"  # type: ignore
    memory_store: "MemoryStore | None" = None  # type: ignore
    use_memory: bool = True


async def retrieve_context(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search the knowledge base for relevant information.

    Args:
        ctx: The run context containing dependencies
        query: The search query

    Returns:
        Formatted context string with relevant information
    """
    results = ctx.deps.retriever.retrieve(query, top_k=3)
    context = ctx.deps.retriever.format_context(results)
    log.info(f"Retrieved {len(results)} documents for query", query=query[:50])
    return context


async def save_memory(
    ctx: RunContext[AgentDeps],
    content: str,
    memory_type: str = "conversation",
    metadata: dict | None = None,
) -> str:
    """Store a memory entry (conversation summary, user preference, or fact).

    Args:
        ctx: The run context containing dependencies
        content: The content to store (will be automatically PII-redacted)
        memory_type: Type of memory: "conversation", "preference", or "fact"
        metadata: Optional additional metadata

    Returns:
        Confirmation message with memory ID
    """
    if not ctx.deps.memory_store or not ctx.deps.use_memory:
        return "Memory system is not enabled."

    redacted_content = redact_pii(content)
    entry = ctx.deps.memory_store.save_memory(
        content=redacted_content,
        memory_type=memory_type,
        metadata=metadata or {},
    )
    log.info(f"Saved memory: {entry.id}", memory_id=entry.id, memory_type=memory_type)
    return f"Memory saved successfully with ID: {entry.id}"


async def recall_memory(
    ctx: RunContext[AgentDeps],
    query: str | None = None,
    memory_type: str | None = None,
    limit: int = 5,
) -> str:
    """Retrieve relevant past conversations or preferences from memory.

    Args:
        ctx: The run context containing dependencies
        query: Optional search query to filter memories
        memory_type: Optional filter by type: "conversation", "preference", or "fact"
        limit: Maximum number of memories to return

    Returns:
        Formatted string of relevant memories
    """
    if not ctx.deps.memory_store or not ctx.deps.use_memory:
        return "Memory system is not enabled."

    if query:
        memories = ctx.deps.memory_store.search_memory(
            query=query, memory_type=memory_type, limit=limit,
        )
    else:
        memories = ctx.deps.memory_store.get_recent_memories(
            limit=limit, memory_type=memory_type,
        )

    if not memories:
        log.info("No memories found", query=query, memory_type=memory_type)
        return "No relevant memories found."

    formatted = []
    for mem in memories:
        formatted.append(
            f"[{mem.type.upper()}] ({mem.timestamp.strftime('%Y-%m-%d %H:%M')})\n{mem.content}"
        )

    log.info(f"Recalled {len(memories)} memories", count=len(memories), query=query)
    return "\n\n---\n\n".join(formatted)


async def summarize(ctx: RunContext[AgentDeps], text: str, max_sentences: int = 3) -> str:
    """Summarize long text or multiple retrieved chunks.

    Args:
        ctx: The run context containing dependencies
        text: The text to summarize
        max_sentences: Target number of sentences for the summary

    Returns:
        A concise summary of the input text
    """
    sentences = text.replace("\n", " ").split(". ")
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= max_sentences:
        return text

    summary_parts = []
    if sentences:
        summary_parts.append(sentences[0])
    if len(sentences) > 2 and max_sentences > 2:
        mid = len(sentences) // 2
        summary_parts.append(sentences[mid])
    if len(sentences) > 1:
        summary_parts.append(sentences[-1])

    summary = ". ".join(summary_parts)
    if not summary.endswith("."):
        summary += "."

    log.info(f"Summarized text from {len(text)} chars to {len(summary)} chars")
    return summary


class RAGAgent:
    """RAG Agent with memory capabilities."""

    def __init__(
        self,
        retriever=None,
        memory_store=None,
        model: str | None = None,
        use_memory: bool = True,
    ):
        settings = get_settings()
        self.retriever = retriever
        self.memory_store = memory_store
        self.model = model or settings.llm_model
        self.use_memory = use_memory
        self._agent: Agent[AgentDeps, AgentResponse] | None = None

    def _get_agent(self) -> Agent[AgentDeps, AgentResponse]:
        """Get or create the Pydantic AI agent."""
        if self._agent is None:
            agent = Agent(
                self.model,
                deps_type=AgentDeps,
                output_type=AgentResponse,
                system_prompt=SYSTEM_PROMPT,
            )
            agent.tool(retrieve_context)
            agent.tool(save_memory)
            agent.tool(recall_memory)
            agent.tool(summarize)
            self._agent = agent

        return self._agent

    async def ask(self, question: str) -> AgentResponse:
        """Ask the agent a question."""
        deps = AgentDeps(
            retriever=self.retriever,
            memory_store=self.memory_store,
            use_memory=self.use_memory,
        )

        agent = self._get_agent()
        result = await agent.run(question, deps=deps)
        output = result.output

        if not output.sources and self.retriever:
            retrieved_docs = self.retriever.retrieve(question, top_k=3)
            output.sources = [
                SourceSnippet(
                    text=doc["text"],
                    relevance_score=doc["similarity_score"],
                    metadata=doc["metadata"],
                )
                for doc in retrieved_docs
            ]

        log.info(
            "Agent response generated",
            confidence=output.confidence,
            source_count=len(output.sources),
        )
        return output

    async def ask_without_memory(self, question: str) -> AgentResponse:
        """Ask the agent a question without using memory."""
        original_use_memory = self.use_memory
        self.use_memory = False
        try:
            return await self.ask(question)
        finally:
            self.use_memory = original_use_memory

    async def ask_without_rag(self, question: str) -> AgentResponse:
        """Ask the agent a question without RAG retrieval."""
        agent = Agent(
            self.model,
            output_type=AgentResponse,
            system_prompt="You are a helpful assistant. Answer questions based on your knowledge. Be honest if you don't know something.",
        )
        result = await agent.run(question)
        return result.output
