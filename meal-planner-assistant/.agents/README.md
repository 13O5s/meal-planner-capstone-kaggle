# .agents — AI Assistant Customization

This directory provides a modular, extensible customization system for AI coding assistants (Google ADK, OpenCode, OpenHands, Claude Code, Gemini CLI) working on this project.

## Structure

```
.agents/
├── README.md              # This file — how to use the system
├── rules/                 # Canonical project standards (one concern per file)
├── skills/                # Reusable workflows for common tasks
│   ├── development/       # Agent/tool/service scaffolding & refactoring
│   ├── meal-planning/     # Domain-specific meal planning operations
│   ├── testing/           # Test writing & pre-commit fixing
│   └── security/          # LLM & MCP security practices
└── templates/             # Boilerplate layouts for new components
```

## How to use

### Rules (`rules/`)

Rules are the **single source of truth** for project standards. Every rule file covers one concern:

- **Purpose** — why this rule exists
- **Principles** — guiding philosophy
- **Required Practices** — must-do actions
- **Forbidden Practices** — must-not-do actions
- **Examples** — concrete code snippets

**Always load the relevant rules before starting a task.** Skills reference rules by name rather than duplicating them.

### Skills (`skills/`)

Skills are **reusable step-by-step workflows** for specific tasks. Each skill describes:

- When to use it
- Expected inputs
- Implementation workflow
- Files to modify
- Validation checklist
- Common mistakes

Skills reference rules (e.g., "Follow `rules/coding.md`") instead of repeating rule content.

### Templates (`templates/`)

Templates provide **boilerplate project layouts** for new components. Use them when scaffolding a new agent, tool, workflow, or MCP server.

## Extending

To add a new rule: create `<name>.md` in `rules/`. Follow the Purpose/Principles/Required/Forbidden/Examples structure.

To add a new skill: create `<name>.md` under the appropriate subdirectory in `skills/`. Reference existing rules by name.

To add a new template: create `<name>-template.md` in `templates/`.

No existing files need modification — the system is designed for additive changes.
