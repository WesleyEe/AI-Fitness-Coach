from pydantic import BaseModel

from app.models.knowledge_chunk import KnowledgeDomain


class RagSearchRequest(BaseModel):
    query: str
    domain: KnowledgeDomain | None = None
    top_k: int = 3


class RagSearchResult(BaseModel):
    domain: KnowledgeDomain
    title: str
    content: str
    distance: float


class RagSearchResponse(BaseModel):
    results: list[RagSearchResult]
