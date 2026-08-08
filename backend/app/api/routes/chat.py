from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.llm.ollama_client import LLMServiceError, send_chat
from app.llm.prompts import SYSTEM_PROMPT, build_knowledge_context
from app.rag.retriever import search as rag_search
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Naive RAG: always retrieve for the latest user message, no judgment call about
    # whether this particular question needs expert reference material - see
    # build_knowledge_context()'s docstring and PLAN.md's Sprint 4/5 notes.
    latest_user_message = next(
        (m.content for m in reversed(payload.messages) if m.role == "user"), None
    )
    try:
        if latest_user_message:
            chunks = await rag_search(db, latest_user_message)
            knowledge_context = build_knowledge_context(chunks)
            if knowledge_context:
                messages.append({"role": "system", "content": knowledge_context})

        messages += [m.model_dump() for m in payload.messages]
        reply_text = await send_chat(messages)
    except LLMServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ChatResponse(message=ChatMessage(role="assistant", content=reply_text))
