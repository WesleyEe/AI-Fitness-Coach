from app.llm.ollama_client import LLMServiceError
from app.models.knowledge_chunk import KnowledgeDomain
from app.rag.retriever import RetrievedChunk


def test_chat_returns_assistant_reply(client, mocker):
    mocker.patch("app.api.routes.chat.rag_search", return_value=[])
    mocker.patch("app.api.routes.chat.send_chat", return_value="Do 3x10 squats today.")

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "What should I train today?"}]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"]["role"] == "assistant"
    assert body["message"]["content"] == "Do 3x10 squats today."


def test_chat_includes_retrieved_knowledge_in_llm_context(client, mocker):
    mocker.patch(
        "app.api.routes.chat.rag_search",
        return_value=[
            RetrievedChunk(
                domain=KnowledgeDomain.HYROX,
                title="Sled Push and Pull Programming",
                content="Programming heavy sled pushes once per week...",
                distance=0.1,
            )
        ],
    )
    send_chat_mock = mocker.patch(
        "app.api.routes.chat.send_chat", return_value="Focus on heavy sled pushes weekly."
    )

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "How do I improve my sled push?"}]},
    )

    assert response.status_code == 200
    # The knowledge chunk should have been folded into the messages sent to the LLM.
    sent_messages = send_chat_mock.call_args[0][0]
    combined_content = " ".join(m["content"] for m in sent_messages)
    assert "Sled Push and Pull Programming" in combined_content


def test_chat_returns_503_when_ollama_unreachable(client, mocker):
    mocker.patch("app.api.routes.chat.rag_search", return_value=[])
    mocker.patch(
        "app.api.routes.chat.send_chat",
        side_effect=LLMServiceError("Could not reach Ollama"),
    )

    response = client.post("/chat", json={"messages": [{"role": "user", "content": "Hi"}]})

    assert response.status_code == 503


def test_chat_returns_503_when_retriever_embedding_fails(client, mocker):
    mocker.patch(
        "app.api.routes.chat.rag_search",
        side_effect=LLMServiceError("Could not reach Ollama"),
    )

    response = client.post("/chat", json={"messages": [{"role": "user", "content": "Hi"}]})

    assert response.status_code == 503


def test_chat_rejects_empty_body(client):
    response = client.post("/chat", json={})
    assert response.status_code == 422
