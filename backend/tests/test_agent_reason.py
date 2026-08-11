from langchain_core.messages import HumanMessage

from app.agent.nodes.reason import ReasoningResult, reason


def _mock_reason_llm(mocker, reasoning_result: ReasoningResult):
    structured_mock = mocker.MagicMock()
    structured_mock.invoke.return_value = reasoning_result
    fake_llm = mocker.MagicMock()
    fake_llm.with_structured_output.return_value = structured_mock
    mocker.patch("app.agent.nodes.reason.llm", fake_llm)
    return fake_llm


def test_reason_maps_structured_result_into_state(mocker):
    _mock_reason_llm(
        mocker,
        ReasoningResult(
            analysis="Cites the ankle restriction directly.",
            needs_clarification=False,
            clarification_question=None,
        ),
    )

    state = {
        "messages": [HumanMessage("can I run again?")],
        "personal_context": "Injury: ankle sprain, restrictions: no running yet",
        "knowledge_context": None,
    }

    result = reason(state)

    assert result["analysis"] == "Cites the ankle restriction directly."
    assert result["needs_clarification"] is False
    assert result["clarification_question"] is None


def test_reason_surfaces_clarification_question(mocker):
    _mock_reason_llm(
        mocker,
        ReasoningResult(
            analysis="No relevant history found.",
            needs_clarification=True,
            clarification_question="Can you tell me more about when this happened?",
        ),
    )

    state = {
        "messages": [HumanMessage("can I run again?")],
        "personal_context": None,
        "knowledge_context": None,
    }

    result = reason(state)

    assert result["needs_clarification"] is True
    assert result["clarification_question"] == "Can you tell me more about when this happened?"


def test_reason_falls_back_to_generic_question_when_llm_forgets_to_fill_it(mocker):
    """A real, observed failure mode against the actual local model: it set
    needs_clarification=true but left clarification_question empty. Structured
    output only constrains the JSON shape, not this kind of cross-field semantic
    compliance - reason() must not trust it blindly."""
    _mock_reason_llm(
        mocker,
        ReasoningResult(analysis="Missing info.", needs_clarification=True, clarification_question=None),
    )

    state = {"messages": [HumanMessage("can I run again?")], "personal_context": None, "knowledge_context": None}

    result = reason(state)

    assert result["needs_clarification"] is True
    assert result["clarification_question"]  # non-empty fallback, not None


def test_reason_handles_missing_context_gracefully(mocker):
    """personal_context/knowledge_context aren't set at all when their branch
    was skipped by _route_after_classify - reason must use .get(), not direct
    subscripting, or this raises a KeyError."""
    _mock_reason_llm(
        mocker,
        ReasoningResult(analysis="Just answering generally.", needs_clarification=False),
    )

    state = {"messages": [HumanMessage("hi")]}  # no personal_context/knowledge_context keys at all

    result = reason(state)

    assert result["analysis"] == "Just answering generally."
