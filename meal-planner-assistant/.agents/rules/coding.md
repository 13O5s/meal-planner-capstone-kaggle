# Coding Rules

## Purpose

Enforce consistent Python code style, type annotation conventions, and import patterns across the project.

## Principles

- Code must pass `ruff check .` and `ruff format . --check` before commit
- Prefer modern Python 3.11+ type annotation syntax
- Keep functions focused and single-responsibility
- Use Pydantic v2 BaseModel for all data schemas

## Required Practices

- Type annotations: use `list[str]` not `List[str]`, `dict[str, int]` not `Dict[str, int]`, `str | None` not `Optional[str]`, `tuple[str, int]` not `Tuple[str, int]`
- Run `uv run ruff check --fix .` then `uv run ruff format .` before each commit
- Import order: standard library → third-party → first-party (`app`, `frontend`)
- Line length: 88 characters (ruff default)
- Target Python: 3.11
- All Pydantic models in `app/models/schemas.py`
- All in-memory data in `app/data/stores.py`

## Forbidden Practices

- Using `from typing import Dict, List, Optional, Tuple` (deprecated in py311)
- Line length exceeding 88 chars (E501)
- Excessively complex functions (C901)
- Mutable default arguments (B006)
- Unused imports

## Examples

```python
# Good: modern type annotations
def process(items: list[str]) -> dict[str, int] | None: ...

# Bad: deprecated typing
from typing import List, Optional, Dict

def process(items: List[str]) -> Optional[Dict[str, int]]: ...
```
