from app.guardrails.grounding import GroundingCheck, check_grounding


def _mock_llm(mocker, result: GroundingCheck):
    structured_mock = mocker.MagicMock()
    structured_mock.invoke.return_value = result
    fake_llm = mocker.MagicMock()
    fake_llm.with_structured_output.return_value = structured_mock
    return fake_llm


def test_check_grounding_passes_through_grounded_result(mocker):
    fake_llm = _mock_llm(mocker, GroundingCheck(grounded=True, unsupported_claims=[]))

    result = check_grounding(
        fake_llm,
        analysis="Their ankle sprain is recovered with no restrictions.",
        source_context="Injury history:\n- 2026-07-20: ankle sprain (moderate, status: recovered)",
    )

    assert result.grounded is True
    assert result.unsupported_claims == []
    fake_llm.with_structured_output.assert_called_once_with(GroundingCheck)


def test_check_grounding_surfaces_unsupported_claims(mocker):
    """Mirrors the exact Sprint 6 failure: status 'recovered', no restrictions in
    the source, but analysis fabricates 'recovering' and a 'no running yet'
    restriction - the check should report that fabrication."""
    fake_llm = _mock_llm(
        mocker,
        GroundingCheck(
            grounded=False,
            unsupported_claims=[
                "status is 'recovering'",
                "restriction: no running yet",
            ],
        ),
    )

    result = check_grounding(
        fake_llm,
        analysis="Their ankle sprain status is 'recovering' with a 'no running yet' restriction.",
        source_context="Injury history:\n- 2026-07-20: ankle sprain (moderate, status: recovered)",
    )

    assert result.grounded is False
    assert "status is 'recovering'" in result.unsupported_claims


def test_check_grounding_sends_both_source_and_analysis_to_the_model(mocker):
    fake_llm = _mock_llm(mocker, GroundingCheck(grounded=True))
    structured_mock = fake_llm.with_structured_output.return_value

    check_grounding(fake_llm, analysis="ANALYSIS_TEXT", source_context="SOURCE_TEXT")

    sent_messages = structured_mock.invoke.call_args[0][0]
    human_message_content = sent_messages[-1].content
    assert "SOURCE_TEXT" in human_message_content
    assert "ANALYSIS_TEXT" in human_message_content
