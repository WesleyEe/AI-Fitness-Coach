from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agent.nodes.classify import classify_intent
from app.agent.nodes.context import make_fetch_context_node
from app.agent.nodes.reason import reason
from app.agent.nodes.recommend import recommend
from app.agent.state import AgentState


def _route_after_classify(state: AgentState) -> str:
    """The one real conditional edge in this graph: skip fetch_context entirely
    (not just no-op through it) when neither DB history nor expert knowledge was
    judged necessary - e.g. a plain greeting."""
    if state["needs_personal_data"] or state["needs_expert_knowledge"]:
        return "fetch_context"
    return "reason"


def build_agent_graph(db: Session):
    """Build and compile the agent graph fresh for this request.

    Built per-request (not once at import time) so fetch_context can close over
    this request's DB session directly, rather than threading a live Session
    object through AgentState - state should stay to request/response-shaped
    data. Graph construction itself is cheap (assembling plain Python objects),
    so rebuilding it per request has no meaningful cost.
    """
    builder = StateGraph(AgentState)

    builder.add_node("classify_intent", classify_intent)
    builder.add_node("fetch_context", make_fetch_context_node(db))
    builder.add_node("reason", reason)
    builder.add_node("recommend", recommend)

    builder.set_entry_point("classify_intent")
    builder.add_conditional_edges(
        "classify_intent",
        _route_after_classify,
        {"fetch_context": "fetch_context", "reason": "reason"},
    )
    builder.add_edge("fetch_context", "reason")
    builder.add_edge("reason", "recommend")
    builder.add_edge("recommend", END)

    return builder.compile()
