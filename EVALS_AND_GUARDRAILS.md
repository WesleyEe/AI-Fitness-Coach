# Evals & Guardrails

Why this exists, what it actually does, and how to run and extend it. If you're
new to either term: **guardrails** run at request time and change what the app
does; **evals** run offline and measure how well it's doing. This doc covers both,
plus how they relate to the pytest suite that already existed.

## Motivation: a real, observed failure

[PLAN.md](PLAN.md)'s Sprint 6 section documents a genuine finding from manually
inspecting this agent's intermediate state, not a hypothetical one:

> After seeding an injury with `status: recovered` and no restrictions, the
> model's `analysis` confidently stated status `"recovering"` and a `"no running
> yet"` restriction — both fabricated, present nowhere in the actual
> `personal_context` it was given.

Read that again: retrieval was correct, the DB query was correct, the prompt was
correct — and the model still stated a specific, plausible, wrong fact with no
signal anything had gone wrong. `reason`'s structured output (`ReasoningResult`)
constrains the *shape* of the response — valid JSON matching the schema — but
never checked whether its *content* was actually true relative to what it was
given. That gap is exactly what this harness closes, and it's also the answer to
a broader question every LLM feature eventually raises: **how do you know the
model is behaving the way the prompt says it should?** You don't, by default —
prompts are requests, not guarantees. You have to build something that checks.

PLAN.md's Sprint 6 "possible future improvements" named the fix directly: *"a
fact-checking/verification node that cross-references specific claims in
`analysis` against `personal_context`/`knowledge_context` before they reach
`recommend`."* This harness builds that node, plus a second, cheaper layer of
protection, plus a way to measure both against the real model over time instead
of trusting them once and forgetting about it.

## Two different problems, two different kinds of guardrail

This project now has two runtime guardrail nodes in the agent graph
([app/agent/graph.py](backend/app/agent/graph.py)), and they're deliberately
built two completely different ways, because they're solving two completely
different problems:

