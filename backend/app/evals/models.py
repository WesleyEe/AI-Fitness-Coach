from dataclasses import dataclass


@dataclass
class EvalResult:
    """One eval case's outcome. Deliberately not a pass/fail bool alone -
    `detail` always carries what was expected vs. what actually happened, since
    that's what you actually need when a case fails against a real model (the
    failure is data about model behavior, not a stack trace to debug)."""

    suite: str
    case_id: str
    description: str
    passed: bool
    detail: str
