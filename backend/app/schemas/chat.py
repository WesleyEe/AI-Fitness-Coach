from typing import Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    # The client sends the full conversation so far (its own state) each turn -
    # the server holds no conversation state between requests.
    messages: list[ChatMessage]
    # Optional since there's still no auth (see ARCHITECTURE.md) - without it, the
    # agent's needs_personal_data branch has no user to look up and says so rather
    # than fabricating history.
    user_id: int | None = None


class ChatResponse(BaseModel):
    message: ChatMessage