| | `input_guardrail` | `verify_grounding` |
|---|---|---|
| **Runs** | First node, before `classify_intent` | After `reason`, before `recommend`/`ask_clarification` |
| **Checks** | The user's raw message | The model's own `analysis`, against retrieved context |
| **Implementation** | Regex, in [app/guardrails/safety.py](backend/app/guardrails/safety.py) | A second, narrow LLM call, in [app/guardrails/grounding.py](backend/app/guardrails/grounding.py) |
| **Why that implementation** | Needs to be *unconditionally* right — a chest-pain message can't get a hedged or "creatively reinterpreted" response depending on how an LLM weighs the system prompt that day | The thing being checked (a written claim vs. a source text) is itself a language-understanding task — regex can't tell "recovering" contradicts "recovered" |
| **Deterministic?** | Yes — same input, same output, always | No — a different call can still miss a fabrication |
| **Measured by** | `app/evals/suites/guardrails_suite.py` (and pytest, since it's deterministic — see below) | `app/evals/suites/grounding_suite.py` (needs a real eval — see below) |

This split is the main thing worth internalizing: **a deterministic guardrail is
something you can unit-test and trust completely; a model-based guardrail is
something you can only ever measure, because it's making the same kind of
judgment call as the thing it's checking.** Don't reach for an LLM call when a
regex genuinely suffices (it's slower, costs money/latency against a hosted
model, and adds its own failure mode) — and don't expect a regex to catch
something that requires actually understanding two pieces of text.

### `input_guardrail` — deterministic, first

Two categories, both short-circuiting straight to a fixed response before
`classify_intent` (or any other LLM call) ever runs:

- **Safety red flags** — chest pain, fainting, spreading numbness, a possible
  fracture, uncontrolled bleeding. These get an unconditional "stop and get real
  medical help" response. A fitness coach chatbot should never be in the business
  of triaging these, however well-intentioned its prompt is.
- **Prompt injection** — "ignore previous instructions", "reveal your system
  prompt", "you are now a general assistant". These get a fixed boundary-setting
  response instead of reaching the model at all.

Both live in [app/guardrails/safety.py](backend/app/guardrails/safety.py) as
plain regex lists, checked in
[app/agent/nodes/input_guardrail.py](backend/app/agent/nodes/input_guardrail.py).
The routing edge (`_route_after_input_guardrail` in
[app/agent/graph.py](backend/app/agent/graph.py)) sends a blocked message
straight to `END`, skipping the entire rest of the graph — no wasted LLM calls on
a message that isn't going to get a normal answer anyway.

### `verify_grounding` — probabilistic, second

Runs only when `personal_context` was gathered (that's the only place the
Sprint 6 failure was observed), and only when `reason` hasn't already decided to
ask for clarification for some other reason. It sends `reason`'s `analysis`
alongside the raw `personal_context` to a second LLM call
([`check_grounding`](backend/app/guardrails/grounding.py)) whose *only* job is:
does every specific personal-history claim in this analysis actually appear in
this source text? If not, `verify_grounding` overrides the routing decision —
`needs_clarification` becomes `True`, and the user gets a "let me double-check
something" question instead of a confidently wrong recommendation. See
[app/agent/nodes/verify_grounding.py](backend/app/agent/nodes/verify_grounding.py).

This is the same "ask rather than guess" pattern `reason` already uses for
missing information — just triggered by a *fact-check failing* instead of a
*fact being absent*.

## The updated graph

```
START → input_guardrail ─┬─(blocked)──────────────────────────────────► END
                          └─(not blocked)
                             ↓
                        classify_intent → [conditional] → fetch_context → reason
                                        ↘ nothing needed ─────────────────↗
                                                                           ↓
                                                                  verify_grounding
                                                                           ↓
                                                                    [conditional]
                                                          ┌────────────────┴───────────────┐
                                                needs_clarification=True           needs_clarification=False
                                                          ↓                                 ↓
                                                ask_clarification → END          recommend → END
```

`verify_grounding` can itself flip `needs_clarification` to `True` — that's the
whole point of putting it before the existing conditional edge rather than giving
it a separate one.

## Evals: measuring what guardrails alone can't guarantee

A guardrail changes behavior *right now*, for one request. It doesn't tell you
whether that behavior is actually any good, on average, against the real model —
and `verify_grounding` in particular can't be trusted just because it's *there*;
a second LLM call is not a proof, it's a mitigation with its own (hopefully
lower) failure rate. That's what the eval harness in
[backend/app/evals/](backend/app/evals/) is for.

### How this differs from the existing pytest suite

The backend already had 50+ pytest tests before this. They mock the LLM
(`mocker.patch(..., fake_llm)`) specifically so they're fast, deterministic, and
test *plumbing*: does `reason()` correctly map a given structured result into
state? Does the graph route to `ask_clarification` when told to? Those questions
have a right answer that doesn't depend on what a real model actually says on a
given day, so mocking is the correct choice for them — see
[tests/test_agent_reason.py](backend/tests/test_agent_reason.py) for the pattern.

Evals ask a different question: **given the real, currently-configured model,
does it actually behave the way we want on realistic inputs?** That's not a
plumbing question, and mocking it away would just prove your mock behaves how you
told it to — the whole point is to remove the mock. This is also why evals are
**not** part of `pytest` and don't run in CI the way the unit suite does: they're
slower, they need Ollama running with the real model pulled, and — this is the
important part, not just a caveat — **they are not deterministic.** A case can
legitimately fail on Tuesday and pass on Wednesday with no code change, because
the model's output varies. Treat a single eval failure as a data point about
model behavior, not a build-breaking bug; treat a *trend* (a case that keeps
failing, or a suite whose pass rate is dropping) as something to actually act on
— reword a prompt, swap the model, or tighten a guardrail.

|  | pytest (`backend/tests/`) | evals (`backend/app/evals/`) |
|---|---|---|
| Question asked | Is the code correct? | Is the model's behavior good enough? |
| LLM calls | Mocked | Real (needs Ollama running) |
| Deterministic | Yes | No |
| Run when | Every change, in CI | Manually, or nightly — before/after a prompt or model change |
| A failure means | A bug — fix the code | A model limitation or a prompt gap — investigate, maybe adjust the prompt/guardrail |

