# create-service

## Purpose
Create a service layer that isolates infrastructure concerns (database access, external API calls, file I/O) behind a stable interface, keeping business logic in tools and orchestration in agents.

## When to Use
- Replacing in-memory data stores (`app/data/stores.py`) with a database or external API
- Wrapping an external service (nutrition API, recipe database, pricing service) behind an interface
- Extracting infrastructure code from tools so tools remain pure business logic
- Adding a new data backend that needs to be swappable without changing agent or tool code

## Prerequisites
- The interface (methods, inputs, outputs) is defined before any implementation
- `rules/architecture.md` has been reviewed — services must not contain business logic
- A dependency injection pattern is chosen (constructor injection via factory parameters)

## Inputs
- Service name and responsibility
- Method signatures (inputs, outputs, error conditions)
- Backend technology (SQLite, PostgreSQL, GCS, REST API, etc.)
- Configuration environment variables needed

## Expected Outputs
- Abstract interface/Protocol class defining the service contract
- Concrete implementation class
- Factory function or DI registration
- Updated agent or tool factories to accept the injected service
- Unit tests with mock implementation
- Integration tests against the real backend

## Step-by-Step Workflow

1. **Define interface**: Create an abstract base class or `Protocol` in `app/services/<name>.py` (or appropriate location) defining the service contract. All methods should accept and return plain Python types or Pydantic models — never framework-specific types.

2. **Implement concrete class**: Create a concrete implementation in the same file or `app/services/<name>_impl.py`. The implementation handles infrastructure concerns: connection pooling, retry, error mapping, serialization. Follow `rules/security.md` for credential handling.

3. **Create factory / DI registration**: Add a factory function in `app/app_utils/services.py` (for session/artifact services) or in a new `app/services/__init__.py`. The factory reads environment variables to decide which implementation to return, falling back to in-memory when config is absent. Follow the pattern in `app/app_utils/services.py` (`get_session_service()`, `get_artifact_service()`).

4. **Inject into consumers**: Modify agent factory functions or tool functions to accept the service as a parameter:
   - For agents: pass the service during construction in `app/agent.py`
   - For tools: pass via closure or partial application

5. **Create unit tests**: Create `tests/unit/test_<service>.py` with a mock implementation of the interface. Verify the service contract is correctly used by consumers.

6. **Create integration tests**: Create `tests/integration/test_<service>.py` against the real backend (using test fixtures or test databases). Do not depend on production credentials.

## Files to Create or Modify

| Action | File |
|--------|------|
| Create | `app/services/<name>.py` — interface + implementation |
| Modify | `app/app_utils/services.py` — factory function (if session/artifact service) |
| Modify | `app/agent.py` — inject service into agent factories |
| Modify | `app/tools/<tool>.py` — accept service as parameter (if applicable) |
| Modify | `.env.example` — new configuration variables |
| Create | `tests/unit/test_<service>.py` |
| Create | `tests/integration/test_<service>.py` |

## Validation Checklist
- [ ] Interface contains no business logic — only infrastructure abstractions
- [ ] In-memory fallback works when no configuration is set
- [ ] All credentials read from environment variables, never hardcoded
- [ ] Concrete implementation handles connection errors, timeouts, and retries
- [ ] All methods return plain Python types or Pydantic models
- [ ] `uv run pytest tests/unit` passes with mock implementation
- [ ] `uv run pytest tests/integration` passes against test backend
- [ ] `agents-cli lint` passes

## Common Mistakes
- Putting business logic in the service layer (belongs in tools)
- Making the interface too specific to one backend (defeats swappability)
- Hardcoding connection strings or credentials
- Not providing an in-memory fallback for local development and tests
- Throwing framework-specific exceptions (raise custom exceptions instead)
- Forgetting that services are injected — agents should not import concrete implementations

## Related Rules
- `rules/architecture.md` — layering, dependency injection, separation of concerns
- `rules/security.md` — credentials from environment variables, secret handling
- `rules/coding.md` — type annotations, Pydantic models for method parameters
- `rules/testing.md` — mock patterns, integration test prerequisites

## Example Usage

```python
# Input: Replace RECIPES in-memory dict with a PostgreSQL database
# Service: RecipeService
# Methods: list_all(), search_by_ingredients(ingredients), get_by_id(id)

# Output: app/services/recipe_service.py
from abc import ABC, abstractmethod

class RecipeService(ABC):
    @abstractmethod
    def search_by_ingredients(self, ingredients: list[str]) -> list[dict]: ...

class PostgresRecipeService(RecipeService):
    def __init__(self, connection_string: str):
        self._conn = ...
    def search_by_ingredients(self, ingredients: list[str]) -> list[dict]:
        # SQL query, not business logic
        ...

class InMemoryRecipeService(RecipeService):
    def __init__(self):
        self._recipes = RECIPES
    def search_by_ingredients(self, ingredients: list[str]) -> list[dict]:
        return [r for r in self._recipes.values() if ...]
```
