from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.llm.ollama_client import embed_text
from app.models.knowledge_chunk import KnowledgeChunk, KnowledgeDomain


@dataclass
class RetrievedChunk:
    domain: KnowledgeDomain
    title: str
    content: str
    distance: float  # cosine distance: 0 = identical, 2 = opposite. Lower is more relevant.


async def search(
    db: Session,
    query: str,
    top_k: int = settings.rag_top_k,
    domain: KnowledgeDomain | None = None,
) -> list[RetrievedChunk]:
    """Embed the query and return the top_k most similar knowledge chunks.

    Uses pgvector's cosine_distance() operator, backed by the HNSW index created in
    the knowledge_chunks migration - Postgres does the similarity ranking, not Python.
    """
    query_embedding = await embed_text(query)

    q = db.query(KnowledgeChunk)
    if domain is not None:
        q = q.filter(KnowledgeChunk.domain == domain)

    distance = KnowledgeChunk.embedding.cosine_distance(query_embedding)
    rows = q.order_by(distance).limit(top_k).with_entities(KnowledgeChunk, distance).all()

    return [
        RetrievedChunk(domain=chunk.domain, title=chunk.title, content=chunk.content, distance=dist)
        for chunk, dist in rows
    ]
