from app.models.knowledge_chunk import KnowledgeDomain
from app.rag.retriever import RetrievedChunk


def test_rag_search_returns_ranked_results(client, mocker):
    mocker.patch(
        "app.api.routes.rag.search",
        return_value=[
            RetrievedChunk(
                domain=KnowledgeDomain.INJURY_PREVENTION,
                title="Ankle Sprain Recovery Principles",
                content="Early protected movement...",
                distance=0.12,
            )
        ],
    )

    response = client.post("/rag/search", json={"query": "ankle injury recovery"})

    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["title"] == "Ankle Sprain Recovery Principles"
    assert results[0]["domain"] == "injury_prevention"


def test_rag_search_returns_503_when_ollama_unreachable(client, mocker):
    from app.llm.ollama_client import LLMServiceError

    mocker.patch(
        "app.api.routes.rag.search",
        side_effect=LLMServiceError("Could not reach Ollama"),
    )

    response = client.post("/rag/search", json={"query": "anything"})

    assert response.status_code == 503
