from app.agent.nodes.ask_clarification import ask_clarification


def test_ask_clarification_passes_question_through_as_response():
    state = {"clarification_question": "How severe was the injury on a scale of 1-10?"}

    result = ask_clarification(state)

    assert result == {"response": "How severe was the injury on a scale of 1-10?"}
