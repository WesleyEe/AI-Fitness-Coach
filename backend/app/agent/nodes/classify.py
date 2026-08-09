from pydantic import BaseModel, Field

from app.agent.llm import llm
from app.agent.state import AgentState

CLASSIFY_SYSTEM_PROMPT = """\
You are the intent-analysis step of a fitness coaching assistant. Given the user's \
latest message, decide what information would help answer it well:

- needs_personal_data: true if answering well requires knowing the user's own \
workout history, injury history, or recent training - e.g. "why am I not \
improving", "is my ankle ready for running again", questions referencing "my" \
recent training.
- needs_expert_knowledge: true if answering well benefits from expert reference \
material on training methodology, programming, or injury prevention/rehab \
principles - e.g. specific "how do I improve X" or "what should I do for Y" \
questions about football, Hyrox, bodybuilding, or injury recovery.

A question can need both, one, or neither (e.g. a greeting or a question fully \
answerable from the conversation itself needs neither).
"""


class IntentClassification(BaseModel):
    needs_personal_data: bool = Field(
        description="True if answering requires the user's workout/injury history"
    )
    needs_expert_knowledge: bool = Field(
        description="True if answering benefits from expert fitness reference material"
    )
    reasoning: str = Field(description="One short sentence explaining the decision")


def classify_intent(state: AgentState) -> dict:
    latest_user_message = next(
        (m.content for m in reversed(state["messages"]) if m.type == "human"), ""
    )

    structured_llm = llm.with_structured_output(IntentClassification)
    result: IntentClassification = structured_llm.invoke(
        [("system", CLASSIFY_SYSTEM_PROMPT), ("human", latest_user_message)]
    )

    return {
        "needs_personal_data": result.needs_personal_data,
        "needs_expert_knowledge": result.needs_expert_knowledge,
        "classification_reasoning": result.reasoning,
    }
