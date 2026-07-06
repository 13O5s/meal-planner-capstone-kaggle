# Tool Template: `<tool_name>`

## Purpose
<!-- Describe what this tool does in one sentence. -->

## Location
`app/tools/<tool_name>.py`

## Implementation

```python
# from app.data.stores import <DATA_STORE>
# from app.models.schemas import <Schema>


def <tool_function>(<param1>: <type>, <param2>: <type>) -> dict:
    """<One-line description>.

    <Detailed description of what the tool does.

    Args:
        <param1>: <description>
        <param2>: <description>

    Returns:
        A dict with <key1>, <key2> keys.
    """
    # Implementation here
    result = {
        "key1": value1,
        "key2": value2,
    }
    return result
```

## Registration

In the agent file (`app/agents/<agent_name>.py`):

```python
from app.tools.<tool_name> import <tool_function>

Agent(
    ...,
    tools=[<tool_function>],
)
```

## Validation

- [ ] Complete docstring with Args and Returns sections
- [ ] Type annotations use modern syntax (`list[str]`, `str | None`, not `List[str]`, `Optional[str]`)
- [ ] Returns JSON-serializable types (Pydantic models exported via `.model_dump()`)
- [ ] No side effects beyond reading data stores
- [ ] Imported as function reference, not module
- [ ] `agents-cli lint` passes

## Reference
- `rules/coding.md` — type annotation and style standards
- `rules/architecture.md` — tool import conventions
- `app/tools/calculate_nutrition.py` — example tool
