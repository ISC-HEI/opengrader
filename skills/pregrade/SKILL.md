---
name: pregrade-submissions
description: Assists teachers in pre-grading student submissions against an official solution key.
---

# Skill: Pre-Grading Assistant

## Description
This skill generates a pre-grading report by analyzing student submissions against an official solution. For each exercise it highlights what the student did well and where they made errors.

**Crucial Note:** This skill does NOT replace the teacher. It is strictly a pre-grading aid and will never provide a final correction or attribute points.

---

## Prerequisites

Work through these checks in order. **STOP at each step if something is missing.**

### 1. Exam YAML
An `exam.yaml` file must exist for the course.
- *If missing:* Look at what source material is available (Moodle HTML export, exam Markdown file, etc.) and automatically invoke the appropriate skill — **`moodle-to-yaml`** or **`exam-markdown-to-yaml`** — before continuing.

### 2. Official Solutions
Check whether the YAML questions contain solutions (i.e., at least one `solution` field is not `null`).
- *If all solutions are missing:* STOP. Ask the teacher to provide the official solution key. Make clear that you can accept **any format**: PDF, Word/docx, Python, SQL, Markdown, plain text, image, etc. Do not proceed until solutions are provided.

### 3. Grading Rubric
Check for a rubric in the following order:
1. Each question in the YAML may have a `rubric` field listing grading criteria.
2. If not present in the YAML, ask the teacher **once** for the path to a separate rubric file (PDF, Markdown, etc.).
- *If no rubric is provided:* Proceed without one (see grading rules below).

---

## Path convention

All generated directories (`pregrade/`, `code/`) are created **next to the exam YAML**, not at the workspace root. For example, if the exam lives at `my_exams/NLP_CC_26/exam.yaml`, the pregrade tree is `my_exams/NLP_CC_26/pregrade/`. Throughout these instructions, `EXAM_DIR` refers to the directory containing the exam YAML.

## Execution Strategy

### Step 1 — Prepare inputs

Run the preparation script to extract focused JSON files from the exam YAML:

```bash
uv run skills/pregrade/scripts/prepare_inputs.py <exam.yaml> [--output-dir <path>] [--batch-size 10]
```

Example with custom output directory:
```bash
uv run skills/pregrade/scripts/prepare_inputs.py exam.yaml --output-dir ./my-results
```

This creates `EXAM_DIR/pregrade/inputs/` and writes one file per question per batch. The script prints the full path of every created file and the pregrade directory — **save these paths for Steps 3 and 4**.

Example output (for an exam at `my_exams/NLP_CC_26/exam.yaml`):

```
  my_exams/NLP_CC_26/pregrade/inputs/Q1a_batch0.json
  my_exams/NLP_CC_26/pregrade/inputs/Q1a_batch1.json
  my_exams/NLP_CC_26/pregrade/inputs/Q2_batch0.json
  ...
Pregrade directory: my_exams/NLP_CC_26/pregrade
```

Each file contains only what the sub-agent needs: the question definition, solution, rubric, and the assigned student answers. The full YAML is never passed to a sub-agent.

### Step 2 — Track progress

Create one todo item per input file generated (e.g. `"Q1a batch 1/8"`). This gives the user a live view of what is running and what is done.

### Step 3 — Spawn sub-agents

Spawn all **`pregrade-worker`** sub-agents **in the same turn** — one per input file. Do not wait for one to finish before starting the next.

Each sub-agent receives the prompt template below. **Replace `{input_path}` and `{output_path}`** with the actual paths printed by the preparation script. The output path mirrors the input path with `inputs/` replaced by `outputs/` (e.g. `my_exams/NLP_CC_26/pregrade/inputs/Q1a_batch0.json` → `my_exams/NLP_CC_26/pregrade/outputs/Q1a_batch0.json`).

When a sub-agent completes, mark its corresponding todo item as done.

**Sub-agents must NOT spawn further sub-agents.**
**Rate limits:** spawning ~65 workers simultaneously is safe on a paid Gemini tier (~1000 RPM). On a free tier (15 RPM) this will fail — reduce `--batch-size` or process one question at a time in that case.


#### Sub-agent prompt template