### The suites

Run everything with:

```bash
cd backend
uv run python -m app.evals.run_evals
```

Or one suite at a time with `--suite` (repeatable):

```bash
uv run python -m app.evals.run_evals --suite grounding
```

Requires Ollama running locally with the configured model pulled (see
[DEPLOYMENT.md](DEPLOYMENT.md)) — `routing` and `grounding` make real calls.

- **`guardrails`** ([suites/guardrails_suite.py](backend/app/evals/suites/guardrails_suite.py))
  — deterministic, no LLM. Included mainly as the simplest possible example of an
  eval case (fixed input → fixed expected output) before the other two suites
  show what changes once a real model is involved. Overlaps with
  `tests/test_guardrails_safety.py` on purpose — this part of the system is
  cheap enough to check both ways.
- **`routing`** ([suites/routing_suite.py](backend/app/evals/suites/routing_suite.py))
  — calls the real `classify_intent` node on a handful of realistic messages
  (a greeting, a personal-history question, an expert-knowledge question, one
  needing both) and checks its `needs_personal_data`/`needs_expert_knowledge`
  decisions match what a person would expect. This is "does the model actually
  do what the routing prompt asks," not "does the graph route correctly given a
  decision" (that's what `tests/test_agent_routing.py` covers).
- **`grounding`** ([suites/grounding_suite.py](backend/app/evals/suites/grounding_suite.py))
  — the flagship suite. It reproduces the exact Sprint 6 scenario (a recovered
  injury, no restrictions) against the real `reason` node, then runs the real
  `check_grounding` guardrail on whatever it produced. **It passes if either the
  model didn't hallucinate this time, or it did and the guardrail caught it** —
  it only fails if a fabricated claim would have reached the user with nothing
  flagging it. That's the one outcome the whole harness exists to prevent, and
  it's checked at the system level (model + guardrail together), not by asserting
  the model never hallucinates — Sprint 6 already proved, empirically, that it
  sometimes does.

### Reading a report

```
== grounding ==
[PASS] recovered_injury_status_not_fabricated_as_recovering: My ankle is better, can I start running again?

3/3 eval cases passed.
```

A `[FAIL]` line prints its `detail` — what was expected vs. what actually
happened, including the model's raw output — right under it, so a failure is
something to read and reason about, not a stack trace to debug.

### Adding a new case

1. Pick the suite it belongs in (or add a new suite: write
   `app/evals/suites/<name>_suite.py` with a `def run() -> list[EvalResult]`,
   then register it in `SUITES` in
   [runner.py](backend/app/evals/runner.py)).
2. Add a `(case_id, ..., expected_...)` tuple to that suite's `CASES` list.
3. Run `uv run python -m app.evals.run_evals --suite <name>` and read the
   output.

The best source of new cases is exactly how the Sprint 6 case was found:
**manual verification that inspects intermediate agent state, not just the final
response.** When you notice a model behaving in a way that's subtly wrong, don't
just fix the prompt and move on — turn the exact scenario into an eval case, the
way `grounding_suite.py` does, so a regression shows up automatically instead of
needing to be rediscovered by hand next time.

## Possible future improvements (not now)

- **CI gating on a pass-rate threshold**, once there's enough historical data on
  a suite's normal pass rate to set a sane bar — right now, three eval suites
  with a handful of cases each isn't enough signal to gate merges on without
  flaking constantly.
- **An LLM-as-judge suite** for response *quality* (tone, specificity, actually
  answering the question) rather than the structural checks here (routing
  correctness, groundedness) — a genuinely different, harder kind of eval.
- **Extending `verify_grounding` to `knowledge_context`** (RAG-retrieved expert
  material), not just `personal_context` — the Sprint 6 finding was specifically
  about personal data, but nothing rules out the same failure mode against
  retrieved knowledge-base chunks.
- **A larger red-team corpus** for `input_guardrail` — the current pattern lists
  are a reasonable start, not an exhaustive safety review.
