from app.agent.state import AgentState


def ask_clarification(state: AgentState) -> dict:
    """Terminal node reached when `reason` decides it doesn't have enough to answer
    safely. Deliberately not an LLM call: `clarification_question` is already
    model-generated text from the reason step - this node is pure flow control,
    carrying it through to the response the user sees. Not every node in a graph
    needs to hit the model.
    """
    return {"response": state["clarification_question"]}
