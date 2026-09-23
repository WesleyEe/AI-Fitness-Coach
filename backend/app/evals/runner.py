from app.evals.models import EvalResult
from app.evals.suites import grounding_suite, guardrails_suite, routing_suite

# Registry of suite name -> its run() function. Add a new suite by writing
# app/evals/suites/<name>_suite.py with a `def run() -> list[EvalResult]` and
# registering it here - see EVALS_AND_GUARDRAILS.md for the full walkthrough.
SUITES = {
    "guardrails": guardrails_suite.run,
    "routing": routing_suite.run,
    "grounding": grounding_suite.run,
}


def run_suites(names: list[str] | None = None) -> list[EvalResult]:
    """Runs the given suites (all of them if names is None) and returns every
    case's result, in suite-registration order."""
    names = names or list(SUITES)
    results: list[EvalResult] = []
    for name in names:
        results.extend(SUITES[name]())
    return results
