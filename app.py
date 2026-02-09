"""Streamlit chat UI for the Second Brain RAG system."""

import asyncio
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from pydantic_ai.mcp import MCPServerStdio

from src.agent import RAGAgent
from src.memory import MemoryStore
from src.observability import setup_logging
from src.rag import EmbeddingModel, KnowledgeBaseIndexer, Retriever, VectorStore

load_dotenv()


@st.cache_resource
def init_system():
    """Initialize the RAG system (cached across Streamlit reruns)."""
    setup_logging()

    embedding_model = EmbeddingModel()
    vector_store = VectorStore()

    if vector_store.count() == 0:
        indexer = KnowledgeBaseIndexer(embedding_model, vector_store)
        data_path = Path("data")
        if data_path.exists():
            indexer.index_directory(str(data_path), "*.md")
            indexer.index_directory(str(data_path), "*.txt")
            transcripts_path = data_path / "transcripts"
            if transcripts_path.exists():
                indexer.index_directory(str(transcripts_path), "*")

    retriever = Retriever(embedding_model, vector_store)
    memory_store = MemoryStore()

    notion_server = MCPServerStdio(
        "uv", args=["run", "python", "src/mcp_notion.py"],
        env={**os.environ},
    )

    agent = RAGAgent(
        retriever=retriever,
        memory_store=memory_store,
        use_memory=True,
        mcp_servers=[notion_server],
    )

    return agent


def main():
    st.set_page_config(page_title="Second Brain", page_icon="🧠", layout="centered")

    # Sidebar
    with st.sidebar:
        st.title("Second Brain")
        st.markdown(
            "RAG agent with **knowledge base retrieval**, "
            "**persistent memory**, and **Notion** integration."
        )
        st.divider()
        st.markdown("**Tools available:**")
        st.markdown(
            "- 🔍 Knowledge base search\n"
            "- 🧠 Memory (save / recall)\n"
            "- 📝 Notion (search / read / create / archive)\n"
            "- 📄 Summarize"
        )

    # Init agent
    agent = init_system()

    # Session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Sources"):
                    for i, src in enumerate(msg["sources"], 1):
                        st.markdown(f"**[{i}]** (relevance: {src['score']:.2f})")
                        st.caption(src["text"][:300])

    # Chat input
    if prompt := st.chat_input("Ask about your knowledge base or Notion..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = asyncio.run(agent.ask(prompt))

            st.markdown(response.answer)

            sources_data = []
            if response.sources:
                with st.expander("Sources"):
                    for i, src in enumerate(response.sources, 1):
                        st.markdown(f"**[{i}]** (relevance: {src.relevance_score:.2f})")
                        st.caption(src.text[:300])
                        sources_data.append({
                            "text": src.text[:300],
                            "score": src.relevance_score,
                        })

            st.caption(f"Confidence: {response.confidence}")

        st.session_state.messages.append({
            "role": "assistant",
            "content": response.answer,
            "sources": sources_data,
        })


if __name__ == "__main__":
    main()
