from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.core.config import settings


@dataclass
class SimilarThreadResult:
    id: str
    text: str
    score: float
    metadata: Dict[str, Any]


class ChromaClient:
    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: str = "thread_summaries",
        embedding_model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name

        self.embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=embedding_model_name
        )
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
        )

    def upsert_thread_summary(
        self,
        *,
        user_id: int,
        thread_id: str,
        summary_text: str,
        message_id: Optional[str] = None,
        gmail_thread_id: Optional[str] = None,
    ) -> None:
        # Id must be stable so updates overwrite.
        doc_id = f"{user_id}:{thread_id}"
        metadata: Dict[str, Any] = {"user_id": user_id}
        if message_id:
            metadata["message_id"] = message_id
        if gmail_thread_id:
            metadata["gmail_thread_id"] = gmail_thread_id

        # Chroma uses add for upsert-like behavior when ids are unique.
        self.collection.upsert(
            ids=[doc_id],
            metadatas=[metadata],
            documents=[summary_text],
        )

    def query_similar_threads(
        self,
        *,
        user_id: int,
        query_text: str,
        top_k: int = 5,
    ) -> List[SimilarThreadResult]:
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where={"user_id": user_id},
        )

        out: List[SimilarThreadResult] = []
        ids = results.get("ids", [[]])[0] or []
        docs = results.get("documents", [[]])[0] or []
        metas = results.get("metadatas", [[]])[0] or []
        scores = results.get("distances", [[]])[0] or results.get("scores", [[]])[0] or []

        for i, doc_id in enumerate(ids):
            out.append(
                SimilarThreadResult(
                    id=str(doc_id),
                    text=str(docs[i]) if i < len(docs) else "",
                    score=float(scores[i]) if i < len(scores) else 0.0,
                    metadata=dict(metas[i]) if i < len(metas) and metas[i] else {},
                )
            )
        return out

