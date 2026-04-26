"""Persistent memory tool backed by ChromaDB vector store."""

import os
from datetime import datetime
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./memory/chroma_db")
_client: chromadb.PersistentClient | None = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        Path(_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=_PERSIST_DIR)
        ef = embedding_functions.DefaultEmbeddingFunction()
        _collection = _client.get_or_create_collection(
            name="memories", embedding_function=ef
        )
    return _collection


async def remember(content: str, key: str | None = None) -> str:
    col = _get_collection()
    doc_id = key or f"mem_{datetime.utcnow().isoformat()}"
    col.upsert(
        documents=[content],
        ids=[doc_id],
        metadatas=[{"timestamp": datetime.utcnow().isoformat(), "key": key or ""}],
    )
    return f"Memory stored with id: {doc_id}"


async def recall(query: str, top_k: int = 5) -> str:
    col = _get_collection()
    results = col.query(query_texts=[query], n_results=min(top_k, col.count()))
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    if not docs:
        return "No relevant memories found."
    lines = []
    for doc, meta in zip(docs, metas):
        ts = meta.get("timestamp", "")
        lines.append(f"[{ts}] {doc}")
    return "\n---\n".join(lines)
