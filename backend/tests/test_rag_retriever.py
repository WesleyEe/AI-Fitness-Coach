import pytest

from app.core.config import settings
from app.models.knowledge_chunk import KnowledgeChunk, KnowledgeDomain
from app.rag.retriever import search

DIM = settings.embedding_dim


def unit_vector(index: int, sign: float = 1.0) -> list[float]:
    """A vector with a single 1.0 (or -1.0) at `index`, zeros elsewhere - lets us
    reason exactly about cosine distance: identical vectors -> 0, orthogonal -> 1,
    opposite -> 2."""
    vec = [0.0] * DIM
    vec[index] = sign
    return vec


@pytest.fixture()
def seeded_chunks(db_session):
    # The real knowledge base (ingested via `uv run python -m app.rag.ingest`) lives
    # permanently in this same dev DB. Clear it within this test's own transaction
    # (rolled back at teardown, per conftest.py) so it doesn't pollute similarity
    # ordering/top_k/domain-filter assertions below - this never touches the real data.
    db_session.query(KnowledgeChunk).delete()

    chunks = [
        KnowledgeChunk(
            domain=KnowledgeDomain.HYROX,
            source="test.md",
            title="Aligned",
            content="Points the same direction as the query.",
            embedding=unit_vector(0),
        ),
        KnowledgeChunk(
            domain=KnowledgeDomain.FOOTBALL,
            source="test.md",
            title="Orthogonal",
            content="Perpendicular to the query.",
            embedding=unit_vector(1),
        ),
        KnowledgeChunk(
            domain=KnowledgeDomain.BODYBUILDING,
            source="test.md",
            title="Opposite",
            content="Points the opposite direction from the query.",
            embedding=unit_vector(0, sign=-1.0),
        ),
    ]
    db_session.add_all(chunks)
    db_session.flush()
    return chunks


async def test_search_orders_by_cosine_distance(db_session, seeded_chunks, mocker):
    mocker.patch("app.rag.retriever.embed_text", return_value=unit_vector(0))

    results = await search(db_session, "irrelevant - embedding is mocked", top_k=3)

    assert [r.title for r in results] == ["Aligned", "Orthogonal", "Opposite"]
    assert results[0].distance == pytest.approx(0.0, abs=1e-6)
    assert results[1].distance == pytest.approx(1.0, abs=1e-6)
    assert results[2].distance == pytest.approx(2.0, abs=1e-6)


async def test_search_respects_domain_filter(db_session, seeded_chunks, mocker):
    mocker.patch("app.rag.retriever.embed_text", return_value=unit_vector(0))

    results = await search(db_session, "irrelevant", top_k=3, domain=KnowledgeDomain.FOOTBALL)

    assert len(results) == 1
    assert results[0].title == "Orthogonal"
    assert results[0].domain == KnowledgeDomain.FOOTBALL


async def test_search_respects_top_k(db_session, seeded_chunks, mocker):
    mocker.patch("app.rag.retriever.embed_text", return_value=unit_vector(0))

    results = await search(db_session, "irrelevant", top_k=1)

    assert len(results) == 1
    assert results[0].title == "Aligned"
