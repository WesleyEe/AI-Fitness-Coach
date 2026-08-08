from app.core.config import settings
from app.models.knowledge_chunk import KnowledgeChunk, KnowledgeDomain
from app.rag.ingest import ingest_file


async def test_ingest_file_chunks_embeds_and_stores(db_session, tmp_path, mocker):
    mocker.patch("app.rag.ingest.embed_text", return_value=[0.1] * settings.embedding_dim)

    doc = tmp_path / "hyrox.md"
    doc.write_text("## Section One\n\nBody one.\n\n## Section Two\n\nBody two.\n")

    count = await ingest_file(db_session, doc)

    assert count == 2
    stored = db_session.query(KnowledgeChunk).filter(KnowledgeChunk.source == "hyrox.md").all()
    assert {c.title for c in stored} == {"Section One", "Section Two"}
    assert all(c.domain == KnowledgeDomain.HYROX for c in stored)


async def test_ingest_file_is_idempotent_on_rerun(db_session, tmp_path, mocker):
    mocker.patch("app.rag.ingest.embed_text", return_value=[0.1] * settings.embedding_dim)

    doc = tmp_path / "football.md"
    doc.write_text("## Only Section\n\nSome content.\n")

    await ingest_file(db_session, doc)
    await ingest_file(db_session, doc)  # re-run after "editing" the same file

    stored = db_session.query(KnowledgeChunk).filter(KnowledgeChunk.source == "football.md").all()
    assert len(stored) == 1  # not duplicated


async def test_ingest_file_rejects_filename_not_matching_a_domain(db_session, tmp_path, mocker):
    mocker.patch("app.rag.ingest.embed_text", return_value=[0.1] * settings.embedding_dim)

    doc = tmp_path / "not_a_real_domain.md"
    doc.write_text("## Section\n\nContent.\n")

    try:
        await ingest_file(db_session, doc)
        assert False, "expected ValueError for an unrecognized domain filename"
    except ValueError:
        pass
