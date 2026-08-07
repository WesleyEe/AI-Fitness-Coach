from fastapi import APIRouter, HTTPException

from app.llm.ollama_client import LLMServiceError, send_chat
from app.llm.prompts import SYSTEM_PROMPT
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [m.model_dump() for m in payload.messages]

    try:
        reply_text = await send_chat(messages)
    except LLMServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ChatResponse(message=ChatMessage(role="assistant", content=reply_text))
