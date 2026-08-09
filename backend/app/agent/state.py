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

    # Set by classify_intent
    needs_personal_data: bool
    needs_expert_knowledge: bool
    classification_reasoning: str

    # Set by fetch_context (only the branch(es) that were needed)
    personal_context: str | None
    knowledge_context: str | None

    # Set by reason
    analysis: str | None

    # Set by recommend - the final answer returned to the user
    response: str | None
