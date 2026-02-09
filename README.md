# Second Brain - Personal Knowledge System

A single-agent RAG (Retrieval-Augmented Generation) system built with Pydantic AI that serves as your personal knowledge base. Features persistent memory, PII protection, Notion integration via MCP, a Streamlit chat UI, and a pydantic-evals evaluation suite.

## Features

- **RAG Retrieval**: Vector-based search using ChromaDB and sentence transformers
- **Persistent Memory**: SQLite-backed storage for conversations, preferences, and facts
- **Notion Integration**: MCP server for searching, reading, creating, and archiving Notion pages
- **PII Guardrails**: Automatic detection and redaction of sensitive information
- **Streamlit Chat UI**: Web-based demo interface for interactive conversations
- **Structured Logging**: Loguru-based JSON logs and console output
- **Evaluation Suite**: pydantic-evals test cases for measuring RAG effectiveness

---

## Quick Start

```bash
# 1. Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# 2. Set up API keys
cp .env.example .env
# Edit .env:
#   ANTHROPIC_API_KEY=your_key_here
#   NOTION_API_TOKEN=your_notion_token_here

# 3. Run (CLI)
uv run python main.py

# 3. Or run (Streamlit UI)
uv run streamlit run app.py
```

---

## Usage

### CLI Commands

```bash
# Interactive chat (default)
uv run python main.py

# Streamlit web UI
uv run streamlit run app.py

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

While in CLI interactive mode:
- `help` - Show example questions
- `memory` - View recent stored memories
- `quit` or `exit` - Exit the application

### Example Questions

```
What features are planned for Q1 2024?
What are the API rate limits?
Search my Notion pages for meeting notes
Create a new Notion page with today's summary
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
│   ├── agent.py               # RAG agent with tools + MCP integration
│   ├── mcp_notion.py          # Notion MCP server (FastMCP)
│   ├── config.py              # Pydantic Settings configuration
│   ├── models.py              # Pydantic response/memory models
│   ├── memory.py              # SQLite memory system
│   ├── guardrails.py          # PII detection and redaction
│   ├── observability.py       # Loguru structured logging
│   ├── evals.py               # pydantic-evals evaluation suite
│   └── rag/
│       ├── __init__.py
│       ├── embeddings.py      # Sentence transformer model
│       ├── chunking.py        # Text chunking logic
│       ├── vector_store.py    # ChromaDB vector store
│       ├── indexer.py         # Document indexing pipeline
│       └── retriever.py       # Query retrieval and formatting
├── app.py                     # Streamlit chat UI
├── main.py                    # CLI entry point
├── logs/
│   └── app.log                # Structured JSON logs
├── pyproject.toml
├── ARCHITECTURE.md
└── README.md
```

---

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system architecture diagram and data flow details.

### Agent Tools

The agent has access to **inline tools** and **MCP tools**:

**Inline tools** (registered directly on the agent):
1. **retrieve_context** - Search the knowledge base using vector similarity
2. **save_memory** - Store conversation summaries, preferences, or facts
3. **recall_memory** - Retrieve relevant past conversations/preferences
4. **summarize** - Summarize long text or multiple retrieved chunks

**Notion MCP tools** (served via FastMCP over stdio):
1. **search_pages** - Search Notion workspace for pages by keyword
2. **get_page_content** - Read the text content of a Notion page
3. **create_page** - Create a new child page under a parent page
4. **archive_page** - Soft-delete (archive) a Notion page

### Notion MCP Server

The Notion integration uses the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). A FastMCP server (`src/mcp_notion.py`) exposes Notion API operations as tools. The Pydantic AI agent connects to it via `MCPServerStdio`, making Notion tools automatically available alongside the inline RAG tools.

Requires a `NOTION_API_TOKEN` in `.env` (create an [internal integration](https://www.notion.so/my-integrations) and share pages with it).

### Streamlit UI

`app.py` provides a web-based chat interface:
- Chat input with message history
- Source snippets shown in expandable sections
- Confidence level display
- Sidebar with tool descriptions

### Memory System

SQLite-backed storage with three memory types:
- `conversation` - Summaries of past conversations
- `preference` - User preferences and settings
- `fact` - Important facts to remember

### PII Guardrails

Automatic detection and redaction before storing:
- Email addresses -> `[EMAIL]`
- Phone numbers -> `[PHONE]`
- Social Security Numbers -> `[SSN]`
- Credit card numbers -> `[CARD]`

### Observability

- **Logging**: Structured JSON logs to `logs/app.log` via Loguru
- **Console**: Readable colored output to stderr

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

The evaluation suite uses [pydantic-evals](https://ai.pydantic.dev/evals/) with custom evaluators:

- **TopicCoverage** - Checks if expected keywords appear in the agent's answer
- **ConfidenceCheck** - Validates the confidence level matches expectations

Test categories:
- **Retrieval** (5 cases) - Can the agent find specific information?
- **Synthesis** (3 cases) - Can it combine multiple sources?
- **Edge cases** (2 cases) - How does it handle unknown topics?

Run evaluations:
```bash
uv run python main.py --eval
```

Results are printed as a formatted table via pydantic-evals reporting.

---

## Configuration

### Environment Variables

```bash
ANTHROPIC_API_KEY=your_api_key_here
NOTION_API_TOKEN=your_notion_token_here
```

### Settings (`src/config.py`)

All settings are configurable via environment variables or `.env`:

| Setting | Default | Description |
|---------|---------|-------------|
| `embedding_model` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `chunk_size` | `500` | Text chunk size for indexing |
| `chunk_overlap` | `50` | Overlap between chunks |
| `chroma_persist_dir` | `./chroma_db` | ChromaDB storage path |
| `collection_name` | `knowledge_base` | ChromaDB collection name |
| `memory_db_path` | `data/memory.db` | SQLite memory database path |
| `llm_model` | `anthropic:claude-sonnet-4-5` | LLM model for the agent |
| `retrieval_top_k` | `3` | Number of documents to retrieve |
| `notion_api_token` | `""` | Notion integration token |
| `log_file` | `logs/app.log` | Log file path |
| `log_level` | `INFO` | Logging level |

---

## Dependencies

Core:
- `pydantic-ai` - Agent framework
- `chromadb` - Vector database
- `sentence-transformers` - Embeddings
- `anthropic` - Claude API
- `aiosqlite` - Async SQLite for memory
- `loguru` - Structured logging
- `pydantic-evals` - Evaluation framework
- `fastmcp` - MCP server framework
- `httpx` - Async HTTP client (Notion API)
- `streamlit` - Web chat UI

---

## Development

```bash
# Install dependencies
uv sync

# Format code
uv run ruff format .

# Lint
uv run ruff check .

# Run evals
uv run python main.py --eval
```
