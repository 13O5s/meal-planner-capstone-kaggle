# create-workflow

## Purpose
Define a new multi-step orchestration workflow that coordinates multiple agents in a deterministic sequence, with validation checkpoints, retry behavior, and testable execution.

## When to Use
- Adding an alternative execution path different from the default 6-step pipeline
- Creating a specialized workflow (e.g., "quick meal plan" that skips inventory)
- Orchestrating external services alongside agent steps

## Prerequisites
- The agent sequence and session state contract between steps are designed
- Each participating agent already exists or is being created alongside the workflow
- `rules/architecture.md` and `rules/agents.md` have been reviewed

## Inputs
- Workflow name (snake_case)
- Ordered list of agents/steps in the sequence
- Session state keys each step reads and writes
- Validation checkpoint conditions per step (what must be true before proceeding)
- Retry configuration (max retries per step, backoff strategy)
- Error handling policy (abort vs skip vs retry)

## Expected Outputs
- Updated coordinator `instruction` or new root agent in `app/agent.py`
- Step registration with validation checkpoints
- Retry logic configuration
- Session state contract documented in `rules/domain.md`
- Integration test verifying deterministic execution

## Step-by-Step Workflow

1. **Define step sequence**: List the agents in execution order. For each step, document:
   - Preconditions: session state keys that must exist before the step runs
   - Postconditions: session state keys the step produces
   - Validation checkpoint: a condition to verify (e.g., "meal_plan total calories within 10% of target")

2. **Choose coordination pattern**:
   - **Option A — Coordinator instruction**: Update the existing root agent's `instruction` to describe the new workflow as an alternative path. Best when the workflow is a variation of the default pipeline.
   - **Option B — Separate root agent**: Create a new `Agent(...)` in `app/agent.py` with its own instruction and `sub_agents`. Best when the workflow is fundamentally different.

3. **Implement validation checkpoints**: For each step, add validation logic either in the agent's instruction ("verify X before proceeding") or as a separate tool. Checkpoints must be deterministic — same input always produces same pass/fail.

4. **Define retry behavior**: Configure retry for each step:
   - `max_retries`: number of retry attempts (default 2)
   - `backoff`: exponential backoff or fixed delay
   - `retry_on`: which errors trigger retry (timeout, validation failure, etc.)
   - Record retry count in session state to detect infinite loops

5. **Implement error handling**: Define per-step error handling:
   - `abort` — stop the entire workflow
   - `skip` — continue to next step
   - `retry` — retry the step up to max_retries
   - `fallback` — execute an alternative step

6. **Document session state contract**: Add all new session state keys to `rules/domain.md`.

7. **Create integration test**: Create `tests/integration/test_<workflow>.py` that runs the workflow with known inputs and asserts:
   - All steps executed in correct order
   - Session state keys populated at expected checkpoints
   - Retry behavior triggers correctly on failure
   - Error handling works (abort/skip/fallback)

## Files to Create or Modify

| Action | File |
|--------|------|
| Modify | `app/agent.py` — updated coordinator instruction or new root agent |
| Modify | `rules/domain.md` — new workflow's session state contract |
| Create | `tests/integration/test_<workflow>.py` |

## Validation Checklist
- [ ] Step sequence is documented in the coordinating agent's instruction
- [ ] Each step's preconditions and postconditions are clearly defined
- [ ] Validation checkpoints are deterministic (same input → same outcome)
- [ ] Retry configuration prevents infinite loops (max_retries set, retry count tracked)
- [ ] No circular dependencies between steps
- [ ] Error handling is defined for every step (not just the happy path)
- [ ] Session state keys are documented in `rules/domain.md`
- [ ] `agents-cli lint` passes
- [ ] `uv run pytest tests/integration/test_<workflow>.py` passes

## Common Mistakes
- Creating circular step dependencies (step A needs B's output, B needs A's output)
- Validation checkpoints that depend on LLM non-determinism (always use tools)
- Not setting max_retries — endless retry loops on persistent failures
- Omitting error handling for steps that can fail
- Making agent instructions too long — split into sub-agents instead
- Forgetting to document new session state keys in `rules/domain.md`

## Related Rules
- `rules/architecture.md` — coordination patterns, session state conventions
- `rules/agents.md` — agent definition, instruction format, sub_agents
- `rules/domain.md` — session state contract documentation
- `rules/testing.md` — integration test patterns

## Example Usage

```bash
# Input: "quick_plan" workflow — skips inventory step
# Sequence: Profile → Recipe → Meal Plan → Nutrition → Shopping
# (omits Inventory)
# Retry: meal_plan step retries up to 3 times on validation failure
# Error: if profile step fails, abort entire workflow

# Output:
# - app/agent.py — new root agent "quick_plan_coordinator"
# - rules/domain.md — documents any new session state keys
# - tests/integration/test_quick_plan.py
```
