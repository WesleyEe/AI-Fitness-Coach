from types import SimpleNamespace

from langchain_core.messages import HumanMessage

from app.agent.graph import build_agent_graph
from app.agent.nodes.classify import IntentClassification
from app.agent.nodes.reason import ReasoningResult
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
        "needs_clarification": False,
        "clarification_question": None,
        "response": None,
    }


def _mock_llm(
    mocker,
    classification: IntentClassification,
    reasoning_result: ReasoningResult | None = None,
    reply_text: str = "Mocked reply.",
):
    """Two different Pydantic schemas now go through .with_structured_output()
    (classify_intent -> IntentClassification, reason -> ReasoningResult), so the
    mock has to return a different canned result depending on which schema was
    requested - a plain single return_value (Sprint 5's approach) can't
    distinguish between them anymore.
    """
    if reasoning_result is None:
        reasoning_result = ReasoningResult(
            analysis="Mocked analysis.", needs_clarification=False, clarification_question=None
        )

    classification_container = mocker.MagicMock()
    classification_container.invoke.return_value = classification
    reasoning_container = mocker.MagicMock()
    reasoning_container.invoke.return_value = reasoning_result

    def with_structured_output_side_effect(schema, *args, **kwargs):
        if schema is IntentClassification:
            return classification_container
        if schema is ReasoningResult:
            return reasoning_container
        raise AssertionError(f"Unexpected structured output schema: {schema}")

    fake_llm = mocker.MagicMock()
    fake_llm.with_structured_output.side_effect = with_structured_output_side_effect
    fake_llm.invoke.return_value = SimpleNamespace(content=reply_text)

    # ChatOllama is a Pydantic model, which doesn't support mocker.patch.object()
    # on an instance the normal way (Pydantic restricts arbitrary instance
    # attribute set/delete, which breaks the patch's teardown). Each node module
    # also did `from app.agent.llm import llm`, binding its own name to the
    # original object at import time - patching app.agent.llm.llm wouldn't reach
    # those. So: build one fake LLM and patch the name in each consuming module.
    mocker.patch("app.agent.nodes.classify.llm", fake_llm)
    mocker.patch("app.agent.nodes.reason.llm", fake_llm)
    mocker.patch("app.agent.nodes.recommend.llm", fake_llm)

    return fake_llm


async def test_full_graph_skips_fetch_context_when_nothing_needed(db_session, mocker):
    _mock_llm(
        mocker,
        IntentClassification(needs_personal_data=False, needs_expert_knowledge=False, reasoning="just a greeting"),
    )

    graph = build_agent_graph(db_session)
    final_state = await graph.ainvoke(_initial_state("Hi there!"))

    assert final_state["personal_context"] is None  # fetch_context never ran
    assert final_state["knowledge_context"] is None
    assert final_state["analysis"] == "Mocked analysis."
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


async def test_full_graph_asks_clarification_instead_of_recommending(db_session, mocker):
    fake_llm = _mock_llm(
        mocker,
        IntentClassification(needs_personal_data=True, needs_expert_knowledge=False, reasoning="needs history"),
        reasoning_result=ReasoningResult(
            analysis="No history found, can't safely advise.",
            needs_clarification=True,
            clarification_question="How long ago was your ankle injury, and has a doctor cleared you?",
        ),
        reply_text="This should never be used.",
    )

    graph = build_agent_graph(db_session)
    # No user_id provided, so fetch_context will report no personal data available -
    # exactly the situation reason should flag as needing clarification.
    final_state = await graph.ainvoke(_initial_state("My ankle is better, can I run again?"))

    assert final_state["needs_clarification"] is True
    assert final_state["response"] == "How long ago was your ankle injury, and has a doctor cleared you?"
    # recommend's plain .invoke() should never have been reached - only reason's
    # structured-output call should have used the shared mock's .invoke via with_structured_output,
    # not the fallback plain invoke used for the final reply text.
    fake_llm.invoke.assert_not_called()
