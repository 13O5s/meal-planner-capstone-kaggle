# Workflow Template: `<workflow_name>`

## Purpose
<!-- Describe the workflow sequence this defines. -->

## Agent Sequence

```
1. <Agent A> → writes <key_A>
2. <Agent B> → reads <key_A>, writes <key_B>
3. <Agent C> → reads <key_A> + <key_B>, writes <key_C>
```

## Session State Contract

| Key | Written By | Read By | Format |
|---|---|---|---|
| `<key_A>` | Agent A | Agent B, Agent C | `dict` or `list` — describe |
| `<key_B>` | Agent B | Agent C | `dict` or `list` — describe |
| `<key_C>` | Agent C | — | `dict` or `list` — describe |

## Coordinator Instruction Update

In `app/agent.py`, update the root agent's `instruction` to include this workflow as an option:

```python
instruction="""...
Available workflows:
1. **<workflow_name>** — <one-line description>: <Agent A> → <Agent B> → <Agent C>
..."""
```

## Or: Create a separate root agent

```python
<workflow_name>_root = Agent(
    name="<workflow_name>_coordinator",
    model=Gemini(model="gemini-flash-latest"),
    instruction="""...""",
    sub_agents=[agent_a, agent_b, agent_c],
)
```

## Validation

- [ ] No circular dependencies between agents
- [ ] Each step reads only keys written by earlier steps
- [ ] Coordinator instruction or separate root agent defined
- [ ] Session state keys documented in `rules/domain.md`
- [ ] `agents-cli lint` passes

## Reference
- `rules/domain.md` — session state contract documentation
- `rules/architecture.md` — coordination patterns
- `rules/agents.md` — agent definition standards
