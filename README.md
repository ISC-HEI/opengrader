# OpenGrader

![logo](docs/opengrader_logo.png)

## About

OpenGrader is a modular agentic system to grade exams. It offers several tools:

- Extract the questions from various formats (LaTeX, Markdown, PDF, Excel, Word, JSON, etc.)
- Extract the questions and answers from various systems (Moodle, VPL, HybridProctor).
- Extract answers from scanned exams.
- Assist in building the rubrics
- Ability to run unit tests - test cases
- Pre-grade the exams using the rubrics and the answers.

Instead of offering a single, monolithic solution, OpenGrader is designed to be modular and extensible. 

OpenGrader capabilities are achieved through a set of skills, which are small, focused modules that can be combined to create a powerful system. Skills adheres to the `SKILL.md` [specification](https://agentskills.io/specification).

## Skills

OpenGrader comes with a set of skills that are bundled with the system. These skills are:

- `pdf`: Extract the questions from PDF files.
- `moodle`: Extract the questions and answers from Moodle.
- `vpl`: Extract the questions and answers from VPL.
- `scans`: Extract answers from scanned exams (OCR).
- `rubrics`: Assist in building the rubrics.

## Using OpenGrader

1. Install the dependencies (one time only)

```bash
pip install -r requirements.txt
```

2. Set your OpenRouter API key

```bash
export OPENROUTER_API_KEY="your-key"
```

Or create a `.env` file with `OPENROUTER_API_KEY=your-key`.

3. Add your exam files

Create a folder in `my_exams/` with the name of the exam.

4. Run the grader agent and follow the instructions

```bash
python opengrader.py my_exams/your_exam_folder
```




## Credits

OpenGrader is built at [ISC](https://isc.hevs.ch) and released under the [Apache 2.0 License](LICENSE.txt).