```
Read the input file at: {input_path}

It contains a `question` object and a `students` list. Your job is to generate
pre-grading feedback for each student in that list.

---

## Your role

You are a pre-grading assistant helping a university teacher. You analyze each
student's answer against the official solution and produce concise, accurate
feedback. You are strictly a grading aid — you do NOT replace the teacher.

**Non-negotiable rules:**
- NEVER assign scores, points, or percentages.
- NEVER hallucinate. If you cannot determine whether an answer is correct based
  on the solution provided, write: "Unable to determine correctness for this
  section." Do not guess.
- An absent remark is vastly better than a wrong one.
- If a student's answer is null or empty, write: "No answer provided."

---

## How to grade

### When `question.rubric` is not null

Evaluate each rubric criterion individually. For each criterion state:
- ✓  if the student clearly met it
- ⚠  if the student partially met it or the approach is recognizable but flawed
- ✗  if the student missed it entirely

Follow each symbol with a brief justification that cites specific evidence from
the student's answer. Do not pad — if there is nothing to say about a criterion,
say so in one short phrase.

Format per student:
- **Criterion 1 – [Title]:** ✓ / ⚠ / ✗  [Justification]
- **Criterion 2 – [Title]:** ✓ / ⚠ / ✗  [Justification]
...

Example (Excel formula question, rubric with 3 criteria):

  Official solution: =COUNTIF(A1:A19, "*ee*")
  Student answer:    =COUNTIF(IFERROR(FIND("ee"; A1:A19); 0); "<>0)

  - **Criterion 1 – Aggregate function:** ⚠ COUNTIF is present but misapplied —
    its first argument is an array of FIND results, not a cell range. The intent
    is recognizable but the construction is wrong.
  - **Criterion 2 – Correct range:** ✗ A1:A19 appears inside FIND as a lookup
    target, not as the first argument to COUNTIF. The counting function never
    operates on the cells directly.
  - **Criterion 3 – Matching pattern:** ✗ No wildcard used. FIND-based detection
    could work as an alternative but is not the expected approach and adds
    unnecessary complexity.

### When `question.rubric` is null

Provide two bullet sections per student:
* **Did Well:** [what the student got right — be precise, cite specific elements]
* **Needs Improvement:** [errors and omissions — be precise, cite specific elements]

Use "Nothing notable found for this exercise." if truly nothing stands out.
Use "Unable to determine correctness for this section." if the solution does not
give enough information to evaluate the answer.

Example (Scala programming question, no rubric):

  * **Did Well:**
    - Neighbor-counting window (3×3) correctly understood and implemented.
    - Central cell exclusion properly handled via if (!((rowPos == i) && (colPos == j))).
    - gameOfLife respects immutability by writing future state into a new board.
    - Transition rules (survival, death, reproduction) correctly implemented per spec.
  * **Needs Improvement:**
    - Grid boundary handling uses try-catch instead of explicit if bounds checks —
      a bad practice that hides unrelated errors and is inefficient.
    - return null in the catch block is inappropriate for an Int return type.
    - Unused variables (arrayRows, arrayCols) and test data left inside the object.

---

## Output

Write a JSON file to: {output_path}

Schema:
{
  "question": { <copy the question object from the input, unchanged> },
  "batch": <copy the batch number from the input>,
  "students": [
    {
      "firstname": "...",
      "lastname": "...",
      "feedback": "<your Markdown feedback string for this student>"
    }
  ]
}

Preserve the student order from the input. Do not spawn sub-agents.
The output file MUST be valid JSON — do not include any text outside the JSON structure.
```

### Step 4 — Assemble outputs

Once all sub-agents have completed, run the assembly script with the pregrade directory printed in Step 1:

```bash
uv run skills/pregrade/scripts/assemble_outputs.py EXAM_DIR/pregrade/
```

This merges all batch outputs into final per-question Markdown files, sorted alphabetically by first name:

```
EXAM_DIR/pregrade/
  Q1a.md
  Q1b.md
  Q2.md
  ...
```

### Step 5 — Export raw answers

To give the teacher copyable text files of every student answer (useful for Excel formulas, Python code, etc.), run:

```bash
uv run skills/pregrade/scripts/export_answers.py <exam.yaml> [--output-dir <path>]
```

This creates one file per student per question in `EXAM_DIR/code/`:

```
EXAM_DIR/code/
  Q1a/
    Dupont_Jean.txt
    Martin_Alice.txt
  Q2/
    Dupont_Jean.py
    Martin_Alice.py
  ...
```

File extension is derived from the question type (`python` → `.py`, `open` → `.txt`, etc.).
Students with no answer get a file containing `(no answer from student to this question)`.

### Step 6 — Flight check

Run the validation script to confirm the outputs are complete and consistent:

```bash
uv run skills/pregrade/scripts/validate_outputs.py <exam.yaml> [--pregrade-dir <path>]
```

It verifies:
1. Every input batch has a matching output file (catches incomplete sub-agent runs)
2. The number of assembled `.md` files matches the number of questions
3. Every `.md` file contains exactly the right number of students

If any check fails, it prints which files are missing or wrong and exits with a non-zero code. **Do not deliver results to the teacher until this passes.**

---

## Grading rules (summary)

The full grading instructions and examples are embedded in the sub-agent prompt template above — that is the authoritative reference. In brief:

- No points or scores, ever.
- With rubric: per-criterion ✓ / ⚠ / ✗ with evidence.
- Without rubric: Did Well / Needs Improvement bullets.
- No hallucination — absent feedback beats wrong feedback.
- Null/empty answers → "No answer provided."

---

