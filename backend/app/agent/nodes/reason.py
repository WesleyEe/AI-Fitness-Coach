from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agent.llm import llm
from app.agent.state import AgentState

REASON_SYSTEM_PROMPT = """\
You are the reasoning step of a fitness coaching assistant. Your output is internal -
not shown directly to the user - a later step turns it into the actual reply.

Given the conversation and whatever context was gathered below:

1. Work out what a good answer needs to cover. Cite SPECIFIC facts from the gathered
   context rather than paraphrasing generically - exact dates, restrictions, severity,
   numbers (e.g. "their ankle sprain on 2026-07-20 has a 'no running yet' restriction
   and status 'recovering'", not just "they have an injury"). If both personal history
   and expert reference material were gathered, connect them explicitly - e.g. compare
   the user's injury status or training history against what the reference material
   says about return-to-sport criteria or programming, don't just summarize each in
   isolation.

2. Decide whether there's enough here to give a safe, confident, personalized answer,
   or whether a critical piece of information is missing and you should ask the user
   directly instead of guessing. IMPORTANT: if the gathered context explicitly says
   personal data is unavailable (e.g. "No user_id was provided" or "No workout or
   injury history found") AND the question is about returning to activity after an
   injury or is otherwise safety-sensitive, you MUST set needs_clarification to true
   rather than giving generic advice - do not proceed with a guessed answer in this
   case. Also ask rather than guess when the question depends on a specific detail
   (pain level, how long ago, what a professional advised) that isn't in the
   conversation or gathered context and would change the answer. Don't ask for
   clarification on questions that already have enough to go on - only when it's
   genuinely needed.
"""


class ReasoningResult(BaseModel):
    analysis: str = Field(description="Concise internal analysis citing specific gathered facts")
    needs_clarification: bool = Field(
        description="True if a critical piece of information is missing and the user "
        "should be asked directly rather than given a guessed answer"
    )
    clarification_question: str | None = Field(
        default=None,
        description="If needs_clarification is true, one natural, friendly question "
        "asking the user for exactly what's missing. Null otherwise.",
    )


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

    structured_llm = llm.with_structured_output(ReasoningResult)
    result: ReasoningResult = structured_llm.invoke(prompt)

    clarification_question = result.clarification_question
    if result.needs_clarification and not clarification_question:
        # Structured output constrains the *shape* of the response (valid JSON
        # matching the schema) but not full semantic compliance - a small local
        # model can set needs_clarification=true and still leave the dependent
        # field empty. Don't let that silently produce a blank response; fall
        # back to a generic ask rather than trust the LLM's output blindly here.
        clarification_question = (
            "I don't have enough information to answer that safely yet - could you "
            "tell me more about your situation (e.g. when this happened, and any "
            "guidance you've already been given)?"
        )

    return {
        "analysis": result.analysis,
        "needs_clarification": result.needs_clarification,
        "clarification_question": clarification_question,
    }
