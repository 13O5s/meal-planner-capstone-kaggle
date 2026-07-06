# refactor

## Purpose
Restructure existing code to reduce duplication, improve modularity, and align with project architecture — without changing external behavior.

## When to Use
- Lint or type-checking issues accumulate and need systematic cleanup
- Code duplication is detected across tools, agents, or services
- A component has grown too large and needs splitting into smaller units
- Type annotations need modernization (e.g., `Optional[str]` → `str | None`)
- Architecture drift is detected (e.g., business logic in instructions instead of tools)

## Prerequisites
- A passing test suite exists to verify behavior preservation
- `agents-cli lint` has been run to establish a baseline
- `rules/coding.md`, `rules/architecture.md`, and `rules/agents.md` have been reviewed for target standards

## Inputs
- Scope: specific files or entire project
- Refactor types: lint fixes, type modernization, deduplication, modularity, architecture compliance
- Behavioral constraints: any aspects that must absolutely not change

## Expected Outputs
- Clean `agents-cli lint` — all four checks passing
- Reduced code duplication (shared logic extracted)
- Improved modularity (large files split, responsibilities separated)
- Modernized type annotations project-wide
- All existing tests still pass with no modifications to test assertions
- Architecture compliance verified against `rules/architecture.md`

## Step-by-Step Workflow

1. **Baseline**: Run `agents-cli lint` and record current state. Run `uv run pytest tests/unit tests/integration` to confirm a passing baseline.

2. **Auto-fix lint**: Run `uv run ruff check --fix .` then `uv run ruff format .` to fix auto-fixable issues (unused imports, import sorting, formatting).

3. **Modernize type annotations**: Replace all deprecated typing patterns project-wide:
   - `List[X]` → `list[X]`
   - `Dict[X, Y]` → `dict[X, Y]`
   - `Optional[X]` → `X | None`
   - `Tuple[X, Y]` → `tuple[X, Y]`
   - Remove `from typing import List, Dict, Optional, Tuple` lines where they become unused

4. **Remove dead code**: Delete unused imports, unused functions, dead code paths. Verify removal with `ruff check`.

5. **Reduce duplication**: Identify repeated patterns across files:
   - Extract shared logic into a new tool or utility function
   - Move repeated session state patterns into helpers
   - Factor out common validation logic

6. **Improve modularity**: Split large files (>200 lines) into focused modules:
   - Move Pydantic models to `app/models/schemas.py`
   - Move data lookups to `app/data/stores.py`
   - Move infrastructure code to service layer
   - Verify no circular imports introduced

7. **Verify architecture compliance**: Check against `rules/architecture.md`:
   - No business logic in agent instruction strings
   - Tools are stateless functions, not classes
   - Session state is the only inter-agent communication
   - Tools imported as function references, not modules

8. **Update tests**: If the refactor changed import paths or function signatures, update tests to match. Do not change test assertions — behavior must be preserved.

9. **Final validation**: Run `agents-cli lint` then `uv run pytest tests/unit tests/integration`. Both must pass with the same results as the baseline.

## Files to Create or Modify

| Action | File |
|--------|------|
| Modify | Any files with lint/type issues |
| Create | New files if splitting existing modules |
| Modify | Tests that reference refactored import paths |

## Validation Checklist
- [ ] `agents-cli lint` passes all four checks (ruff check, ruff format, codespell, ty)
- [ ] All existing tests pass without assertion modifications
- [ ] No behavioral changes introduced
- [ ] All deprecated typing imports removed project-wide
- [ ] No unused imports or dead code remain
- [ ] Architecture compliance verified against `rules/architecture.md`
- [ ] No circular imports introduced
- [ ] Agent instructions remain declarative (no migrated business logic)

## Common Mistakes
- Introducing behavioral changes during refactoring (fix bugs in separate commits)
- Removing imports that are still needed by other parts of the codebase
- Forgetting to run `ruff format` after `ruff check --fix` (format can reintroduce style issues)
- Splitting modules without checking for circular imports
- Changing test assertions to match refactored output (should match original output)
- Making agent instructions more complex during cleanup (keep them declarative)

## Related Rules
- `rules/coding.md` — type annotations, import order, style guide
- `rules/architecture.md` — layering, tool patterns, session state rules
- `rules/agents.md` — agent instruction standards
- `rules/testing.md` — test preservation during refactoring
- `rules/workflow.md` — development order (lint → test → deploy)

## Example Usage

```bash
# Input: refactor entire project for type modernization
# Scope: app/agent.py, app/models/schemas.py, app/data/stores.py,
#        app/tools/*.py, app/agents/*.py
# Types: List[x] → list[x], Optional[x] → x | None, Dict[x,y] → dict[x,y]

# Workflow:
1. uv run ruff check --fix .
2. uv run ruff format .
3. Manually review each file for remaining deprecated typing imports
4. Remove unused `from typing import ...` lines
5. uv run ruff check --fix .   # catch any missed removals
6. uv run pytest tests/unit tests/integration
7. agents-cli lint

# Output: clean lint, modern types, passing tests
```
