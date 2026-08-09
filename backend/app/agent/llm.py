"""Shared LangChain chat model for the agent graph.

Sprint 3 called Ollama directly via httpx to see the raw request/response shape.
The agent graph uses LangChain's ChatOllama instead, because LangGraph's idiomatic
patterns - structured output (.with_structured_output()), message types
(HumanMessage/SystemMessage/AIMessage) - are built around LangChain's chat model
interface. app/llm/ollama_client.py's raw functions are still used directly for
embeddings (via the RAG retriever) and remain as-is for /rag/search.
"""

from langchain_ollama import ChatOllama

from app.core.config import settings

llm = ChatOllama(model=settings.ollama_model, base_url=settings.ollama_base_url, temperature=0)
