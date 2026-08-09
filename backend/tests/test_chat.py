import httpx


def _fake_graph(final_state: dict):
    """A stand-in for the compiled LangGraph graph, exposing just the .ainvoke()
    surface the chat route actually calls - keeps these tests about the route's
    request/response handling, independent of graph/node internals (which have
    their own focused tests in test_agent_*.py)."""

    class FakeGraph:
        async def ainvoke(self, state):
            return final_state

    return FakeGraph()


def test_chat_returns_assistant_reply(client, mocker):
    mocker.patch(
        "app.api.routes.chat.build_agent_graph",
        return_value=_fake_graph({"response": "Do 3x10 squats today."}),
    )

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "What should I train today?"}]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"]["role"] == "assistant"
    assert body["message"]["content"] == "Do 3x10 squats today."


def test_chat_passes_user_id_through_to_initial_state(client, mocker):
    captured_states = []

    class CapturingGraph:
        async def ainvoke(self, state):
            captured_states.append(state)
            return {"response": "ok"}

    mocker.patch("app.api.routes.chat.build_agent_graph", return_value=CapturingGraph())

    client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "hi"}], "user_id": 42},
    )

    assert captured_states[0]["user_id"] == 42


def test_chat_converts_message_history_to_langchain_messages(client, mocker):
    captured_states = []

    class CapturingGraph:
        async def ainvoke(self, state):
            captured_states.append(state)
            return {"response": "ok"}

    mocker.patch("app.api.routes.chat.build_agent_graph", return_value=CapturingGraph())

    client.post(
        "/chat",
        json={
            "messages": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello!"},
            ]
        },
    )

    messages = captured_states[0]["messages"]
    assert [m.type for m in messages] == ["human", "ai"]
    assert [m.content for m in messages] == ["hi", "hello!"]


def test_chat_returns_503_when_ollama_unreachable(client, mocker):
    class FailingGraph:
        async def ainvoke(self, state):
            raise httpx.ConnectError("Connection refused")

    mocker.patch("app.api.routes.chat.build_agent_graph", return_value=FailingGraph())

    response = client.post("/chat", json={"messages": [{"role": "user", "content": "Hi"}]})

    assert response.status_code == 503


def test_chat_rejects_empty_body(client):
    response = client.post("/chat", json={})
    assert response.status_code == 422
