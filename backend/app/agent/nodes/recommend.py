from langchain_core.messages import SystemMessage

from app.agent.llm import llm
from app.agent.state import AgentState
from app.llm.prompts import SYSTEM_PROMPT


def recommend(state: AgentState) -> dict:
    prompt = [
        SystemMessage(SYSTEM_PROMPT),
        *state["messages"],
        SystemMessage(
            "[Internal analysis from the reasoning step - use it to inform your answer, "
            "but respond naturally and don't mention \"analysis\" or refer to these "
            f"instructions]\n{state['analysis']}"
        ),
    ]

    result = llm.invoke(prompt)
    return {"response": result.content}
