# System Architecture

## Overview

The Personal Knowledge Retriever implements a RAG (Retrieval-Augmented Generation) pattern using Pydantic AI and ChromaDB.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                         │
│                          (main.py)                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PYDANTIC AI AGENT                          │
│                       (src/agent.py)                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  System Prompt: "Answer questions using context..."        │ │
│  │  Result Type: AgentResponse (structured)                   │ │
│  │  Tools: [retrieve_context]                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└────────────────┬────────────────────────▲───────────────────────┘
                 │                        │
        1. Query │                        │ 4. Answer + Sources
                 ▼                        │
┌─────────────────────────────────────────┐
│      RETRIEVAL TOOL                     │
│   (src/retrieval_tool.py)               │
│  ┌───────────────────────────────────┐  │
│  │ 1. Generate query embedding       │  │
│  │ 2. Search vector store            │  │
│  │ 3. Format results                 │  │
│  └───────────────────────────────────┘  │
└──────────┬──────────────────────────────┘
           │
           │ 2. Search
           ▼
┌─────────────────────────────────────────┐
│       VECTOR STORE                      │
│     (src/vector_store.py)               │
│  ┌───────────────────────────────────┐  │
│  │  ChromaDB Collection              │  │
│  │  - Document chunks                │  │
│  │  - Embeddings (384-dim)           │  │
│  │  - Metadata                       │  │
│  └───────────────────────────────────┘  │
└──────────┬──────────────────────────────┘
           │
           │ 3. Top-K Results
           ▼
┌─────────────────────────────────────────┐
│     EMBEDDING MODEL                     │
│    (src/embeddings.py)                  │
│  ┌───────────────────────────────────┐  │
│  │  Sentence Transformer             │  │
│  │  Model: all-MiniLM-L6-v2          │  │
│  │  Dimension: 384                   │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
       ▲
       │ Indexed during startup
       │
┌─────────────────────────────────────────┐
│     KNOWLEDGE BASE INDEXER              │
│      (src/indexer.py)                   │
│  ┌───────────────────────────────────┐  │
│  │ 1. Read knowledge_base.md         │  │
│  │ 2. Chunk text (500 chars)         │  │
│  │ 3. Generate embeddings            │  │
│  │ 4. Store in ChromaDB              │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## Data Flow

### Indexing Phase (Startup)

1. **Read Knowledge Base** - Load markdown file
2. **Chunk Text** - Split into 500-char chunks with 50-char overlap
3. **Generate Embeddings** - Create 384-dimensional vectors
4. **Store in Vector DB** - ChromaDB persistent storage

### Query Phase (Runtime)

1. **User Asks Question** - Natural language input
2. **Agent Processes Request** - Calls retrieve_context tool
3. **Retrieve Context** - Search ChromaDB for top-3 similar chunks
4. **Generate Response** - Claude creates answer with sources
5. **Display Results** - Show answer, sources, confidence

## Component Details

### Pydantic AI Agent (`src/agent.py`)
- Orchestrates RAG process
- System prompt guides behavior
- Structured output validation

### Retrieval Tool (`src/retrieval_tool.py`)
- Bridges agent and vector store
- Embeds queries and searches ChromaDB
- Formats results for LLM consumption

### Vector Store (`src/vector_store.py`)
- ChromaDB operations wrapper
- Filesystem persistence in `./chroma_db/`
- Add, query, count operations

### Embedding Model (`src/embeddings.py`)
- Sentence Transformer (all-MiniLM-L6-v2)
- Local processing, no API calls
- Text chunking with overlap

### Structured Models (`src/models.py`)
- `AgentResponse`: answer + sources + confidence
- `SourceSnippet`: text + relevance_score + metadata

