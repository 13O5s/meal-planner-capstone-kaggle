# create-agent

## Purpose
Scaffold a new ADK sub-agent following the project's agent architecture, including its factory, prompts, models, registration, and tests.

## When to Use
- Adding a new domain responsibility to the meal planner assistant
- Splitting an existing agent into smaller focused agents
- Extending the coordinator's workflow with a new processing step

## Prerequisites
- Familiarity with the agent's domain responsibility and session state contract
- The coordinator's `instruction` prompt is understood so the new agent can be inserted in the correct sequence position
- `rules/agents.md` and `rules/architecture.md` have been reviewed

## Inputs
- Agent name (snake_case, e.g., `budget_optimizer`)
- One-line description of the agent's responsibility
- Session state keys it will read and write
- Tools it needs (imported function references)
- Where in the coordinator's 6-step sequence it fits

## Expected Outputs
- `app/agents/<name>.py` — factory function `create_<name>_agent()`
- `app/agents/<name>/prompts.py` — extracted instruction strings (optional, for long prompts)
- `app/agents/<name>/models.py` — agent-specific Pydantic models (optional)
- Updated `app/agent.py` — import, instantiation, sub_agents registration
- Updated coordinator `instruction` — new step inserted in workflow
- `tests/unit/test_<name>.py` — unit tests for agent logic
- `tests/integration/test_<name>.py` — integration test for agent in workflow

## Step-by-Step Workflow

1. **Create agent factory**: Create `app/agents/<name>.py` with a `create_<name>_agent()` function returning an `Agent` instance. Follow `rules/agents.md` for naming, description, and instruction requirements.

2. **Extract prompts** (optional): If the instruction string exceeds 50 lines, move it to `app/agents/<name>/prompts.py` as a module-level constant and import it in the factory.

3. **Extract models** (optional): If the agent needs schemas not in `app/models/schemas.py`, create `app/agents/<name>/models.py` with Pydantic `BaseModel` subclasses. Follow `rules/coding.md` for type annotations.

4. **Register in root agent**: In `app/agent.py`:
   - Import the factory: `from app.agents.<name> import create_<name>_agent`
   - Instantiate: `<name>_agent = create_<name>_agent()`
   - Add to `sub_agents=[..., <name>_agent]`

5. **Update coordinator instruction**: Insert the new agent's step in the coordinator's `instruction` string at the correct sequence position. Document what session state keys it reads and writes.

6. **Document session state contract**: If the agent introduces new session state keys, add them to `rules/domain.md` session state contract table.

7. **Create unit tests**: Create `tests/unit/test_<name>.py` covering the agent's tool invocations and session state logic. Mock all dependencies. Follow `rules/testing.md`.

8. **Create integration test**: Create `tests/integration/test_<name>.py` that runs the full workflow with the new agent, verifying session state propagation. Use `InMemorySessionService`. Follow `writing/integration-tests` skill.

## Files to Create or Modify

| Action | File |
|--------|------|
| Create | `app/agents/<name>.py` |
| Create | `app/agents/<name>/prompts.py` (if prompts extracted) |
| Create | `app/agents/<name>/models.py` (if custom models needed) |
| Modify | `app/agent.py` — import + instantiate + sub_agents |
| Modify | Coordinator's `instruction` string |
| Modify | `rules/domain.md` — new session state keys (if any) |
| Create | `tests/unit/test_<name>.py` |
| Create | `tests/integration/test_<name>.py` |

## Validation Checklist
- [ ] Agent has a unique `name` not shared by any other sub-agent
- [ ] `description` is a single sentence explaining responsibility
- [ ] `instruction` documents all session state keys read and written
- [ ] Tools are imported as function references, not modules
- [ ] Factory function is called in `app/agent.py` and result added to `sub_agents`
- [ ] Coordinator `instruction` includes the new step in correct sequence
- [ ] New session state keys (if any) documented in `rules/domain.md`
- [ ] `agents-cli lint` passes
- [ ] `uv run pytest tests/unit/test_<name>.py` passes
- [ ] `uv run pytest tests/integration/test_<name>.py` passes

## Common Mistakes
- Forgetting to register the agent in `sub_agents=[...]` after importing the factory
- Not updating the coordinator's instruction (agent exists but never gets invoked)
- Importing `app.tools.<module>` instead of `from app.tools.<module> import <function>`
- Putting business logic in the instruction string instead of a tool function
- Creating an agent that overlaps in responsibility with an existing sub-agent
- Omitting session state documentation in instructions, making the agent unusable by downstream agents

## Related Rules
- `rules/agents.md` — agent definition standards (name, description, instruction format)
- `rules/architecture.md` — wiring patterns, session state conventions, tool imports
- `rules/domain.md` — session state contract documentation, data store layout
- `rules/coding.md` — type annotations, imports, code style
- `rules/testing.md` — test organization, pytest conventions

## Example Usage

```bash
# Create inventory agent (existing reference)
Input:
  Agent name: "inventory"
  Description: "Normalizes and validates ingredients"
  Session state writes: available_ingredients, requested_ingredients
  Tools: [normalize_ingredients]
  Sequence position: 2 (after profile)

Output:
  - app/agents/inventory.py  # factory file
  - app/agent.py updated     # import + register
  - Coordinator instruction updated  # step 2 added
  - tests/unit/test_inventory.py
  - tests/integration/test_inventory.py
```
