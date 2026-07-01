"""
rag/vector_store.py
===================
WHY THIS FILE EXISTS:
    After we chunk and embed text, we need somewhere to store those vectors so
    we can search them later. ChromaDB is a free, local vector database. This
    file wraps it in a few simple functions so the rest of the app never has
    to touch Chroma directly.

WHAT IT DOES:
    - Creates/opens a persistent Chroma collection.
    - add_chunks(): embed chunks and store them with metadata.
    - query(): embed a question and return the closest chunks.
    - get_all() / stats() / reset(): support the Monitoring tab and cleanup.

HOW IT CONNECTS:
    - The extraction agent calls add_chunks() after processing a PDF.
    - rag/retrieval.py calls query() / get_all() to fetch context.
    - config/settings.CHROMA_DIR decides where data is persisted.
"""

import uuid
from utils.logger import log
from rag.embedding import embed_texts, embed_query
from config import settings


class VectorStore:
    """Thin wrapper around a single ChromaDB collection."""

    def __init__(self, embedding_model: str):
        import chromadb

        self.embedding_model = embedding_model
        # PersistentClient writes to disk so data survives between reruns.
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
        # We manage embeddings ourselves, so no embedding_function is passed.
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )

    # -- WRITE ---------------------------------------------------------------
    def add_chunks(self, chunks: list[str], base_metadata: dict):
        """
        Embed and store a list of text chunks. `base_metadata` should include
        at least 'filename' and 'page'. A unique chunk_id is added per chunk.
        """
        if not chunks:
            return 0
        vectors = embed_texts(chunks, self.embedding_model)
        ids, metadatas = [], []
        for i, _ in enumerate(chunks):
            cid = str(uuid.uuid4())[:8]
            ids.append(cid)
            meta = dict(base_metadata)
            meta["chunk_id"] = cid
            metadatas.append(meta)
        self.collection.add(
            ids=ids,
            documents=chunks,
            embeddings=vectors,
            metadatas=metadatas,
        )
        log(f"Stored {len(chunks)} chunks from {base_metadata.get('filename')}")
        return len(chunks)

    # -- READ ----------------------------------------------------------------
    def query(self, question: str, top_k: int, filenames: list[str] | None = None):
        """
        Return the `top_k` most similar chunks to the question.
        Optionally restrict to specific filenames.
        Output: list of {"text", "metadata", "distance"}.
        """
        if self.count() == 0:
            return []
        qvec = embed_query(question, self.embedding_model)
        where = None
        if filenames:
            where = {"filename": {"$in": filenames}}
        res = self.collection.query(
            query_embeddings=[qvec],
            n_results=min(top_k, self.count()),
            where=where,
        )
        return self._format(res)

    def get_all(self, filenames: list[str] | None = None, limit: int = 100):
        """Fetch stored chunks (used by MMR/Hybrid re-ranking & comparison)."""
        where = {"filename": {"$in": filenames}} if filenames else None
        res = self.collection.get(where=where, limit=limit)
        out = []
        for doc, meta in zip(res.get("documents", []), res.get("metadatas", [])):
            out.append({"text": doc, "metadata": meta, "distance": None})
        return out

    def _format(self, res):
        out = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            out.append({"text": doc, "metadata": meta, "distance": dist})
        return out

    # -- STATS / ADMIN -------------------------------------------------------
    def count(self) -> int:
        return self.collection.count()

    def stats(self) -> dict:
        all_items = self.collection.get()
        files = {m.get("filename") for m in all_items.get("metadatas", [])}
        return {"total_chunks": self.count(), "files": sorted(f for f in files if f)}

    def reset(self):
        """Delete everything (used by the 'Clear all data' button)."""
        self.client.delete_collection("documents")
        self.collection = self.client.get_or_create_collection(
            name="documents", metadata={"hnsw:space": "cosine"}
        )
        log("Vector store reset.")
