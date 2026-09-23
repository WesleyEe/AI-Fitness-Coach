from app.agent.state import AgentState
from app.guardrails.safety import screen_input


def input_guardrail(state: AgentState) -> dict:
    """First node in the graph - a deterministic, LLM-free screen on the user's
    latest message, run before classify_intent or any other model call.

    Safety-critical symptoms and prompt-injection attempts both belong here rather
    than in a system prompt: they need a response that's unconditionally correct,
    not one that depends on the model correctly weighing instructions on a given
    turn. See app/guardrails/safety.py for why this is regex-based, not an LLM call.
    """
    latest_user_message = next(
        (m.content for m in reversed(state["messages"]) if m.type == "human"), ""
    )

    result = screen_input(latest_user_message)
    if not result.blocked:
        return {"blocked": False}

    return {"blocked": True, "block_reason": result.category, "response": result.message}
