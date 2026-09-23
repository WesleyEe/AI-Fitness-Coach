from app.agent.nodes.verify_grounding import FALLBACK_QUESTION, verify_grounding
from app.guardrails.grounding import GroundingCheck


def _mock_grounding_llm(mocker, result: GroundingCheck):
    structured_mock = mocker.MagicMock()
    structured_mock.invoke.return_value = result
    fake_llm = mocker.MagicMock()
    fake_llm.with_structured_output.return_value = structured_mock
    mocker.patch("app.agent.nodes.verify_grounding.llm", fake_llm)
    return fake_llm


def test_verify_grounding_skips_when_no_personal_context():
    state = {"personal_context": None, "needs_clarification": False, "analysis": "General advice."}

    result = verify_grounding(state)

    assert result == {}


def test_verify_grounding_skips_when_already_needs_clarification(mocker):
    """Nothing to gain from re-checking analysis that reason already decided not
    to use - and it shouldn't spend an LLM call doing so."""
    fake_llm = _mock_grounding_llm(mocker, GroundingCheck(grounded=True))

    state = {
        "personal_context": "Injury history:\n- 2026-07-20: ankle sprain (status: recovered)",
        "needs_clarification": True,
        "analysis": "Not enough info.",
    }

    result = verify_grounding(state)

    assert result == {}
    fake_llm.with_structured_output.assert_not_called()


def test_verify_grounding_passes_through_when_grounded(mocker):
    _mock_grounding_llm(mocker, GroundingCheck(grounded=True))

    state = {
        "personal_context": "Injury history:\n- 2026-07-20: ankle sprain (status: recovered)",
        "needs_clarification": False,
        "analysis": "Their ankle sprain has recovered with no restrictions.",
    }

    result = verify_grounding(state)

    assert result == {"unsupported_claims": []}


def test_verify_grounding_overrides_to_clarification_when_ungrounded(mocker):
    """Mirrors the Sprint 6 finding directly: analysis fabricates a status/
    restriction not present in personal_context - the guardrail should catch it
    and stop it from reaching recommend."""
    _mock_grounding_llm(
        mocker,
        GroundingCheck(grounded=False, unsupported_claims=["status is 'recovering'", "no running yet"]),
    )

    state = {
        "personal_context": "Injury history:\n- 2026-07-20: ankle sprain (status: recovered)",
        "needs_clarification": False,
        "analysis": "Their ankle sprain status is 'recovering' with a 'no running yet' restriction.",
    }

    result = verify_grounding(state)

    assert result["needs_clarification"] is True
    assert result["clarification_question"] == FALLBACK_QUESTION
    assert result["unsupported_claims"] == ["status is 'recovering'", "no running yet"]
