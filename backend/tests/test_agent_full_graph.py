from types import SimpleNamespace

from langchain_core.messages import HumanMessage

from app.agent.graph import build_agent_graph
from app.agent.nodes.classify import IntentClassification
from app.models.user import User
from app.models.workout import ExerciseType, Workout


def _initial_state(message: str, user_id: int | None = None) -> dict:
    return {
        "messages": [HumanMessage(message)],
        "user_id": user_id,
        "needs_personal_data": False,
        "needs_expert_knowledge": False,
        "classification_reasoning": "",
        "personal_context": None,
        "knowledge_context": None,
        "analysis": None,
        "response": None,
    }


def _mock_llm(mocker, classification: IntentClassification, reply_text: str = "Mocked reply."):
    # ChatOllama is a Pydantic model, which doesn't support mocker.patch.object()
    # on an instance the normal way (Pydantic restricts arbitrary instance
    # attribute set/delete, which breaks the patch's teardown). Each node module
    # also did `from app.agent.llm import llm`, binding its own name to the
    # original object at import time - patching app.agent.llm.llm wouldn't reach
    # those. So: build one fake LLM and patch the name in each consuming module.
    fake_llm = mocker.MagicMock()
    structured_mock = mocker.MagicMock()
    structured_mock.invoke.return_value = classification
    fake_llm.with_structured_output.return_value = structured_mock
    fake_llm.invoke.return_value = SimpleNamespace(content=reply_text)

    mocker.patch("app.agent.nodes.classify.llm", fake_llm)
    mocker.patch("app.agent.nodes.reason.llm", fake_llm)
    mocker.patch("app.agent.nodes.recommend.llm", fake_llm)


async def test_full_graph_skips_fetch_context_when_nothing_needed(db_session, mocker):
    _mock_llm(
        mocker,
        IntentClassification(needs_personal_data=False, needs_expert_knowledge=False, reasoning="just a greeting"),
    )

    graph = build_agent_graph(db_session)
    final_state = await graph.ainvoke(_initial_state("Hi there!"))

    assert final_state["personal_context"] is None  # fetch_context never ran
    assert final_state["knowledge_context"] is None
    assert final_state["analysis"] == "Mocked reply."
    assert final_state["response"] == "Mocked reply."


async def test_full_graph_fetches_personal_data_when_needed(db_session, mocker):
    user = User(name="Graph Test User")
    db_session.add(user)
    db_session.flush()
    db_session.add(
        Workout(user_id=user.id, date="2026-08-01", exercise_type=ExerciseType.STRENGTH, notes="heavy squats")
    )
    db_session.flush()

    _mock_llm(
        mocker,
        IntentClassification(needs_personal_data=True, needs_expert_knowledge=False, reasoning="needs history"),
    )

    graph = build_agent_graph(db_session)
    final_state = await graph.ainvoke(
        _initial_state("Why am I not improving?", user_id=user.id)
    )

    assert final_state["personal_context"] is not None
    assert "heavy squats" in final_state["personal_context"]
    assert final_state["knowledge_context"] is None  # wasn't needed
    assert final_state["response"] == "Mocked reply."


async def test_full_graph_fetches_knowledge_when_needed(db_session, mocker):
    mocker.patch("app.agent.nodes.context.rag_search", return_value=[])
    _mock_llm(
        mocker,
        IntentClassification(needs_personal_data=False, needs_expert_knowledge=True, reasoning="needs expert info"),
    )

    graph = build_agent_graph(db_session)
    final_state = await graph.ainvoke(_initial_state("How do I improve my sled push?"))

    assert final_state["knowledge_context"] is not None
    assert final_state["personal_context"] is None  # wasn't needed
