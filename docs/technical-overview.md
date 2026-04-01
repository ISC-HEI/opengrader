# OpenGrader Technical Overview

OpenGrader is a modular agentic system that helps university professors grade exams efficiently. It transforms exam data from various formats (Moodle exports, scanned PDFs, Markdown files) into a unified YAML format, then assists with pre-grading and exporting to GradeScope.

## How It Works

OpenGrader uses a **skills-based architecture**:

1. **Unified YAML format** — All tools read and write the same YAML schema (`models/schema.yaml`). This is the contract between all skills.
2. **Skills** — Modular components, each handling one specific task (import, export, pre-grade, etc.)
3. **LLM + Scripts** — The LLM handles semantic decisions; Python scripts handle mechanical data transformation


## Folder Structure

| Folder | What it does |
|--------|--------------|
| `skills/` | 12 modular skills for exam processing |
| `models/` | YAML schema and Jinja2 templates |
| `prompts/` | System prompts for the OpenGrader agent |
| `scripts/` | Utility scripts (validation, benchmarking) |
| `config/` | OpenCode configuration |
| `docs/` | Documentation |
| `local_proxy/` | Observability setup (Langfuse + LiteLLM) |

## Skills Reference

| Skill | What it does | When to use it |
|-------|--------------|----------------|
| `exam-markdown-to-yaml` | Parses .md exam files into YAML | "I have an exam in Markdown format" |
| `moodle-html-to-yaml` | Parses Moodle HTML/CSV export | "I exported my exam from Moodle as HTML" |
| `moodle-mbz-to-yaml` | Parses Moodle .mbz backup file | "I have a Moodle backup file (.mbz)" |
| `text-exam-to-yaml` | Parses any text format (txt, html, doc, rtf) | "I have a text-based exam file" |
| `scan-to-yaml` | Extracts answers from scanned PDF exams via OCR | "I have scanned paper exams" |
| `import-student-answers` | Imports student code submissions into YAML | "I want to add student submissions" |
| `import-unit-tests` | Imports unit test code into questions | "I want to add unit tests" |
| `import-gradescope-rubrics` | Imports rubrics from GradeScope export | "I exported rubrics from GradeScope" |
| `export-exam-to-pdf` | Generates GradeScope-ready PDFs | "I need PDFs for GradeScope" |
| `pregrade-submissions` | AI-assisted pre-grading against solution key | "I want to pre-grade students" |
| `rubric-activation-benchmark` | Benchmarks rubric quality | "I want to test rubric accuracy" |
| `skill-creator` | Creates new skills | "I want to create a new skill" |

## Typical Workflows

### Workflow 1: Import → Pre-grade → Export

1. Import exam questions (Markdown, Moodle, or text)
2. Import student answers
3. Run pre-grading with solution key
4. Export to GradeScope PDFs

### Workflow 2: Moodle Import

1. Export exam from Moodle (.mbz or HTML)
2. Import student answers
3. Pre-grade and export

## Quick Start

1. **Install**
   ```bash
   uv run install.py
   ```

2. **Run OpenGrader**
   ```bash
   opencode        # Terminal UI
   # or
   opencode web   # Web UI
   ```

3. **Ask naturally** — Describe what you want to do, and the agent will guide you through the right workflow.
