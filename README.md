# OpenGrader

![logo](docs/opengrader_logo.png)

## About

OpenGrader is a modular agentic system to grade exams. It offers several tools:

- Extract the questions from various formats (LaTeX, Markdown, PDF, JSON, CSV etc.)
- Extract the questions and answers from various systems (Moodle, VPL, HybridProctor).
- Extract answers from scanned exams.
- Assist in building the rubrics
- Ability to run unit tests - test cases
- Pre-grade the exams using the rubrics and the answers.
- Export to PDFs formatted for Gradescope import.

Instead of offering a single, monolithic solution, OpenGrader is designed to be modular and extensible. 

OpenGrader capabilities are achieved through a set of skills, which are small, focused modules that can be combined to create a powerful system. Skills adheres to the `SKILL.md` [specification](https://agentskills.io/specification).

## Skills

OpenGrader comes with a set of skills that are bundled with the system. These skills are:

- **exam-markdown-to-yaml**: Transforms an exam markdown file into a structured YAML file, extracting metadata, questions, point values, types, and solutions.
- **export-exam-to-pdf**: Exports an exam YAML into PDFs ready for GradeScope upload, generating both blank templates and student answer PDFs with normalized page counts.
- **import-student-answers**: Imports student submission files into an existing exam YAML file, automatically detecting folder structures and handling duplicates.
- **import-unit-tests**: Imports unit test code from files into an exam YAML file, matching tests to questions based on filenames or content.
- **moodle-to-yaml**: Converts Moodle exam exports (HTML responses and CSV grades) into the unified YAML schema.
- **pregrade**: **BETA**  Generates a pre-grading report by analyzing student submissions against an official solution, highlighting strengths and errors without assigning points.

## Installation

For this project, we recommand using [OpenCode](https://opencode.ai/), as it can be linked to the AI agent of your choice, and support the `SKILL.md` [specification](https://agentskills.io/specification). But you can bring the local agent of your choice. We will only detail installation and usage with this tool, and we officially support only this one.

Run the installation script to set up OpenGrader with OpenCode:

```bash
uv run install.py
```

This script installs three components to `~/.config/opencode/`:
- **Skills**: Linked from the `skills/` folder using GNU stow
- **Prompts**: Linked from the `prompts/` folder using GNU stow  
- **Config**: Merged with your existing OpenCode config (if any), overlaying only the options defined in `config/opencode.json`

## Usage

Using `opencode`, you can start a sessions either in the terminal (with a TUI) using :
```bash
opencode
```

Or start a web based session using :

```bash
opencode web
```

Then, to cycle between the different agent (and use the `OpenGrader` agent), you can use the `tab` key by default.

Then, you can start prompting the agent with requests like :
- `I want to import an exam I downloaded from Moodle` -> To trigger the `moodle-to-yaml` skill
- `I want to import some students submissions into my exam` -> To trigger the `import-student-answers` skill
- ...

Or you can force the usage of a particual skill by typing `/skills` and then pressing `Tab`.

## Observability

To enable LLM debugging, you have two paths forward :
- OpenRouter Broadcasting
- Local LiteLLM proxy

### OpenRouter Broadcasting

This solution is the simplest to implement, but it will limit the model you debug to only the ones available on `OpenRouter`. 

To enable the broadcasting, got to [this](https://openrouter.ai/settings/observability) page, and toggle the Observability broadcast switch. Then, connect for example a `Langfuse` instance to this by adding your private and public key.

### Local LiteLLM proxy

This solution deploy a local instance of `Langfuse`, and a small LLM proxy named `LiteLLM` to forward all the requests. This allows to log all the requests made from OpenCode (independently from the model/provider selected) to the local instance of langfuse.

You can follow the instructions [here](./local_proxy/README.md) to install and use it.

## Credits

OpenGrader is built at [ISC](https://isc.hevs.ch) and released under the [Apache 2.0 License](LICENSE.txt).
