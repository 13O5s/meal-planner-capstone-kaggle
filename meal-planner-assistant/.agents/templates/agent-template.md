# Agent Template: `<agent_name>`

## Purpose
<!-- Describe what this agent does in one sentence. -->

## Location
`app/agents/<agent_name>.py`

## Factory Function

```python
from google.adk.agents import Agent

# Import tools as function references (not modules)
# from app.tools.<tool_name> import <tool_function>


def create_<agent_name>_agent():
    return Agent(
        name="<agent_name>",
        description="""<One-line description of what this agent does>""",
        instruction="""<Detailed instruction for the LLM>

Session state keys:
- Reads: <key1>, <key2>
- Writes: <key3>, <key4>

Steps:
1. Read <key1> from session state.
2. <Step description>.
3. Store result in session state['<key3>'].
4. Report back to the user.
""",
        # tools=[<tool_function>],
    )
```

## Registration in `app/agent.py`

```python
from app.agents.<agent_name> import create_<agent_name>_agent

<agent_name>_agent = create_<agent_name>_agent()

root_agent = Agent(
    ...,
    sub_agents=[
        ...,
        <agent_name>_agent,
    ],
)
```

Update the coordinator's `instruction` string to include the new agent in the correct workflow position.

## Validation

- [ ] Unique `name` — no duplicates across sub-agents
- [ ] Instruction documents all session state keys read and written
- [ ] Tools imported as function references, not modules
- [ ] Registered in `sub_agents=[...]`
- [ ] Coordinator instruction updated
- [ ] `agents-cli lint` passes

## Reference
- `rules/agents.md` — agent definition standards
- `rules/architecture.md` — wiring and session state conventions
- `rules/domain.md` — session state contract
