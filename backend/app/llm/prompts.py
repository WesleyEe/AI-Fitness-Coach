from app.rag.retriever import RetrievedChunk

SYSTEM_PROMPT = """\
You are a knowledgeable, encouraging personal fitness coach. You help with football, \
Hyrox training, bodybuilding, and injury recovery/prevention.

You do not yet have access to the user's workout history or injury history - you're \
working from general fitness expertise, retrieved reference material (if provided \
below), and whatever the user tells you directly in this conversation. If a \
recommendation would benefit from information you don't have (their recent training \
load, an old injury, etc.), ask for it rather than guessing.

Keep responses practical and specific - concrete sets/reps/durations over vague advice.
"""


def build_knowledge_context(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved knowledge chunks into a system message the LLM can cite from.

    Naive RAG: this is always called with whatever the retriever found for the
    latest user message - there's no judgment yet about whether the question
    actually needed expert reference material. Sprint 5's agent adds that decision.
    """
    if not chunks:
        return ""

    sections = "\n\n".join(f"### {c.title} ({c.domain.value})\n{c.content}" for c in chunks)
    return (
        "Reference material retrieved for the user's latest message. Use it if "
        "relevant, but don't force it in if the question doesn't call for it, and "
        "don't mention that you're using \"retrieved material\" - just answer naturally:\n\n"
        f"{sections}"
    )
