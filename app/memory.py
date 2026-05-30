"""
Memory layer: SQLite for raw storage, ChromaDB for semantic search.
"""
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions
from loguru import logger

from app.config import DB_FILE, CHROMA_PATH


# ── ChromaDB setup ────────────────────────────────────────────────────────────

_chroma_client: Optional[chromadb.PersistentClient] = None
_collection_entries = None
_collection_synthetic = None
_embed_fn = None


def _get_embed_fn():
    global _embed_fn
    if _embed_fn is None:
        _embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    return _embed_fn


def get_chroma():
    global _chroma_client, _collection_entries, _collection_synthetic
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection_entries = _chroma_client.get_or_create_collection(
            name="entries",
            embedding_function=_get_embed_fn(),
            metadata={"hnsw:space": "cosine"},
        )
        _collection_synthetic = _chroma_client.get_or_create_collection(
            name="synthetic",
            embedding_function=_get_embed_fn(),
            metadata={"hnsw:space": "cosine"},
        )
    return _chroma_client, _collection_entries, _collection_synthetic


# ── SQLite helpers ────────────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# ── Core write ────────────────────────────────────────────────────────────────

def save_entry(
    raw_text: str,
    pillar: str,
    summary: str = "",
    entities: list = None,
    sentiment: str = "neutral",
    importance: int = 5,
    source: str = "text",
) -> int:
    """Save a new entry to SQLite + ChromaDB. Returns the SQLite row id."""
    chroma_id = str(uuid.uuid4())
    entities_json = json.dumps(entities or [])

    # 1. SQLite
    conn = get_db()
    cur = conn.execute(
        """
        INSERT INTO entries (pillar, raw_text, summary, entities, sentiment, importance, source, chroma_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (pillar, raw_text, summary, entities_json, sentiment, importance, source, chroma_id),
    )
    entry_id = cur.lastrowid
    conn.commit()
    conn.close()

    # 2. ChromaDB — embed the summary (richer) if available, else raw
    _, col_entries, _ = get_chroma()
    embed_text = summary if summary else raw_text
    col_entries.add(
        ids=[chroma_id],
        documents=[embed_text],
        metadatas=[{
            "entry_id": entry_id,
            "pillar": pillar,
            "importance": importance,
            "created_at": datetime.utcnow().isoformat(),
        }],
    )

    logger.info(f"Saved entry #{entry_id} pillar={pillar} importance={importance}")
    return entry_id


def save_synthetic_memory(insight: str, pillars: list, importance: int = 7) -> int:
    chroma_id = str(uuid.uuid4())
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO synthetic_memories (insight, pillars, importance, chroma_id) VALUES (?,?,?,?)",
        (insight, ",".join(pillars), importance, chroma_id),
    )
    mem_id = cur.lastrowid
    conn.commit()
    conn.close()

    _, _, col_syn = get_chroma()
    col_syn.add(
        ids=[chroma_id],
        documents=[insight],
        metadatas=[{"pillars": ",".join(pillars), "importance": importance}],
    )
    return mem_id


# ── Core read ─────────────────────────────────────────────────────────────────

def semantic_search(
    query: str,
    pillar: Optional[str] = None,
    n_results: int = 8,
) -> list[dict]:
    """
    Search ChromaDB for relevant entries, then hydrate from SQLite.
    Returns list of dicts with full entry data.
    """
    _, col_entries, col_syn = get_chroma()

    where = {"pillar": pillar} if pillar else None

    try:
        results = col_entries.query(
            query_texts=[query],
            n_results=min(n_results, col_entries.count() or 1),
            where=where,
        )
    except Exception as e:
        logger.warning(f"ChromaDB query error: {e}")
        return []

    ids = results["ids"][0] if results["ids"] else []
    if not ids:
        return []

    # Also pull synthetic memories
    try:
        syn_results = col_syn.query(
            query_texts=[query],
            n_results=min(3, col_syn.count() or 1),
        )
        syn_docs = syn_results["documents"][0] if syn_results["documents"] else []
    except Exception:
        syn_docs = []

    # Hydrate entries from SQLite
    conn = get_db()
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT * FROM entries WHERE chroma_id IN ({placeholders})",
        ids,
    ).fetchall()
    conn.close()

    entries = []
    for row in rows:
        entries.append({
            "id": row["id"],
            "pillar": row["pillar"],
            "raw_text": row["raw_text"],
            "summary": row["summary"],
            "entities": json.loads(row["entities"] or "[]"),
            "importance": row["importance"],
            "sentiment": row["sentiment"],
            "created_at": row["created_at"],
            "source": row["source"],
        })

    # Append synthetic memories as context
    for doc in syn_docs:
        entries.append({
            "id": None,
            "pillar": "synthetic",
            "raw_text": doc,
            "summary": doc,
            "entities": [],
            "importance": 7,
            "sentiment": "neutral",
            "created_at": "",
            "source": "muse",
        })

    return entries


def get_recent_entries(pillar: Optional[str] = None, limit: int = 20) -> list[dict]:
    conn = get_db()
    if pillar:
        rows = conn.execute(
            "SELECT * FROM entries WHERE pillar=? ORDER BY created_at DESC LIMIT ?",
            (pillar, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM entries ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    conn = get_db()
    rows = conn.execute(
        "SELECT pillar, COUNT(*) as cnt FROM entries GROUP BY pillar"
    ).fetchall()
    conn.close()
    return {r["pillar"]: r["cnt"] for r in rows}
