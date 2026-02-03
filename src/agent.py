"""Pydantic AI agent with RAG capabilities."""

from typing import Optional
from pydantic_ai import Agent, RunContext
from src.models import AgentResponse, SourceSnippet
from src.retrieval_tool import RetrievalTool
from dataclasses import dataclass


@dataclass
class AgentDeps:
    """Dependencies for the RAG agent."""
    retrieval_tool: RetrievalTool


# System prompt for the RAG agent
SYSTEM_PROMPT = """You are a knowledgeable assistant that helps users find information from their personal knowledge base.

Your responsibilities:
1. Use the retrieve_context tool to search for relevant information before answering questions
2. Base your answers primarily on the retrieved context
3. Cite your sources by referencing the information from the context
4. If the context doesn't contain enough information to answer confidently, acknowledge this
5. Be concise but thorough in your responses

When providing answers:
- Set confidence to "high" if the context strongly supports your answer
- Set confidence to "medium" if the context partially supports your answer
- Set confidence to "low" if you're uncertain or extrapolating beyond the context
- Set confidence to "none" if no relevant context was found

Always include the source snippets you used in your response."""

async def retrieve_context(ctx: RunContext[AgentDeps], query: str) -> str:
    """Search the knowledge base for relevant information.

    Args:
        ctx: The run context containing dependencies
        query: The search query

    Returns:
        Formatted context string with relevant information
    """
    # Retrieve relevant documents
    results = ctx.deps.retrieval_tool.retrieve(query, top_k=3)

    # Format the context
    context = ctx.deps.retrieval_tool.format_context(results)

    return context


async def validate_response(ctx: RunContext[AgentDeps], result: AgentResponse) -> AgentResponse:
    """Validate and enrich the agent's response with source information.

    Args:
        ctx: The run context
        result: The agent's response

    Returns:
        Validated and enriched response
    """
    # If sources are empty, try to populate them from the last retrieval
    # This is a fallback in case the agent didn't populate sources properly
    if not result.sources:
        # We could retrieve again here, but for now just ensure the structure is correct
        pass

    return result


class RAGAgent:
    def __init__(self, retrieval_tool: RetrievalTool, model: str = 'anthropic:claude-sonnet-4-5'):
        self.retrieval_tool = retrieval_tool
        self.model = model
        self._agent: Optional[Agent[AgentDeps, AgentResponse]] = None

    def _get_agent(self) -> Agent[AgentDeps, AgentResponse]:
        if self._agent is None:
            agent = Agent(
                self.model,
                deps_type=AgentDeps,
                output_type=AgentResponse,
                system_prompt=SYSTEM_PROMPT,
            )

            agent.tool(retrieve_context)
            agent.output_validator(validate_response)

            self._agent = agent

        return self._agent

    async def ask(self, question: str) -> AgentResponse:
        deps = AgentDeps(retrieval_tool=self.retrieval_tool)

        # Run the agent
        agent = self._get_agent()
        result = await agent.run(question, deps=deps)

        output = result.output

        # Ensure sources are populated
        if not output.sources:
            retrieved_docs = self.retrieval_tool.retrieve(question, top_k=3)
            output.sources = [
                SourceSnippet(
                    text=doc['text'],
                    relevance_score=doc['similarity_score'],
                    metadata=doc['metadata']
                )
                for doc in retrieved_docs
            ]

        return output
