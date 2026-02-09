# System Architecture

## Overview

A RAG system where a Pydantic AI agent orchestrates retrieval from a vector store, manages persistent memory, ensures PII safety, and integrates with Notion via MCP. Two interfaces are available: a CLI and a Streamlit web UI.

## High-Level Architecture

```
┌──────────────┐     ┌──────────────┐
│     CLI      │     │  Streamlit   │
│  (main.py)   │     │  (app.py)    │
└──────┬───────┘     └──────┬───────┘
       │                    │
       └────────┬───────────┘
                ▼
┌──────────────────────────────────────────────────┐
│              PYDANTIC AI AGENT                   │  src/agent.py
│  ┌──────────────────────────────────────────┐    │
│  │ Inline: retrieve_context, save_memory,   │    │
│  │         recall_memory, summarize         │    │
│  │                                          │    │
│  │ MCP:    search_pages, get_page_content,  │    │
│  │         create_page, archive_page        │    │
│  └──────────────────────────────────────────┘    │
└───┬────────┬────────┬────────┬──────────┬────────┘
    │        │        │        │          │
    ▼        ▼        ▼        ▼          ▼
┌───────┐┌───────┐┌───────┐┌───────┐┌─────────────┐
│  RAG  ││MEMORY ││  PII  ││ LOGS  ││ NOTION MCP  │
│       ││ STORE ││GUARD- ││       ││  SERVER     │
│       ││       ││ RAIL  ││       ││(src/mcp_    │
│       ││       ││       ││       ││ notion.py)  │
└───┬───┘└───┬───┘└───────┘└───────┘└──────┬──────┘
    │        │                             │
    ▼        ▼                             ▼
 ChromaDB  SQLite                      Notion API

┌──────────────────────────────────────────────────┐
│         EVALUATION (pydantic-evals)              │  src/evals.py
│  Runs agent through test cases                   │
└──────────────────────────────────────────────────┘
```

## Module Interactions

### 1. Query Flow (User Question -> Answer)

```
User Input (CLI or Streamlit)
    ↓
RAGAgent.ask(question)
    ↓
async with agent:         ← opens MCP server connection
    agent.run(question)   ← agent decides which tools to call
    ↓
Agent may call any combination of:
  retrieve_context() → Retriever → ChromaDB
  recall_memory()    → MemoryStore → SQLite
  search_pages()     → MCP → Notion API
  get_page_content() → MCP → Notion API
    ↓
Agent (Claude) generates AgentResponse
    ↓
Response returned to caller (CLI prints, Streamlit renders)
```

### 2. Memory Flow (Save & Recall)

```
Agent calls save_memory tool
    ↓
save_memory() → redact_pii() → strips [EMAIL], [PHONE], etc.
    ↓
MemoryStore.save_memory() → SQLite insert

Agent calls recall_memory tool
    ↓
MemoryStore.search_memory() or get_recent_memories()
    ↓
Formatted memories returned to agent
```

### 3. Notion Flow (via MCP)

```
Agent calls a Notion MCP tool (e.g. search_pages)
    ↓
Pydantic AI sends tool call over stdio to FastMCP server
    ↓
FastMCP server (src/mcp_notion.py) handles the call
    ↓
httpx async request to Notion API (api.notion.com)
    ↓
Response parsed and returned to agent via MCP protocol
```

### 4. Indexing Flow (Data -> Vector Store)

```
main.py --ingest
    ↓
KnowledgeBaseIndexer scans data/ directory
    ↓
For each file: TextChunker.chunk()
    ↓
For each chunk: EmbeddingModel.embed()
    ↓
VectorStore.add() → ChromaDB persisted to ./chroma_db/
```

### 5. Evaluation Flow

```
main.py --eval
    ↓
pydantic-evals Dataset.evaluate(task_fn)
    ↓
For each Case: task_fn(question) → agent.ask()
    ↓
TopicCoverage & ConfidenceCheck evaluate response
    ↓
Report.print() shows pass/fail with reasons
```

## Key Module Responsibilities

### Agent (`src/agent.py`)
- **Owns**: Tool orchestration, system prompt, MCP server lifecycle
- **Calls**: Retriever, MemoryStore, guardrails, MCP servers
- **Returns**: Structured `AgentResponse` (answer + sources + confidence)

### Notion MCP Server (`src/mcp_notion.py`)
- **Owns**: FastMCP server, Notion API HTTP calls
- **Interactions**:
  - Agent connects via `MCPServerStdio` (stdio transport)
  - Tools auto-discovered by Pydantic AI at connection time
  - Uses `NOTION_API_TOKEN` from environment for auth

### RAG Pipeline (`src/rag/`)
- **Owns**: Embedding generation, vector storage, retrieval
- **Interactions**:
  - `retriever.py` coordinates embedding + querying
  - `indexer.py` reads files, chunks, embeds, stores
  - `vector_store.py` wraps ChromaDB

### Memory Store (`src/memory.py`)
- **Owns**: SQLite database, CRUD operations
- **Interactions**:
  - Agent calls via `save_memory` / `recall_memory` tools
  - Receives pre-redacted content from guardrails

### Streamlit UI (`app.py`)
- **Owns**: Web chat interface, session state
- **Interactions**:
  - Initializes same system as `main.py` (cached via `@st.cache_resource`)
  - Calls `RAGAgent.ask()` per user message
  - Renders answer, sources, and confidence

### Guardrails (`src/guardrails.py`)
- **Owns**: PII regex patterns, `redact_pii()`, `contains_pii()`
- **Called by**: `save_memory` tool before storage

### Observability (`src/observability.py`)
- **Owns**: Loguru logger setup
- **Imported as**: `log` across all modules

### Evaluation (`src/evals.py`)
- **Owns**: Test dataset, custom evaluators
- **Interactions**: Initializes full system, runs through pydantic-evals

## Data Dependencies

```
┌─────────────┐     ┌─────────────┐
│  data/      │────▶│ ./chroma_db/│
│  *.md, *.txt│     │  (vectors)  │
└─────────────┘     └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │   Retriever │
                    └─────────────┘

┌─────────────┐
│ data/       │
│ memory.db   │◀──── MemoryStore
└─────────────┘

┌─────────────┐
│ Notion API  │◀──── MCP Server (via NOTION_API_TOKEN)
└─────────────┘

┌─────────────┐
│ logs/       │
│ app.log     │◀──── Observability
└─────────────┘
```

## Configuration

All modules read from `src/config.py` (Pydantic Settings):
- Agent gets `llm_model`, `retrieval_top_k`, `use_memory`
- RAG pipeline gets `embedding_model`, `chunk_size`, `chunk_overlap`, `chroma_persist_dir`
- Memory gets `memory_db_path`
- Notion gets `notion_api_token`
- Observability gets `log_file`, `log_level`

Configuration is centralized and loaded once at startup.
