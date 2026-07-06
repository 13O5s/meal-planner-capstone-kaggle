# Agent Rules

## Purpose

Standardize how ADK agents are defined, configured, and wired together in this project.

## Principles

- Each agent has a single, focused responsibility with a narrow tool surface
- Agent instructions are declarative prompts, not procedural code
- All sub-agents are stateless — state lives in session storage
- The root coordinator owns the workflow sequence; sub-agents own their domain

## Required Practices

- Each agent must have a unique `name`, a descriptive `description`, and a clear `instruction`
- Agent instructions must specify what session state keys to read and write
- Tools must be listed in the `tools` parameter as imported function references
- Sub-agents must be registered in the coordinator's `sub_agents` list
- All agents must be created via factory functions in `app/agents/`

## Forbidden Practices

- Two agents sharing the same `name`
- Agent instructions containing hardcoded secrets
- Agents calling other agents' tools directly
- Putting logic in instructions that belongs in a tool function
- Instructions that do not document session state keys

## Examples

```python
# Good: focused agent with documented session state
def create_profile_agent():
    return Agent(
        name="profile_agent",
        description="Builds structured user profile",
        instruction="""Extract into session state 'user_profile':
- age (int)
- goal (string: healthy/budget/high_protein/weight_loss)
...""",
    )

# Bad: vague name, no documented state keys
Agent(name="agent1", description="Does stuff", instruction="Do the thing")
```
