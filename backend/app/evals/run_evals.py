"""CLI entry point for the eval suites.

These are deliberately NOT run as part of `pytest` - see EVALS_AND_GUARDRAILS.md
for why (they hit the real, non-deterministic local model and are slow relative
to the mocked unit suite). Run them explicitly, with Ollama running locally:

    uv run python -m app.evals.run_evals                 # every suite
    uv run python -m app.evals.run_evals --suite routing  # just one
"""

import argparse
import sys

from app.evals.report import print_report
from app.evals.runner import SUITES, run_suites


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the fitness-coach-ai eval suites against the real configured LLM."
    )
    parser.add_argument(
        "--suite",
        action="append",
        choices=sorted(SUITES),
        help="Run only this suite (repeatable). Default: run every suite.",
    )
    args = parser.parse_args()

    results = run_suites(args.suite)
    all_passed = print_report(results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
