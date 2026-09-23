from app.evals.models import EvalResult


def print_report(results: list[EvalResult]) -> bool:
    """Prints a pass/fail table grouped by suite, with the expected-vs-actual
    detail for every failure. Returns True iff every case passed."""
    all_passed = True
    current_suite = None

    for r in results:
        if r.suite != current_suite:
            current_suite = r.suite
            print(f"\n== {current_suite} ==")
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.case_id}: {r.description}")
        if not r.passed:
            print(f"       {r.detail}")
            all_passed = False

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    print(f"\n{passed}/{total} eval cases passed.")
    return all_passed
