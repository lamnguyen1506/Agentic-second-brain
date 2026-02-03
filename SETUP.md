# Setup Instructions

## Prerequisites
- Python 3.11 or higher (for best performance)
- Anthropic API key (get one at https://console.anthropic.com/)
- uv package manager (recommended) or pip

**Why Python 3.11?** 10-60% faster execution, better error messages, and improved performance for AI workloads.

## Installation Steps

### Option 1: Using uv (Recommended - Fast!)

#### 1. Install uv

**On macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**On Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Or using pip:**
```bash
pip install uv
```

#### 2. Navigate to the repository
```bash
cd Agentic-second-brain
```

#### 3. Install dependencies
```bash
uv sync
```

That's it! uv automatically:
- Creates a virtual environment (`.venv/`)
- Installs all dependencies from `pyproject.toml`
- Locks dependencies in `uv.lock`

**Note:** First-time installation downloads the embedding model (~80MB). With uv, this is 10-100x faster than pip!

### Option 2: Using Traditional pip/venv

#### 1. Navigate to the repository
```bash
cd Agentic-second-brain
```

#### 2. Create a virtual environment
```bash
python -m venv venv
```

#### 3. Activate the virtual environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

#### 4. Install dependencies
```bash
pip install -r requirements.txt
```

This will install:
- `pydantic-ai` - The Pydantic AI framework
- `chromadb` - Vector database
- `sentence-transformers` - For generating embeddings
- `anthropic` - Anthropic API client
- `python-dotenv` - For environment variable management

**Note:** First-time installation may take a few minutes as it downloads the embedding model (all-MiniLM-L6-v2).

### 5. Set up your API key

Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

**Or** export it in your shell:
```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

### 6. Run the application

**With uv:**
```bash
uv run python main.py
```

**With traditional venv (make sure it's activated):**
```bash
python main.py
```

On first run, the system will:
1. Load the embedding model (all-MiniLM-L6-v2)
2. Index the knowledge base from `data/knowledge_base.md`
3. Store embeddings in `chroma_db/` directory
4. Launch interactive mode

## Usage

### Interactive Mode
```bash
uv run python main.py
```
Then select option `1` for interactive mode.

Ask questions like:
- "What features are planned for Q1 2024?"
- "What are the API rate limits?"
- "Who is responsible for the Advanced Search feature?"

### Demo Mode
```bash
uv run python main.py
```
Then select option `2` for demo mode with pre-defined questions.

## Project Structure

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

## Customization

### Add Your Own Knowledge Base

1. Edit `data/knowledge_base.md` with your own content
2. Delete the `chroma_db/` directory to force re-indexing
3. Run `uv run python main.py` again

### Adjust Chunking Parameters

Edit `src/indexer.py`:
```python
self.chunker = TextChunker(chunk_size=500, overlap=50)
```

### Change Number of Retrieved Documents

Edit `src/agent.py`:
```python
results = ctx.deps.retrieval_tool.retrieve(query, top_k=3)  # Change top_k
```

### Use Different Embedding Model

Edit `src/embeddings.py`:
```python
def __init__(self, model_name: str = "all-MiniLM-L6-v2"):  # Change model name
```
