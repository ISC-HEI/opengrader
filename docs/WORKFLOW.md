# OpenGrader — Exam Grading Workflow

Step-by-step guide to go from student submissions to graded PDFs ready for Gradescope.

---

## Prerequisites

| Tool | Purpose | Install |
|---|---|---|
| **Python ≥ 3.12** + [uv](https://docs.astral.sh/uv/) | Run all scripts | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Typst ≥ 0.14** | Compile PDFs | `curl -fsSL https://typst.app/install.sh \| sh` |
| **Coursier** (`cs`) | Fetch and run Scala 2.13 | `curl -fL https://github.com/coursier/launchers/raw/master/cs-x86_64-pc-linux.gz \| gzip -d > cs && chmod +x cs && ./cs setup` |
| **isc-hei-document ≥ 0.7.1** | Typst package used by the template | installed automatically by Typst |

Install Python dependencies once (per exam project folder):
```bash
uv sync
```

---

## Repository layout

```
opengrader/                         ← this repo (framework only)
├── scripts/
│   ├── generate_pdfs_typst.py      ← generate per-student PDFs
│   ├── run_tests.py                ← compile & run ScalaTest suites
│   └── generate_summary.py        ← produce corrector summary (MD + PDF)
├── models/
│   └── template.typst.jinja2      ← Typst/Jinja2 template for student PDFs
├── exams/
│   └── 2026_poo_structure.yaml    ← exam questions only (no student data)
├── docs/
│   └── WORKFLOW.md                ← this file
└── pyproject.toml
```

**What lives locally, never in git:**

| File/folder | Why excluded |
|---|---|
| `*.tar` / `students_submissions.tar` | Raw student archives |
| `labo_test_YYYY.yaml` (full version) | Contains student source code |
| `pdf/` | Student PDFs (personal data) |
| `test_results.json` | Per-student test scores |
| `summary.md` / `summary.pdf` | Aggregated student data |
| `pregrade/` (entire folder) | Question drafts, OCR inputs/outputs, LLM artefacts |

---

## Step 0 — Set up a new exam (agent-assisted)

Both sub-steps below are handled by the OpenGrader agent. Start a session with `opencode` (or Claude Code), then prompt as described.

### 0a. Generate the exam YAML from the Markdown spec

You have a Markdown file describing the exam (questions, point values, code types). Ask the agent:

> *"I have my exam spec at `exams/my_exam_2027.md`. Convert it to an OpenGrader YAML structure file."*

The agent will invoke the **`exam-markdown-to-yaml`** skill and produce a YAML such as:

```yaml
exam_name: "ISC -- Course Name 2027"
course_name: "101.2 …"
exam_date: 2027-05-XX
authors: ["Dr A. Author"]
questions:
- name: "Question 1"
  id: 0          # 0-based — must match the test suite index
  type: scala
  max_points: 6.0
  description: |-
    # Question 1 — Title
    …Markdown question text…
```

> **Tip:** the `# Heading` at the start of each `description` is automatically stripped in the PDF — keep it, it becomes the subtitle visible in the question statement.

Save the result as `exams/YYYY_coursecode_structure.yaml` (structure only — commit this). The full YAML with student answers will live elsewhere locally.

### 0b. Generate the IntelliJ / Scala project skeleton

You have the reference solutions and want to generate the student skeletons, ScalaTest suites, and directory layout. Ask the agent:

> *"I have the exam spec at `exams/my_exam_2027.md` with Scala questions and solutions. Generate the IntelliJ project with student skeletons, solution files, and ScalaTest suites."*

The agent will invoke the **`cs101-labotest`** skill. The expected project layout it produces is:

```
intellij/
├── lib/                              ← ScalaTest 2.13 JARs (copy from previous year)
├── src/
│   ├── exercises/                    ← student stubs (??? placeholders)
│   ├── exercises/solutions/          ← reference implementations
│   ├── tests/                        ← student-facing test shells
│   └── tests/solutions/             ← ScalaTest suites (one per question)
└── <data files used by tests>
```

After generation, verify the project compiles with:

```bash
cs launch scalac:2.13.12 -- \
  -classpath intellij/lib/'*' \
  -d /tmp/verify \
  intellij/src/exercises/solutions/*.scala \
  intellij/src/tests/solutions/*.scala
```

Then update the two constants at the top of `scripts/run_tests.py`:

```python
INTELLIJ = Path("/absolute/path/to/intellij/project")

QUESTION_MAP = {
    0: ("ExerciseName1", "tests.solutions.Exercise1Test"),
    1: ("ExerciseName2", "tests.solutions.Exercise2Test"),
    # … one entry per question, id matches the YAML
}
```

---

## Step 1 — Extract student submissions

The students upload a single Scala file per question via Moodle/the exam platform. The raw archive arrives as `students_submissions.tar`.

```bash
mkdir -p pregrade/inputs
tar xf students_submissions.tar -C pregrade/inputs/
```

---

## Step 2 — Pre-grade (LLM extraction)

This step reads student submissions (Scala files) and extracts per-question student code into a structured YAML. Run the existing pre-grade scripts (in `scripts/` or a separate pipeline):

```bash
# Example — adapt to your actual pre-grade tooling
uv run python scripts/pregrade.py \
    --input  pregrade/inputs/ \
    --output pregrade/outputs/ \
    --exam   exams/2027_poo_structure.yaml
```

The output is a full YAML file that merges the exam structure with student answers:

```yaml
# labo_test_2027.yaml  (keep this LOCAL — do not commit)
exam_name: "…"
questions: […]
student_response:
- firstname: Alice
  lastname:  Dupont
  answers:
  - question_id: 0
    content: |
      package exercises
      object WordList { … }
    points:
    correction_details:
```

> If students submit multiple files concatenated (e.g., implementation + their own test class), the pipeline handles splitting automatically (`extract_implementation` in `run_tests.py`).

---

## Step 3 — Run unit tests

Compiles the reference solutions and all test suites once, then compiles and tests each student's code in parallel.

```bash
uv run python scripts/run_tests.py \
    -i labo_test_2027.yaml \
    -o test_results.json \
    -j 4              # parallel workers — tune to your machine
```

**What it does per student per question:**
1. Strips any embedded test class from the student code.
2. Renames `package exercises` → `package exercises.solutions` so the existing test suites can find the class.
3. Compiles only the student's file (solution JARs remain as cross-dep fallback).
4. Runs the matching `XxxTest` suite; student class shadows the reference in the classpath.
5. Parses the ScalaTest output: `Tests: succeeded N, failed M`.

**Possible outcomes per cell:**

| Status | Meaning |
|---|---|
| `N/T` | N tests passed out of T |
| `compile_error` | Student code does not compile |
| `timeout` | Infinite loop in student code (90 s wall-clock limit) |
| `parse_error` | ScalaTest crashed before printing the summary line |
| `empty` | No code submitted |

Output: `test_results.json` (keep local, do not commit).

---

## Step 4 — Generate per-student PDFs

```bash
uv run python scripts/generate_pdfs_typst.py \
    -i labo_test_2027.yaml \
    -o pdf/ \
    --test-results test_results.json
```

Each PDF contains:
- Student name header
- One section per question (question text in Source Sans 3, then student code)
- "Student answer" header showing test badge (✓ green / ~ orange / ✗ red / ⚠ error) and point score
- Pages are padded so all copies are layout-aligned (makes Gradescope rubric anchoring easy)

Upload the contents of `pdf/` to Gradescope.

---

## Step 5 — Generate corrector summary

```bash
uv run python scripts/generate_summary.py \
    -i labo_test_2027.yaml \
    -r test_results.json \
    -o summary
```

Produces:
- `summary.md` — Markdown table (paste into a shared document)
- `summary.pdf` — color-coded PDF table (green/orange/red per cell)

Share with the other correctors. **Do not commit either file.**

---

## Quick-reference cheat sheet

```bash
# One-time setup
uv sync

# Full run (steps 3-5)
uv run python scripts/run_tests.py          -i EXAM.yaml -o test_results.json -j 4
uv run python scripts/generate_pdfs_typst.py -i EXAM.yaml -o pdf/ --test-results test_results.json
uv run python scripts/generate_summary.py    -i EXAM.yaml -r test_results.json -o summary
```

---

## Troubleshooting

**`cs` not found** — Coursier is not on `PATH`. Re-run `cs setup` and open a new shell.

**`typst` not found** — Re-run the Typst installer or add `~/.local/bin` to `PATH`.

**All Q1 compile errors** — Check whether the student YAML `content` field mixes implementation + test class. The `extract_implementation()` function in `run_tests.py` splits on the second `package` declaration; confirm the separator pattern matches your exam's format.

**Many timeouts** — Reduce `-j` to 2 to lower memory pressure, or increase the `timeout=90` constant in `run_test.py:run_student_test()`.

**`parse_error`** — ScalaTest threw an unhandled exception before printing the summary. Check `test_results.json` for the `details` field; it contains the first 400 chars of stdout+stderr.

**Typst `No authors provided`** — The `authors` field is missing or empty in the exam YAML header.

**`isc-hei-document` package not found** — Run `typst update` or pin the package version in the template.
