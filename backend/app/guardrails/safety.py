"""Deterministic, LLM-free input screening.

Two categories of message get short-circuited before they ever reach the agent
graph's first LLM call:

1. Safety red flags - symptoms (chest pain, fainting, uncontrolled bleeding, a
   possible fracture) that need an unconditional "stop and get real medical help"
   response, not advice a model could phrase as a hedge or a suggestion.
2. Prompt injection - attempts to override the assistant's behavior or extract its
   system prompt ("ignore previous instructions", "you are now...").

Both are deliberately regex-based rather than an LLM classification step. A red-flag
symptom needs a response that's *always* right, not one that's right whenever the
model correctly weighs the instructions - and both categories are also cheap and
fast to check this way, so there's no reason to spend an LLM call (or risk one being
talked out of the right answer) on them. See EVALS_AND_GUARDRAILS.md for why this is
one of two guardrail layers, not the only one.
"""

import re
from dataclasses import dataclass

# Each entry is (pattern, human-readable label for logging/eval detail). Patterns
# are intentionally narrow and symptom-specific - broad matches like "pain" would
# false-positive on completely normal soreness questions ("my legs are sore").
RED_FLAG_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"chest pain|tightness in (my |the )?chest", re.I), "possible cardiac symptom"),
    (
        re.compile(r"can'?t breathe|difficulty breathing|shortness of breath", re.I),
        "breathing difficulty",
    ),
    (
        re.compile(r"(passed out|fainted|blacked out|loss of consciousness)", re.I),
        "loss of consciousness",
    ),
    (
        re.compile(r"numbness (is |that('s| is) )?spreading|spreading numbness", re.I),
        "spreading numbness",
    ),
    (
        re.compile(
            r"(bone (is )?(sticking|poking) out|visible deformity|can'?t bear (any )?weight at all)",
            re.I,
        ),
        "possible fracture",
    ),
    (
        re.compile(r"(won'?t stop bleeding|heavy bleeding|uncontrolled bleeding)", re.I),
        "uncontrolled bleeding",
    ),
]

INJECTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        # e.g. "ignore all previous instructions", "ignore your instructions" -
        # allow a short run of words between the verb and the noun rather than
        # requiring an exact phrase, since real injection attempts stack qualifiers.
        re.compile(r"ignore\s+(?:\w+\s+){0,3}instructions", re.I),
        "instruction override attempt",
    ),
    (
        re.compile(r"disregard (your|the) (system )?prompt", re.I),
        "instruction override attempt",
    ),
    (
        re.compile(
            r"reveal your (system )?prompt|print your instructions|what (is|are) your (system )?(prompt|instructions)",
            re.I,
        ),
        "prompt exfiltration attempt",
    ),
    (
        re.compile(r"you are now (a|an)|forget you('re| are) a fitness coach", re.I),
        "role override attempt",
    ),
]

SAFETY_MESSAGE = (
    "What you're describing sounds like it could be a medical emergency, not "
    "something a fitness coach should advise on. Please stop exercising and "
    "contact emergency services or a medical professional right away rather than "
    "waiting on advice here."
)

INJECTION_MESSAGE = (
    "I'm a fitness coaching assistant, so I can't follow instructions that try to "
    "change how I behave or reveal internal configuration - happy to help with "
    "training, recovery, or programming questions though."
)


@dataclass
class InputScreenResult:
    blocked: bool
    category: str | None  # "safety_red_flag" | "prompt_injection" | None
    label: str | None  # which specific pattern matched, for logging/eval detail
    message: str | None  # fixed response to return to the user, if blocked


def screen_input(text: str) -> InputScreenResult:
    for pattern, label in RED_FLAG_PATTERNS:
        if pattern.search(text):
            return InputScreenResult(
                blocked=True, category="safety_red_flag", label=label, message=SAFETY_MESSAGE
            )

    for pattern, label in INJECTION_PATTERNS:
        if pattern.search(text):
            return InputScreenResult(
                blocked=True, category="prompt_injection", label=label, message=INJECTION_MESSAGE
            )

    return InputScreenResult(blocked=False, category=None, label=None, message=None)
