from typing import TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Shared state threaded through every node in the graph.

    Each node is a plain function `(state) -> dict` that returns only the keys
    it wants to update - LangGraph merges that partial dict back into the full
    state before calling the next node. Nothing here needs a custom reducer
    (like the `add_messages` pattern for growing a list) because every field is
    simply overwritten once by the node responsible for it, not accumulated
    across multiple nodes.
    """

    messages: list[BaseMessage]  # full conversation so far, oldest first
    user_id: int | None

    # Set by input_guardrail
    blocked: bool
    block_reason: str | None

    # Set by classify_intent
    needs_personal_data: bool
    needs_expert_knowledge: bool
    classification_reasoning: str

    # Set by fetch_context (only the branch(es) that were needed)
    personal_context: str | None
    knowledge_context: str | None

    # Set by reason
    analysis: str | None
    needs_clarification: bool
    clarification_question: str | None

    # Set by verify_grounding, only when it flags an ungrounded claim
    unsupported_claims: list[str] | None

    # Set by recommend, ask_clarification, or input_guardrail (when blocked) -
    # the final answer returned to the user
    response: str | None
