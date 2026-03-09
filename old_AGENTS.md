# OpenGrader

Modular agentic system for grading exams, built at [ISC/HEVS](https://isc.hevs.ch).

## Architecture

OpenGrader is a conversational grading assistant built on LangGraph deep agents.
It uses LLMs via LiteLLM, persists conversation state in SQLite, and follows the
[Agent Skills specification](https://agentskills.io/specification) for modularity.

The agent guides teachers through a multi-stage workflow: inventory exam files,
extract questions, build rubrics, then grade answers — with human confirmation
at each step.

## Project Layout

```
opengrader.py          Main entry point (OpenGraderAgent class, interactive CLI)
utils.py               Shared utilities (logging, progress spinner)
requirements.txt       Python dependencies
skills/                Modular skills, each with a SKILL.md
  inventory/           Scans working directory, identifies files, presents options
  question-extraction/ Extracts questions from markdown, LaTeX, PDF → questions.yaml
  sql-executor/        Executes SQL for test-case grading (stub)
my_exams/              User exam data directories (gitignored, not part of the codebase)
docs/                  Internal documentation
```

## Tech Stack

- **Python 3** with dependencies in `requirements.txt`
- **LangGraph deep agents** (`deepagents`) — agent framework
- **LiteLLM** (`langchain-litellm`) — LLM abstraction via OpenRouter
- **SQLite** (`langgraph-checkpoint-sqlite`) — conversation checkpointing
- **pypdf / pdfplumber** — PDF text extraction

## Skills System

Skills are self-contained modules in `skills/<name>/`. Each contains a `SKILL.md`
following the [Agent Skills spec](https://agentskills.io/specification) with YAML
frontmatter and natural language instructions the agent reads at runtime.

To add a skill: create a new directory under `skills/` with a `SKILL.md`.

## Key Conventions

- Generated files go in an `opengrader/` subfolder within the teacher's working directory
- Structured data uses YAML (questions, rubrics, grades)
- Human-in-the-loop: the agent confirms file writes and edits before executing
- API key (`OPENROUTER_API_KEY`) and model (`OPENGRADER_MODEL`) are configured via environment variables

## Running

```bash
pip install -r requirements.txt
python opengrader.py <path-to-exam-folder>
```
