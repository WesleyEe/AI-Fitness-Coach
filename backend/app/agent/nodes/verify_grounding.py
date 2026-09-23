from app.agent.llm import llm
from app.agent.state import AgentState
from app.guardrails.grounding import check_grounding

FALLBACK_QUESTION = (
    "Before I answer, I want to double-check something about your history rather "
    "than risk getting a detail wrong - could you confirm your current status and "
    "any restrictions you've been given?"
)


def verify_grounding(state: AgentState) -> dict:
    """Runs after `reason`, before the recommend/ask_clarification branch.

    Targets the exact failure documented in PLAN.md's Sprint 6 writeup: `reason`
    can write a confident `analysis` that states a specific injury status or
    restriction contradicting - or absent from - the `personal_context` it was
    actually given. This is a second, narrowly-scoped LLM call whose only job is
    comparing analysis against source context; see app/guardrails/grounding.py.

    Only runs when personal_context was gathered (that's the only place this
    failure mode was observed - running it unconditionally would double the LLM
    calls on every turn for no benefit) and reason hasn't already decided to ask
    for clarification for some other reason (nothing to gain from re-checking
    analysis that isn't going to be used anyway).
    """
    personal_context = state.get("personal_context")
    if not personal_context or state.get("needs_clarification"):
        return {}

    check = check_grounding(llm, state["analysis"], personal_context)
    if check.grounded:
        return {"unsupported_claims": []}

    # Don't let a fabricated claim reach the user: override the routing decision
    # rather than push the ungrounded analysis on to `recommend` anyway. This is
    # the same "ask rather than guess" pattern `reason` itself uses - just
    # triggered by a fact-check failing instead of missing information.
    return {
        "needs_clarification": True,
        "clarification_question": FALLBACK_QUESTION,
        "unsupported_claims": check.unsupported_claims,
    }
