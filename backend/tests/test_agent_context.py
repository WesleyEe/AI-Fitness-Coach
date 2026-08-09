from langchain_core.messages import HumanMessage

from app.agent.nodes.context import make_fetch_context_node
from app.models.injury import Injury, InjurySeverity, InjuryStatus
from app.models.user import User
from app.models.workout import ExerciseType, Workout
from app.rag.retriever import RetrievedChunk
from app.models.knowledge_chunk import KnowledgeDomain


def _base_state(**overrides):
    state = {
        "messages": [HumanMessage("My ankle is better, can I start running again?")],
        "user_id": None,
        "needs_personal_data": False,
        "needs_expert_knowledge": False,
    }
    state.update(overrides)
    return state


async def test_fetch_context_gathers_personal_data_when_needed(db_session):
    user = User(name="Test User")
    db_session.add(user)
    db_session.flush()

    db_session.add(
        Workout(user_id=user.id, date="2026-08-05", exercise_type=ExerciseType.MOBILITY, notes="ankle work")
    )
    db_session.add(
        Injury(
            user_id=user.id,
            injury_type="ankle sprain",
            date_occurred="2026-07-20",
            severity=InjurySeverity.MODERATE,
            status=InjuryStatus.RECOVERING,
            restrictions="no running yet",
        )
    )
    db_session.flush()

    node = make_fetch_context_node(db_session)
    result = await node(_base_state(user_id=user.id, needs_personal_data=True))

    assert "personal_context" in result
    assert "ankle work" in result["personal_context"]
    assert "no running yet" in result["personal_context"]
    assert "knowledge_context" not in result  # wasn't needed, so wasn't fetched


async def test_fetch_context_reports_missing_user_id_gracefully(db_session):
    node = make_fetch_context_node(db_session)
    result = await node(_base_state(user_id=None, needs_personal_data=True))

    assert "No user_id was provided" in result["personal_context"]


async def test_fetch_context_reports_no_history_found(db_session):
    user = User(name="Fresh User")
    db_session.add(user)
    db_session.flush()

    node = make_fetch_context_node(db_session)
    result = await node(_base_state(user_id=user.id, needs_personal_data=True))

    assert "No workout or injury history found" in result["personal_context"]


async def test_fetch_context_gathers_knowledge_when_needed(db_session, mocker):
    mocker.patch(
        "app.agent.nodes.context.rag_search",
        return_value=[
            RetrievedChunk(
                domain=KnowledgeDomain.INJURY_PREVENTION,
                title="Ankle Sprain Recovery Principles",
                content="Early protected movement...",
                distance=0.1,
            )
        ],
    )

    node = make_fetch_context_node(db_session)
    result = await node(_base_state(needs_expert_knowledge=True))

    assert "personal_context" not in result  # wasn't needed
    assert "Ankle Sprain Recovery Principles" in result["knowledge_context"]


async def test_fetch_context_gathers_both_when_both_needed(db_session, mocker):
    mocker.patch("app.agent.nodes.context.rag_search", return_value=[])
    user = User(name="Both Needed User")
    db_session.add(user)
    db_session.flush()

    node = make_fetch_context_node(db_session)
    result = await node(
        _base_state(user_id=user.id, needs_personal_data=True, needs_expert_knowledge=True)
    )

    assert "personal_context" in result
    assert "knowledge_context" in result
