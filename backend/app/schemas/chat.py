from typing import Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    # The client sends the full conversation so far (its own state) each turn -
    # the server holds no session/conversation state in Sprint 3.
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    message: ChatMessage
