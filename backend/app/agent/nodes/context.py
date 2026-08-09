from collections.abc import Callable, Coroutine
from typing import Any

from sqlalchemy.orm import Session

from app.agent.state import AgentState
from app.models.injury import Injury
from app.models.workout import Workout
from app.rag.retriever import RetrievedChunk, search as rag_search

RECENT_WORKOUTS_LIMIT = 5


def _format_personal_context(workouts: list[Workout], injuries: list[Injury]) -> str:
    if not workouts and not injuries:
        return "No workout or injury history found for this user."

    lines: list[str] = []

    if workouts:
        lines.append("Recent workouts (most recent first):")
        for w in workouts:
            detail = f"- {w.date}: {w.exercise_type.value}"
            if w.duration_minutes:
                detail += f", {w.duration_minutes} min"
            if w.notes:
                detail += f" - {w.notes}"
            lines.append(detail)

    if injuries:
        lines.append("\nInjury history:")
        for i in injuries:
            lines.append(
                f"- {i.date_occurred}: {i.injury_type} ({i.severity.value}, status: {i.status.value})"
                + (f" - restrictions: {i.restrictions}" if i.restrictions else "")
            )

    return "\n".join(lines)


def _format_knowledge_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return ""
    return "\n\n".join(f"### {c.title} ({c.domain.value})\n{c.content}" for c in chunks)


def make_fetch_context_node(db: Session) -> Callable[[AgentState], Coroutine[Any, Any, dict]]:
    """Build the fetch_context node as a closure over this request's DB session.

    The graph is built fresh per-request (see app/agent/graph.py) precisely so
    nodes that need the DB can just close over a plain `db: Session` rather than
    threading a session through AgentState itself - state should stay to
    request/response-shaped data, not live infrastructure objects.
    """

    async def fetch_context(state: AgentState) -> dict:
        update: dict = {}

        if state["needs_personal_data"]:
            if state["user_id"] is not None:
                workouts = (
                    db.query(Workout)
                    .filter(Workout.user_id == state["user_id"])
                    .order_by(Workout.date.desc())
                    .limit(RECENT_WORKOUTS_LIMIT)
                    .all()
                )
                injuries = (
                    db.query(Injury)
                    .filter(Injury.user_id == state["user_id"])
                    .order_by(Injury.date_occurred.desc())
                    .all()
                )
                update["personal_context"] = _format_personal_context(workouts, injuries)
            else:
                update["personal_context"] = (
                    "No user_id was provided, so personal workout/injury history is unavailable."
                )

        if state["needs_expert_knowledge"]:
            latest_user_message = next(
                (m.content for m in reversed(state["messages"]) if m.type == "human"), ""
            )
            chunks = await rag_search(db, latest_user_message)
            update["knowledge_context"] = _format_knowledge_context(chunks)

        return update

    return fetch_context
