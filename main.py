"""Main entry point for the Personal Knowledge Retriever RAG system."""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

from src.embeddings import EmbeddingModel
from src.vector_store import VectorStore
from src.retrieval_tool import RetrievalTool
from src.indexer import KnowledgeBaseIndexer
from src.agent import RAGAgent


def setup_environment():
    """Setup environment and check for API key."""
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n⚠️  ANTHROPIC_API_KEY not found in environment!")
        print("Please create a .env file with your API key:")
        print("  ANTHROPIC_API_KEY=your_key_here")
        print("\nOr export it in your shell:")
        print("  export ANTHROPIC_API_KEY=your_key_here")
        return False

    return True


def initialize_system():
    """Initialize all components of the RAG system."""
    print("\n" + "="*60)
    print("Personal Knowledge Retriever - RAG System")
    print("="*60)

    # Initialize embedding model
    embedding_model = EmbeddingModel()

    # Initialize vector store
    vector_store = VectorStore(
        persist_directory="./chroma_db",
        collection_name="knowledge_base"
    )

    # Check if we need to index the knowledge base
    doc_count = vector_store.count()

    if doc_count == 0:
        print("\n📚 Knowledge base is empty. Indexing documents...")
        indexer = KnowledgeBaseIndexer(embedding_model, vector_store)

        # Index the knowledge base
        kb_path = Path("data/knowledge_base.md")
        if kb_path.exists():
            chunks_indexed = indexer.index_file(str(kb_path))
            print(f"\n✅ Indexed {chunks_indexed} chunks from knowledge base")
        else:
            print(f"\n⚠️  Knowledge base file not found: {kb_path}")
            print("Please create data/knowledge_base.md with your content")
            return None, None
    else:
        print(f"\n✅ Knowledge base already indexed ({doc_count} documents)")

    # Initialize retrieval tool
    retrieval_tool = RetrievalTool(embedding_model, vector_store)

    # Display statistics
    stats = vector_store.get_stats()
    print(f"\n📊 Vector Store Statistics:")
    print(f"   Collection: {stats['collection_name']}")
    print(f"   Documents: {stats['document_count']}")
    print(f"   Location: {stats['persist_directory']}")

    return vector_store, retrieval_tool


async def interactive_mode(rag_agent: RAGAgent):
    """Run the system in interactive mode."""
    print("\n" + "="*60)
    print("🤖 RAG Agent Ready! Ask me anything about your knowledge base.")
    print("   Type 'quit' or 'exit' to stop, 'help' for examples")
    print("="*60)

    # Example questions
    examples = [
        "What features are planned for Q1 2024?",
        "What are the rate limits for the API?",
        "Who is responsible for the Advanced Search feature?",
        "What is the mobile app redesign timeline?",
        "What are the top customer requests?"
    ]

    while True:
        print("\n" + "-"*60)
        user_input = input("❓ Your question: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break

        if user_input.lower() == 'help':
            print("\n💡 Example questions you can ask:")
            for i, example in enumerate(examples, 1):
                print(f"   {i}. {example}")
            continue

        # Ask the question
        try:
            print("\n🔍 Searching knowledge base and generating answer...")
            response = await rag_agent.ask(user_input)
            print(response.display())
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again or check your API key configuration.")


async def demo_mode(rag_agent: RAGAgent):
    """Run a demo with pre-defined questions."""
    print("\n" + "="*60)
    print("🎬 Running Demo Mode")
    print("="*60)

    demo_questions = [
        "What features are planned for Q1 2024?",
        "What are the API rate limits?",
        "What is the status of the bulk export feature?",
    ]

    for i, question in enumerate(demo_questions, 1):
        print(f"\n\n{'='*60}")
        print(f"Demo Question {i}/{len(demo_questions)}")
        print(f"{'='*60}")
        print(f"❓ {question}")

        try:
            response = await rag_agent.ask(question)
            print(response.display())
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

        if i < len(demo_questions):
            print("\nPress Enter to continue...")
            input()


def main():
    """Main function."""
    # Check environment
    if not setup_environment():
        return

    # Initialize system
    vector_store, retrieval_tool = initialize_system()

    if retrieval_tool is None:
        return

    rag_agent = RAGAgent(retrieval_tool=retrieval_tool)

    # Ask user for mode
    print("\n" + "="*60)
    print("Select mode:")
    print("  1. Interactive mode (ask your own questions)")
    print("  2. Demo mode (run pre-defined questions)")
    print("="*60)

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "2":
        asyncio.run(demo_mode(rag_agent))
    else:
        asyncio.run(interactive_mode(rag_agent))


if __name__ == "__main__":
    main()
