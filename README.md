# Personal Knowledge Retriever - RAG System

A single-agent RAG (Retrieval-Augmented Generation) application built with Pydantic AI that answers questions based on your personal knowledge base with cited sources.

**What it does:** Retrieves relevant context from a vector database → Augments LLM prompts → Generates accurate answers with source citations.

---

## 🚀 Quick Start (3 Steps)

```bash
# 1. Install dependencies (super fast with uv!)
curl -LsSf https://astral.sh/uv/install.sh | sh 
uv sync                                          

# 2. Set up API key
cp .env.example .env
# Edit .env: ANTHROPIC_API_KEY=your_key_here

# 3. Run
uv run python main.py
```

**Using traditional pip?** See [installation options](#installation-options) below.

---

## 💬 Usage

```bash
# Run the application
uv run python main.py

# Test it works
uv run python test_basic.py

# Re-index after changing knowledge base
rm -rf chroma_db/ && uv run python main.py
```

### Example Questions

Try these with the included sample knowledge base:
- "What features are planned for Q1 2024?"
- "What are the API rate limits?"
- "Who is responsible for the Advanced Search feature?"

### Example Output

```
ANSWER:
Three main features are planned for Q1 2024:
1. Advanced Search - launching March 2024
2. API Rate Limiting - February 2024
3. Bulk Export Feature - February 2024

Confidence: HIGH

SOURCES:
[1] Relevance: 0.89 - "Product Roadmap Planning Meeting..."
[2] Relevance: 0.82 - "Customer Feedback Review..."
```

---

## 📁 Project Structure

```
Agentic-second-brain/
├── data/
│   └── knowledge_base.md      # Your knowledge base content
├── src/
│   ├── __init__.py
│   ├── embeddings.py          # Embedding generation and text chunking
│   ├── vector_store.py        # ChromaDB vector store management
│   ├── retrieval_tool.py      # RAG retrieval functionality
│   ├── models.py              # Pydantic models for structured outputs
│   ├── agent.py               # Pydantic AI agent definition
│   └── indexer.py             # Knowledge base indexing utilities
├── main.py                    # Main entry point
├── requirements.txt           # Python dependencies
├── .env                       # Your API key (not in git)
└── chroma_db/                 # Vector database storage (auto-created)
```

---

## Customization

### Add Your Own Content
1. Edit `data/knowledge_base.md` with your content
2. Delete `chroma_db/` directory
3. Run `uv run python main.py` (auto re-indexes)

### Adjust Settings

| What to Change | File | Line | Example |
|---------------|------|------|---------|
| Retrieved docs (top-k) | `src/agent.py` | 40 | `top_k=3` → `top_k=5` |
| Chunk size | `src/indexer.py` | 13 | `chunk_size=500` |
| LLM model | `src/agent.py` | 35 | Try `claude-3.5-haiku` for lower cost |
| Embedding model | `src/embeddings.py` | 11 | Try `all-mpnet-base-v2` |

---

## Setting up 

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install deps & run
uv sync
uv run python main.py
```

