import httpx
import pytest

from app.llm.ollama_client import LLMServiceError


def test_chat_returns_assistant_reply(client, mocker):
    mocker.patch("app.api.routes.chat.send_chat", return_value="Do 3x10 squats today.")

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "What should I train today?"}]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"]["role"] == "assistant"
    assert body["message"]["content"] == "Do 3x10 squats today."


def test_chat_returns_503_when_ollama_unreachable(client, mocker):
    mocker.patch(
        "app.api.routes.chat.send_chat",
        side_effect=LLMServiceError("Could not reach Ollama"),
    )

    response = client.post("/chat", json={"messages": [{"role": "user", "content": "Hi"}]})

    assert response.status_code == 503


def test_chat_rejects_empty_body(client):
    response = client.post("/chat", json={})
    assert response.status_code == 422
