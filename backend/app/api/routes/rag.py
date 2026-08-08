from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.llm.ollama_client import LLMServiceError
from app.rag.retriever import search
from app.schemas.rag import RagSearchRequest, RagSearchResponse, RagSearchResult

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/search", response_model=RagSearchResponse)
async def rag_search(payload: RagSearchRequest, db: Session = Depends(get_db)) -> RagSearchResponse:
    """Manual retrieval-quality testing endpoint - not used by /chat directly.

    Lets you eyeball whether a given question surfaces the right knowledge chunks
    before trusting the pipeline to feed an LLM.
    """
    try:
        results = await search(db, payload.query, top_k=payload.top_k, domain=payload.domain)
    except LLMServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return RagSearchResponse(
        results=[
            RagSearchResult(domain=r.domain, title=r.title, content=r.content, distance=r.distance)
            for r in results
        ]
    )
