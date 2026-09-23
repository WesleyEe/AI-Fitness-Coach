"""LLM-based groundedness ("faithfulness") checking.

This targets a specific, previously-observed failure documented in PLAN.md's
Sprint 6 writeup: with correct retrieval, correct DB queries, and correct
prompting, the local 3B model still wrote an `analysis` stating a specific injury
status and restriction that directly contradicted - and appeared nowhere in - the
`personal_context` it was actually given (seeded status "recovered", no
restrictions; model wrote "recovering" with a "no running yet" restriction).

Structured output (`.with_structured_output()`) only guarantees the *shape* of a
response is valid JSON matching a schema - it says nothing about whether the
content is faithful to the source material it was supposed to reason over. Catching
that requires an actual check, not a stricter schema. This module is that check: a
second, narrowly-scoped LLM call whose only job is comparing a piece of generated
text against its source and flagging anything the source doesn't support.

This is inherently probabilistic, not deterministic like app.guardrails.safety - a
different model call can still get it wrong. That's exactly why
app/evals/suites/grounding_suite.py exists: to measure, against the real model, how
often this check actually catches the fabrication it's meant to catch.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

GROUNDING_SYSTEM_PROMPT = """\
You are a fact-checking step, not the assistant itself. You will be shown a SOURCE \
DOCUMENT (the user's actual personal history, retrieved from the database) and a \
paragraph of ANALYSIS someone wrote about it. Your only job is to compare them.

Find every SPECIFIC factual claim in the ANALYSIS that is about the user's personal \
history - a status, a restriction, a date, a severity, a number, an injury detail. \
For each one, check whether it is explicitly supported by the SOURCE DOCUMENT. A \
claim is UNSUPPORTED if it states something more specific, more severe, more \
restrictive, or simply different from what the source says - including when the \
source doesn't mention it at all. General statements not tied to a specific fact \
(e.g. "training consistently helps recovery") don't count as claims to check.

Be strict: this check exists specifically because small local models have been \
observed stating a confident, plausible-sounding injury status or restriction that \
directly contradicts - or isn't present in - the source document they were given.
"""


class GroundingCheck(BaseModel):
    grounded: bool = Field(
        description="True only if every specific personal-history claim in the "
        "analysis is explicitly supported by the source document"
    )
    unsupported_claims: list[str] = Field(
        default_factory=list,
        description="Specific claims from the analysis that aren't supported by the "
        "source document, quoted or closely paraphrased. Empty if grounded is true.",
    )


def check_grounding(llm, analysis: str, source_context: str) -> GroundingCheck:
    structured_llm = llm.with_structured_output(GroundingCheck)
    return structured_llm.invoke(
        [
            SystemMessage(GROUNDING_SYSTEM_PROMPT),
            HumanMessage(f"[SOURCE DOCUMENT]\n{source_context}\n\n[ANALYSIS TO CHECK]\n{analysis}"),
        ]
    )
