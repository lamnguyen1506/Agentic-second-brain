"""SQLite-backed memory system for storing conversation history and preferences."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.config import get_settings
from src.models import MemoryEntry


class MemoryStore:
    """SQLite-backed memory storage for conversations, preferences, and facts."""

    def __init__(self, db_path: str | None = None):
        """Initialize the memory store.

        Args:
            db_path: Path to the SQLite database file.
                    Defaults to settings.memory_db_path.
        """
        settings = get_settings()
        self.db_path = db_path or settings.memory_db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('conversation', 'preference', 'fact')),
                    content TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp DESC)
            """)
            conn.commit()

    def save_memory(
        self,
        content: str,
        memory_type: str = "conversation",
        metadata: dict | None = None,
        memory_id: str | None = None,
    ) -> MemoryEntry:
        """Save a memory entry to the database.

        Args:
            content: The memory content (already PII-redacted)
            memory_type: Type of memory (conversation, preference, fact)
            metadata: Optional metadata dictionary
            memory_id: Optional custom ID (auto-generated if not provided)

        Returns:
            The created MemoryEntry
        """
        if memory_type not in ("conversation", "preference", "fact"):
            raise ValueError(f"Invalid memory type: {memory_type}")

        entry = MemoryEntry(
            id=memory_id or str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            type=memory_type,
            content=content,
            metadata=metadata or {},
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO memories (id, timestamp, type, content, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    entry.id,
                    entry.timestamp.isoformat(),
                    entry.type,
                    entry.content,
                    json.dumps(entry.metadata),
                ),
            )
            conn.commit()

        return entry

    def search_memory(
        self,
        query: str,
        memory_type: str | None = None,
        limit: int = 5,
    ) -> list[MemoryEntry]:
        """Search memories by content (simple substring match).

        Args:
            query: Search query string
            memory_type: Optional filter by memory type
            limit: Maximum number of results

        Returns:
            List of matching MemoryEntry objects
        """
        with sqlite3.connect(self.db_path) as conn:
            if memory_type:
                cursor = conn.execute(
                    """
                    SELECT id, timestamp, type, content, metadata
                    FROM memories
                    WHERE content LIKE ? AND type = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (f"%{query}%", memory_type, limit),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT id, timestamp, type, content, metadata
                    FROM memories
                    WHERE content LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (f"%{query}%", limit),
                )

            return [self._row_to_entry(row) for row in cursor.fetchall()]

    def get_recent_memories(
        self,
        limit: int = 10,
        memory_type: str | None = None,
    ) -> list[MemoryEntry]:
        """Get the most recent memories.

        Args:
            limit: Maximum number of memories to return
            memory_type: Optional filter by memory type

        Returns:
            List of MemoryEntry objects, most recent first
        """
        with sqlite3.connect(self.db_path) as conn:
            if memory_type:
                cursor = conn.execute(
                    """
                    SELECT id, timestamp, type, content, metadata
                    FROM memories
                    WHERE type = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (memory_type, limit),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT id, timestamp, type, content, metadata
                    FROM memories
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            return [self._row_to_entry(row) for row in cursor.fetchall()]

    def get_memory_by_id(self, memory_id: str) -> MemoryEntry | None:
        """Get a specific memory by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, timestamp, type, content, metadata
                FROM memories
                WHERE id = ?
                """,
                (memory_id,),
            )
            row = cursor.fetchone()
            return self._row_to_entry(row) if row else None

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM memories WHERE id = ?",
                (memory_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def clear_all(self) -> int:
        """Clear all memories from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM memories")
            count = cursor.rowcount
            conn.commit()
            return count

    def count(self, memory_type: str | None = None) -> int:
        """Count memories in the database."""
        with sqlite3.connect(self.db_path) as conn:
            if memory_type:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM memories WHERE type = ?",
                    (memory_type,),
                )
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM memories")
            return cursor.fetchone()[0]

    def _row_to_entry(self, row: tuple) -> MemoryEntry:
        """Convert a database row to a MemoryEntry."""
        return MemoryEntry(
            id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            type=row[2],
            content=row[3],
            metadata=json.loads(row[4]) if row[4] else {},
        )
