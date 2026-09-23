"""Routing (intent classification) accuracy against the REAL local model.

Unlike tests/test_agent_routing.py (tests the pure routing *functions* with a
canned dict) or tests/test_agent_full_graph.py (mocks the LLM entirely for fast,
deterministic plumbing tests), this calls the real classify_intent node with the
real model configured in Settings - because "does the graph route correctly when
the LLM returns X" and "does the LLM actually return X for a given question" are
two different questions, and only tests answer the first one. This answers the
second. Requires Ollama running locally with the configured model pulled - see
EVALS_AND_GUARDRAILS.md.
"""

from langchain_core.messages import HumanMessage

from app.agent.nodes.classify import classify_intent
from app.evals.models import EvalResult

# (case_id, message, expected_needs_personal_data, expected_needs_expert_knowledge)
CASES: list[tuple[str, str, bool, bool]] = [
    ("greeting_needs_neither", "Hey, how's it going?", False, False),
    ("progress_question_needs_personal", "Why do I feel like I'm not improving lately?", True, False),
    (
        "technique_question_needs_expert",
        "What's a good way to improve my sled push technique for Hyrox?",
        False,
        True,
    ),
    (
        "return_to_activity_needs_both",
        "My ankle sprain is healing, can I start running again?",
        True,
        True,
    ),
    ("plateau_question_needs_both", "My bench has stalled for weeks, what should I change?", True, True),
]


def run() -> list[EvalResult]:
    results = []
    for case_id, message, expected_personal, expected_expert in CASES:
        state = {"messages": [HumanMessage(message)]}
        out = classify_intent(state)

        passed = (
            out["needs_personal_data"] == expected_personal
            and out["needs_expert_knowledge"] == expected_expert
        )
        detail = (
            f"expected=(personal={expected_personal}, expert={expected_expert}) "
            f"actual=(personal={out['needs_personal_data']}, expert={out['needs_expert_knowledge']}) "
            f"model_reasoning={out['classification_reasoning']!r}"
        )
        results.append(EvalResult("routing", case_id, message, passed, detail))
    return results
