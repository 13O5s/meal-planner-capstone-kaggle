# llm-security-review

## Purpose
Review LLM-specific security concerns in agents built with ADK: prompt separation (system/user/assistant), tool-calling safety, hallucination mitigation, output validation, and least-privilege tool access.

## When to Use
- When creating or modifying an ADK agent definition
- When adding new tools that an agent can call
- When the agent handles user-provided data (ingredients, preferences) that could influence its behavior
- Before deploying any agent that has tool execution ability

## Prerequisites
- All agent files in `app/agents/` are accessible
- Tool definitions in tool files are accessible
- `rules/security.md` and `rules/architecture.md` have been reviewed
- Understanding of ADK agent structure (system_instruction, tools, before_tool_callback, after_tool_callback)

## Inputs
- Agent definitions (e.g., `app/agents/inventory.py`, `app/agents/recipe.py`)
- Tool definitions (e.g., `app/tools/*.py`)
- Agent instructions and prompt templates

## Expected Outputs
- LLM security review report covering:
  1. Prompt Separation
  2. Tool Safety
  3. Hallucination Mitigation
  4. Least Privilege
  5. Output Validation
  6. Data Exfiltration
- Remediation steps for each finding

## Step-by-Step Workflow

### 1. Prompt Separation
- Verify that system instructions, user messages, and assistant messages are properly separated in the ADK agent definition. User input should NEVER be part of `system_instruction`.
- Check if user-provided data (ingredient lists, preferences) is injected into `system_instruction` or mixed with system-level instructions. If so, flag for separation.
- Check if any agent uses string interpolation to build prompts from user input. If yes, this is a prompt injection risk. Flag and recommend structured input via ADK tool parameters.

### 2. Tool Safety
- For each tool registered with the agent, verify:
  - The tool does not execute arbitrary shell commands
  - The tool validates its own inputs before using them
  - The tool does not read or write files outside allowed paths
  - The tool does not make network requests to user-controlled URLs
- Flag any tool that accepts user-controlled strings used in file operations, command execution, or network requests.

### 3. Hallucination Mitigation
- Check if the agent has instructions to admit uncertainty when it doesn't know something (e.g., "If you don't know the nutrition data, say you don't know rather than guessing").
- Verify that tools return structured data and the agent is instructed to use tool results for factual claims (nutrition data, recipe lists, prices) rather than generating them.
- Check if the agent references external data sources (DuckDB, stores) with clear instructions to only use valid data from those sources.

### 4. Least Privilege
- Review each agent's tool list. Does it have more tools than it needs? For example, should the Nutrition Agent have access to the `duckdb_query` tool, or only the `calculate_nutrition` tool?
- Verify that agents don't have access to tools that could modify session state in ways that break the workflow contract.
- Check if any tool allows raw SQL execution (`conn.execute(raw_query)`) — this should not be exposed to agents.

### 5. Output Validation
- Check if agent outputs (responses to users) are validated before being returned. Are there constraints on what the agent can say or what data it can expose?
- Verify that agent responses don't leak internal data (full DuckDB schemas, API keys, system prompts).

### 6. Data Exfiltration
- Check if any tool or agent output contains more data than necessary (e.g., returning the full recipe database instead of just top 3 recommendations).
- Verify that agent conversation history doesn't accumulate indefinitely — long histories increase the risk of prompt injection through context.

## Files to Create or Modify

| Action | File |
|--------|------|
| Read | `app/agents/*.py` — all agent definitions |
| Read | `app/tools/*.py` — all tool definitions |
| Read | `app/instructor.py` or `app/orchestrator.py` — if agent orchestration exists |
| Create | LLM security review report (output, not committed) |

## Validation Checklist
- [ ] All 6 categories reviewed
- [ ] Each agent's tool list is reviewed for least privilege
- [ ] Prompt separation verified: user input never in system_instruction
- [ ] All tool functions reviewed for unsafe operations (shell, file, network)
- [ ] Hallucination mitigations documented in agent instructions
- [ ] Output validation checked for data leak risk
- [ ] Data exfiltration vectors identified and documented

## Common Mistakes
- Assuming ADK automatically prevents prompt injection — it does not; the developer must ensure proper separation
- Giving agents too many tools — each agent should only have the tools it needs for its specific task
- Ignoring tool output — if a tool returns unvalidated data and the agent uses it directly, that's a risk
- Forgetting that tool descriptions are part of the prompt — a tool description that says "Use this to access the database" gives the agent unnecessary context for injection
- Letting agents write to session state without validation tools — session state keys should have controlled write access
- Not checking tool parameters — a tool that accepts raw SQL or file paths is a critical risk

## Related Rules
- `rules/security.md` — project-specific security policies
- `rules/architecture.md` — agent/tool contract, session state access patterns
- `rules/coding.md` — input validation and error handling

## Example Usage

```python
# Finding (CRITICAL) — Prompt Separation
# app/agents/recipe.py
# Issue: User preferences are injected into system_instruction
agent = Agent(
    model=gemini_model,
    name="recipe_agent",
    # BAD — user input in system instruction
    system_instruction=f"You are a recipe recommender. The user likes {user_preferences}"
)
# Remediation: Use tool parameters for user preferences, not system_instruction

# Finding (HIGH) — Least Privilege
# app/agents/nutrition.py
# Issue: Nutrition agent has access to raw SQL tool
agent = Agent(
    tools=[calculate_nutrition, duckdb_query],  # BAD — doesn't need duckdb_query
)
# Remediation: Remove duckdb_query from nutrition agent's tool list

# Finding (HIGH) — Tool Safety
# app/tools/db.py
# Issue: Tool accepts raw SQL from agent
def duckdb_query(sql: str):  # BAD — agent can execute any SQL
    return conn.execute(sql).fetchall()
# Remediation: Only expose specific query functions, not raw SQL
```
