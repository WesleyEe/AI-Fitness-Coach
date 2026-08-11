import httpx
from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.orm import Session

from app.agent.graph import build_agent_graph
from app.core.db import get_db
from app.llm.ollama_client import LLMServiceError
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    messages = [
        HumanMessage(m.content) if m.role == "user" else AIMessage(m.content)
        for m in payload.messages
    ]

    initial_state = {
        "messages": messages,
        "user_id": payload.user_id,
        "needs_personal_data": False,
        "needs_expert_knowledge": False,
        "classification_reasoning": "",
        "personal_context": None,
        "knowledge_context": None,
        "analysis": None,
        "needs_clarification": False,
        "clarification_question": None,
        "response": None,
    }

    graph = build_agent_graph(db)
    try:
        final_state = await graph.ainvoke(initial_state)
    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=503, detail=f"Could not reach Ollama: {exc}"
        ) from exc
    except LLMServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return ChatResponse(message=ChatMessage(role="assistant", content=final_state["response"]))
