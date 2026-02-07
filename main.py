"""Main entry point for the Second Brain RAG system."""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.agent import RAGAgent
from src.memory import MemoryStore
from src.observability import log, setup_logging
from src.rag import EmbeddingModel, KnowledgeBaseIndexer, Retriever, VectorStore


def setup_environment() -> bool:
    """Setup environment and check for API key."""
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nANTHROPIC_API_KEY not found in environment!")
        print("Please create a .env file with your API key:")
        print("  ANTHROPIC_API_KEY=your_key_here")
        return False

    return True


def initialize_system(
    force_reindex: bool = False,
    use_memory: bool = True,
) -> tuple[VectorStore, Retriever, MemoryStore | None, EmbeddingModel]:
    """Initialize all components of the RAG system."""
    setup_logging()

    embedding_model = EmbeddingModel()
    vector_store = VectorStore()

    doc_count = vector_store.count()

    if doc_count == 0 or force_reindex:
        if force_reindex and doc_count > 0:
            print("Clearing existing index...")
            vector_store.clear()

        print("Knowledge base is empty. Indexing documents...")
        indexer = KnowledgeBaseIndexer(embedding_model, vector_store)

        data_path = Path("data")
        if data_path.exists():
            md_count = indexer.index_directory(str(data_path), "*.md")
            txt_count = indexer.index_directory(str(data_path), "*.txt")

            transcripts_path = data_path / "transcripts"
            transcript_count = (
                indexer.index_directory(str(transcripts_path), "*")
                if transcripts_path.exists()
                else 0
            )

            total = md_count + txt_count + transcript_count
            print(f"Indexed {total} chunks from knowledge base")
            log.info(f"Indexed {total} chunks", md=md_count, txt=txt_count, transcripts=transcript_count)
        else:
            print(f"Data directory not found: {data_path}")
            print("Please create data/ with your content")
    else:
        print(f"Knowledge base already indexed ({doc_count} documents)")

    retriever = Retriever(embedding_model, vector_store)

    memory_store = None
    if use_memory:
        memory_store = MemoryStore()
        print(f"Memory system initialized ({memory_store.count()} memories stored)")

    return vector_store, retriever, memory_store, embedding_model


async def interactive_mode(rag_agent: RAGAgent) -> None:
    """Run the system in interactive mode."""
    print("\nRAG Agent Ready! Ask me anything about your knowledge base.")
    print("  Type 'quit' or 'exit' to stop")
    print("  Type 'help' for example questions")
    print("  Type 'memory' to view recent memories")

    examples = [
        "What features are planned for Q1 2024?",
        "What are the rate limits for the API?",
        "Who is responsible for the Advanced Search feature?",
        "What is the mobile app redesign timeline?",
        "What are the top customer requests?",
    ]

    while True:
        print()
        user_input = input("Your question: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        if user_input.lower() == "help":
            print("\nExample questions you can ask:")
            for i, example in enumerate(examples, 1):
                print(f"  {i}. {example}")
            continue

        if user_input.lower() == "memory":
            if rag_agent.memory_store:
                memories = rag_agent.memory_store.get_recent_memories(limit=5)
                if memories:
                    print("\nRecent memories:")
                    for mem in memories:
                        print(f"  [{mem.type}] {mem.content[:100]}...")
                else:
                    print("\nNo memories stored yet.")
            else:
                print("\nMemory system is not enabled.")
            continue

        try:
            print("\nSearching knowledge base and generating answer...")
            response = await rag_agent.ask(user_input)
            print(response.display())
        except Exception as e:
            log.error(f"Error processing question: {e}")
            print(f"\nError: {e}")
            print("Please try again or check your API key configuration.")


def run_ingest(embedding_model: EmbeddingModel, vector_store: VectorStore) -> None:
    """Re-index the knowledge base."""
    print("Re-indexing knowledge base...")
    vector_store.clear()

    indexer = KnowledgeBaseIndexer(embedding_model, vector_store)
    data_path = Path("data")
    if data_path.exists():
        md_count = indexer.index_directory(str(data_path), "*.md")
        txt_count = indexer.index_directory(str(data_path), "*.txt")

        transcripts_path = data_path / "transcripts"
        transcript_count = (
            indexer.index_directory(str(transcripts_path), "*")
            if transcripts_path.exists()
            else 0
        )

        total = md_count + txt_count + transcript_count
        print(f"Successfully indexed {total} chunks")
    else:
        print(f"Data directory not found: {data_path}")


def run_eval() -> None:
    """Run the evaluation suite."""
    print("Running evaluation suite...")
    from src.evals import run_evaluations

    asyncio.run(run_evaluations())


def clear_memory() -> None:
    """Clear all stored memories."""
    memory_store = MemoryStore()
    count = memory_store.count()

    if count == 0:
        print("No memories to clear.")
        return

    confirm = input(f"Are you sure you want to delete {count} memories? (y/N): ")
    if confirm.lower() == "y":
        deleted = memory_store.clear_all()
        print(f"Cleared {deleted} memories.")
    else:
        print("Cancelled.")


def main() -> None:
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Second Brain - Personal Knowledge System with RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python main.py              # Interactive chat (default)
  uv run python main.py --ingest     # Re-index knowledge base
  uv run python main.py --eval       # Run evaluations
  uv run python main.py --clear-memory  # Clear stored memories
        """,
    )

    parser.add_argument("--ingest", action="store_true", help="Re-index the knowledge base")
    parser.add_argument("--eval", action="store_true", help="Run the evaluation suite")
    parser.add_argument("--clear-memory", action="store_true", help="Clear all stored memories")
    parser.add_argument("--no-memory", action="store_true", help="Disable memory system")

    args = parser.parse_args()

    if args.clear_memory:
        clear_memory()
        return

    if not args.ingest and not setup_environment():
        sys.exit(1)

    if args.ingest:
        embedding_model = EmbeddingModel()
        vector_store = VectorStore()
        run_ingest(embedding_model, vector_store)
        return

    if args.eval:
        if not setup_environment():
            sys.exit(1)
        run_eval()
        return

    # Default: interactive mode
    vector_store, retriever, memory_store, _ = initialize_system(
        use_memory=not args.no_memory,
    )

    rag_agent = RAGAgent(
        retriever=retriever,
        memory_store=memory_store,
        use_memory=not args.no_memory,
    )

    asyncio.run(interactive_mode(rag_agent))


if __name__ == "__main__":
    main()
