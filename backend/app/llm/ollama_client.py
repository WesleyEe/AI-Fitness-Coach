"""Thin wrapper around Ollama's REST API.

Deliberately raw HTTP (via httpx) rather than a framework like LangChain -
Sprint 3's goal is to see exactly what a chat completion request/response
looks like before Sprint 5 wraps it in higher-level orchestration.

Ollama's /api/chat endpoint: https://github.com/ollama/ollama/blob/main/docs/api.md#chat-request-with-history
Request:  {"model": ..., "messages": [{"role": "user"|"assistant"|"system", "content": ...}], "stream": false}
Response: {"message": {"role": "assistant", "content": "..."}, "done": true, ...}
"""

import httpx

from app.core.config import settings


class LLMServiceError(Exception):
    """Raised when the local Ollama server is unreachable or returns an error."""


async def send_chat(messages: list[dict[str, str]]) -> str:
    """Send a full conversation history to Ollama and return the assistant's reply text."""
    url = f"{settings.ollama_base_url}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            response = await http_client.post(url, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LLMServiceError(f"Could not reach Ollama at {settings.ollama_base_url}: {exc}") from exc

    data = response.json()
    return data["message"]["content"]
