---
name: rubric-precision-benchmark
description: Benchmark the precision of rubric precision benchmarking
---
# Rubric precision benchmark

This skill allow the generation of a benchmark to evaluate the precision of rubric based correction.

# Required Inputs

As input, a YAML exam file should be provided. This file should contains :
- **Student submissions:** One or more student submissions to base the benchmark on
- **Questions solution:** The official answer for the questions to benchmark
- **Question rubrics:** The rubric to base the correction on for each question

If not mentionned, generate the benchmark for every questions with all those pre-requisites filled. If mentionned, only generate the benchmark for the questions asked by the user.

# Core instructions and Rules of engagement

You goal is to grade all the student submissions in the input YAML file. 

## Track progress

Create one todo item per question to grade (e.g. `"Q1a"`). This gives the user a live view of what is running and what is done.

## Spawn sub agents

Spawn all **`worker`** sub-agents **in the same turn** — one per question. Do not wait for one to finish before starting the next.

Each sub-agent receives the prompt template below. When a sub-agent completes, mark its corresponding todo item as done.

**Sub-agents must NOT spawn further sub-agents.**

### Sub-agent prompt template

```
Read the input file at: benchmark/inputs/<filename>.yaml

It contains a unified exam file. In this file, you can read the question id <question id>, and read all the students submissions for this question.

The question should contains a rubric lists, and a grading method (positive or negative). 

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

Evaluate each rubric criterion individually. For each criterion, look :
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

---

## Output

As output, write a .csv file to benchmark/outputs/generated/<filename>.csv

Format : 
\`\`\`csv
First Name, Last Name, <Rubric 1 description>, <Rubric 2 description>, ...
..., ..., <true if has rubric 1>, <true if has rubric 2>, ...
\`\`\`

Preserve the student order from the input. Do not spawn sub-agents.
```

# Output format

You will ouput a `.csv` per qestion to the user requested location. If the user did not mention a location, **ask for it**.

The format will be the following :
```csv
First Name, Last Name, <Rubric 1 description>, <Rubric 2 description>, ...
..., ..., <true if has rubric 1>, <true if has rubric 2>, ...
```

Fhe filename should be : `<question_id>_generated.csv`

# Validation

To validate the generated files, you can run this script :

```bash
uv run scripts/validate_csv.py exam.yaml --files <question_id_0>_generated.csv <question_id_1>_generated.csv
```

It take as parameter the exam YAML file, and a list of all the generated files.

# Next steps

Once this file is generated, ask the user if he want to continue by running the benchmarking.
If the user accepts, you will need an additionnal input : 
- **Path to the exported gradescope folder:** A path leading to a folder containing the exported corrections from gradescope.

In this folder, there is one file per exam question, you will then need to match each filename with the question in the YAML file.
