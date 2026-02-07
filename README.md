# Second Brain - Personal Knowledge System

A single-agent RAG (Retrieval-Augmented Generation) system built with Pydantic AI that serves as your personal knowledge base. Features persistent memory, PII protection, OpenTelemetry observability, and evaluation-driven development.

## Features

- **RAG Retrieval**: Vector-based search using ChromaDB and sentence transformers
- **Persistent Memory**: SQLite-backed storage for conversations, preferences, and facts
- **PII Guardrails**: Automatic detection and redaction of sensitive information
- **OTEL Observability**: Tracing, structured logging, and performance metrics
- **Evaluation Suite**: Test cases for measuring RAG and memory effectiveness

---

## Quick Start

```bash
# 1. Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# 2. Set up API key
cp .env.example .env
# Edit .env: ANTHROPIC_API_KEY=your_key_here

# 3. Run
uv run python main.py
```

---

## Usage

### CLI Commands

```bash
# Interactive chat (default)
uv run python main.py

# Re-index knowledge base from data/ directory
uv run python main.py --ingest

# Run evaluation suite
uv run python main.py --eval

# Clear all stored memories
uv run python main.py --clear-memory

# Run without memory system
uv run python main.py --no-memory
```

### Interactive Commands

While in interactive mode:
- `help` - Show example questions
- `memory` - View recent stored memories
- `metrics` - View performance metrics
- `quit` or `exit` - Exit the application

### Example Questions

```
What features are planned for Q1 2024?
What are the API rate limits?
Who is responsible for the Advanced Search feature?
What are the top customer requests?
```

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

## Project Structure

```
Agentic-second-brain/
├── data/
│   ├── knowledge_base.md      # Your knowledge content
│   ├── transcripts/           # Meeting transcripts
│   └── memory.db              # SQLite memory (auto-created)
├── src/
│   ├── __init__.py
│   ├── agent.py               # RAG agent with all tools
│   ├── embeddings.py          # Embedding model and text chunking
│   ├── vector_store.py        # ChromaDB vector store
│   ├── indexer.py             # Document indexing
│   ├── retrieval_tool.py      # RAG retrieval functionality
│   ├── models.py              # Pydantic models
│   ├── memory.py              # SQLite memory system
│   ├── guardrails.py          # PII detection and redaction
│   ├── observability.py       # OTEL tracing and logging
│   └── evals.py               # Evaluation suite
├── logs/
│   └── app.log                # Structured JSON logs
├── results/
│   └── eval_results.json      # Evaluation results
├── main.py                    # CLI entry point
├── pyproject.toml
└── README.md
```

---

## Architecture

### Agent Tools

The RAG agent has access to four tools:

1. **retrieve_context** - Search the knowledge base using vector similarity
2. **save_memory** - Store conversation summaries, preferences, or facts
3. **recall_memory** - Retrieve relevant past conversations/preferences
4. **summarize** - Summarize long text or multiple retrieved chunks

### Memory System

SQLite-backed storage with three memory types:
- `conversation` - Summaries of past conversations
- `preference` - User preferences and settings
- `fact` - Important facts to remember

### PII Guardrails

Automatic detection and redaction before storing:
- Email addresses → `[EMAIL]`
- Phone numbers → `[PHONE]`
- Social Security Numbers → `[SSN]`
- Credit card numbers → `[CARD]`

### Observability

- **Tracing**: OpenTelemetry spans for all operations
- **Logging**: Structured JSON logs to `logs/app.log`
- **Metrics**: Query latency, retrieval scores, memory operations

---

## Data Ingestion

The system supports ingesting from the `data/` directory:
- Markdown files (`.md`)
- Text files (`.txt`)
- Meeting transcripts (in `data/transcripts/`)

To add new content:
1. Add files to `data/` directory
2. Run `uv run python main.py --ingest`

---

## Evaluation

The evaluation suite tests:
- **Retrieval**: Can the agent find relevant information?
- **Synthesis**: Can it combine multiple sources?
- **Memory**: Does memory improve responses?
- **Edge cases**: How does it handle unknown topics?

Run evaluations:
```bash
uv run python main.py --eval
# Or directly:
uv run python -m src.evals
```

Results are saved to `results/eval_results.json`.

---

## Configuration

### Environment Variables

```bash
ANTHROPIC_API_KEY=your_api_key_here
```

### Customization

| Setting | File | Description |
|---------|------|-------------|
| Top-k results | `src/agent.py:66` | Number of documents to retrieve |
| Chunk size | `src/indexer.py:20` | Text chunk size for indexing |
| LLM model | `src/agent.py:254` | Change to different Claude model |
| Embedding model | `src/embeddings.py:11` | Sentence transformer model |

---

## Dependencies

Core:
- `pydantic-ai` - Agent framework
- `chromadb` - Vector database
- `sentence-transformers` - Embeddings
- `anthropic` - Claude API

New additions:
- `aiosqlite` - Async SQLite for memory
- `loguru` - Structured logging
- `opentelemetry-api/sdk` - Tracing

---

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Format code
uv run ruff format .

# Lint
uv run ruff check .
```

---

## License

MIT
