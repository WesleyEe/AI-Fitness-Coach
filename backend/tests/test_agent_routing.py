from app.agent.graph import _route_after_classify, _route_after_reason


def _classify_state(needs_personal_data=False, needs_expert_knowledge=False):
    return {"needs_personal_data": needs_personal_data, "needs_expert_knowledge": needs_expert_knowledge}


def test_routes_to_fetch_context_when_personal_data_needed():
    assert _route_after_classify(_classify_state(needs_personal_data=True)) == "fetch_context"


def test_routes_to_fetch_context_when_expert_knowledge_needed():
    assert _route_after_classify(_classify_state(needs_expert_knowledge=True)) == "fetch_context"


def test_routes_to_fetch_context_when_both_needed():
    assert (
        _route_after_classify(_classify_state(needs_personal_data=True, needs_expert_knowledge=True))
        == "fetch_context"
    )


def test_skips_fetch_context_when_neither_needed():
    assert _route_after_classify(_classify_state()) == "reason"


def test_routes_to_ask_clarification_when_needed():
    assert _route_after_reason({"needs_clarification": True}) == "ask_clarification"


def test_routes_to_recommend_when_clarification_not_needed():
    assert _route_after_reason({"needs_clarification": False}) == "recommend"
