# OpenGrader — Agent Guide

OpenGrader is a modular agentic system for assisting university professors with exam grading. 
The LLM handles all semantic decisions; Python scripts handle purely mechanical data transformation.

## Skills

All capabilities are delivered through **skills**, see README.md

## Unified YAML Format

Every exam is represented as a single `.yaml` file. This is the contract between all skills. The full schema is in `models/schema.yaml`.

Always use YAML literal block scalar (`|`) for multiline strings (`description`, `content`, `solution`, `unit_tests`).

## Development Setup

- **Package manager**: `uv` — use `uv run <script>` to execute scripts
- **Installation**: `uv run install.py` — links skills and prompts into `~/.config/opencode/` via GNU stow and merges `config/opencode.json`

Run scripts with `uv run`, not `python` directly:
```bash
uv run skills/moodle-to-yaml/scripts/moodle_to_yaml.py <responses.html> <notes.csv> [output.yaml]
uv run skills/moodle-to-yaml/scripts/validate_exam_yaml.py <path-to-exam.yaml>
```

## Key Files

| File | Role |
|---|---|
| `models/schema.yaml` | JSON Schema (draft-07) for the unified YAML format |
| `models/template.jinja2` | Jinja2 template rendering a `FilledExam` to Markdown/PDF |
| `prompts/open-grader.md` | System prompt for the OpenGrader agent in OpenCode |
| `config/opencode.json` | OpenCode agent configuration (model, permissions, prompt reference) |
| `install.py` | One-shot installer (stow + config merge) |

