# Architecture Rules

## Purpose

Define the project's structural patterns so that all agents, tools, and workflows follow a consistent, scalable architecture.

## Principles

- Single root coordinator agent delegates to specialized sub-agents via instruction prompts
- Session state is the sole communication channel between agents (no direct agent-to-agent calls)
- Tools are stateless Python functions imported as references, not modules
- Sub-agents are created via factory functions returning `Agent(...)` instances
- In-memory data stores are preferred until persistence is required

## Required Practices

- Root agent must list all sub-agents in `sub_agents=[...]`
- Coordinator's `instruction` prompt must define the sequential workflow
- Each sub-agent factory must live in `app/agents/<name>.py`
- Each tool must live in `app/tools/<name>.py`
- Session state keys must follow lowercase snake_case convention
- New sub-agents must be added to: factory file, `app/agent.py` import + instantiation + sub_agents list, and coordinator instruction

## Forbidden Practices

- Agents calling other agents directly (use session state instead)
- Hardcoding API keys or secrets in agent files
- Importing tools as modules (`import app.tools.foo`); always import the function
- Putting business logic inside agent instruction strings (use tools instead)

## Examples

```python
# Good: session state communication
session_state["user_profile"] = {"age": 30, ...}

# Good: tool imported as function reference
from app.tools.normalize_ingredients import normalize_ingredients
tools=[normalize_ingredients]

# Bad: tools imported as module
import app.tools.normalize_ingredients
```
