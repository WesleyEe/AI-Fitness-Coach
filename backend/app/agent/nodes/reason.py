from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.llm import llm
from app.agent.state import AgentState

REASON_SYSTEM_PROMPT = """\
You are the reasoning step of a fitness coaching assistant - your output is an \
internal analysis, not shown directly to the user, that a later step will turn into \
the actual reply. Given the conversation and whatever context was gathered below, \
work out what a good answer needs to cover: relevant facts from the user's history \
(if provided), relevant expert guidance (if provided), and anything important that's \
still missing or should be asked about. Be concise - a short analysis, not a full \
response.
"""


def reason(state: AgentState) -> dict:
    context_parts = []
    if state.get("personal_context"):
        context_parts.append(f"User's personal history:\n{state['personal_context']}")
    if state.get("knowledge_context"):
        context_parts.append(f"Relevant expert reference material:\n{state['knowledge_context']}")
    context_block = (
        "\n\n".join(context_parts) if context_parts else "No additional context was retrieved."
    )

    prompt = [
        SystemMessage(REASON_SYSTEM_PROMPT),
        *state["messages"],
        HumanMessage(f"[Context gathered for this question]\n{context_block}"),
    ]

    result = llm.invoke(prompt)
    return {"analysis": result.content}
