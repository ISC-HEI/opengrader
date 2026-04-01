---
name: rubric-activation-benchmark
description: Assess rubric activation based on pregrade feedback to benchmark LLM grading precision
---
# Skill: Rubric Activation Benchmark

This skill analyzes pregrade feedback to assess which rubric criteria were met for each student. It produces benchmark data to evaluate LLM grading precision against teacher-created rubrics.

**Note:** Run the pregrade skill first to generate the feedback files this skill depends on.

---

## Prerequisites

### 1. Exam YAML
An `exam.yaml` file must exist with:
- Questions with `rubric` definitions (list of criteria with `description` and `value`)
- Student submissions in `student_response`

### 2. Pregrade Outputs
The pregrade skill must have been run first, producing:
- `pregrade/outputs/*.md` (assembled feedback files per question)

**ONLY** if pregrade outputs are missing, run:
```bash
uv run skills/pregrade/scripts/prepare_inputs.py <exam.yaml> [--output-dir <path>] [--batch-size 10]
# Then spawn sub-agents (see pregrade skill)
uv run skills/pregrade/scripts/assemble_outputs.py pregrade/
```

Note: If you used a custom `--output-dir` in `prepare_inputs.py`, adjust the path to `assemble_outputs.py` accordingly.

---

## Execution Strategy

### Step 1 — Prepare inputs

Run the preparation script to extract JSON files from exam YAML + pregrade outputs:

```bash
uv run skills/rubric-activation-benchmark/scripts/prepare_inputs.py <exam.yaml> <pregrade_dir> <benchmark_dir> [--batch-size N]
```

Example:
```bash
uv run skills/rubric-activation-benchmark/scripts/prepare_inputs.py exam.yaml ./pregrade ./benchmark --batch-size 10
```

This writes to `<benchmark_dir>/inputs/`:

```
<benchmark_dir>/inputs/
  Q1a_batch0.json    ← question metadata + rubrics + students with pregrade feedback
  Q1a_batch1.json
  Q2_batch0.json
  ...
```

Each file contains: question name, rubrics list, and students with their pregrade feedback.

### Step 2 — Track progress

Create one todo item per input file (e.g., `"Q1a batch 1/4"`).

### Step 3 — Spawn sub-agents

Spawn all **`-worker`** sub-agents **in the same turn** — one per input file.

**Sub-agents must NOT spawn further sub-agents.**

#### Sub-agent prompt template

```
# Prompt: Rubric-Based Student Feedback Analysis

## Task
Read the input file at: `benchmark/inputs/<filename>.json`

The input contains:
- **question**: { name, max_points, rubrics: [{description, value}, ...] }
- **batch**: <batch_number>
- students: [{ firstname, lastname, pregrade_feedback }, ...]

Your task: For each student, analyze the `pregrade_feedback` and assess whether each rubric criterion was activated.

---

## Critical Logic & Constraints
1. **Point Ceiling**: The total `value` of all activated rubrics must not exceed the `max_points` field provided in the input.
2. **Mutual Exclusion**: Some rubrics may be mutually exclusive or hierarchical (where one encompasses another). In such cases, activate only the single most appropriate rubric to avoid over-counting.
3. **Preservation**: Maintain the exact student order from the input. Copy the `batch` number and `question` object exactly as they appear. Do not spawn sub-agents.

---

## Assessment Rules (The Rubric-First Rule)
For each rubric criterion (index 0, 1, 2, ...):
- **active**: `true` if the student met this specific criterion, `false` otherwise.
- **confidence**: 0.0–1.0 score based on your certainty. 
    - **Note**: Accuracy is paramount. If there is ambiguity in the feedback, a **lower confidence score is preferred over a false high-confidence assessment**. Use low scores (0.1–0.4) if the feedback is vague or contradictory regarding the rubric.
- **justification**: A brief explanation (1-2 sentences max).

**Strictness**: The rubric is the **single source of truth**. 
- If the rubric indicates that a specific response or condition is sufficient to be considered "correct" or "active," you **must** set `active: true`. 
- This applies even if the student's response fails to fulfill the broader requirements of the original exercise. If the rubric is satisfied, the criterion is active—regardless of overall exercise completion.

---

## Output Format
**IMPORTANT: You MUST write the output to the file using the Write tool.*
Write a JSON file to: `<output_folder>/outputs/<filename>.json`

**Schema:**
{
  "question": { <copy from input, unchanged> },
  "batch": <copy batch number from input>,
  "students": [
    {
      "firstname": "...",
      "lastname": "...",
      "rubric_assessments": [
        {
          "rubric_index": 0,
          "active": true/false,
          "confidence": 0.0-1.0,
          "justification": "..."
        },
        ...
      ]
    }
  ]
}
```

### Step 4 — Assemble outputs

Once all sub-agents complete, run:

```bash
uv run skills/rubric-activation-benchmark/scripts/assemble_outputs.py <benchmark_dir>
```

Example:
```bash
uv run skills/rubric-activation-benchmark/scripts/assemble_outputs.py ./benchmark
```

This merges batch outputs into final per-question JSON files in `<benchmark_dir>/activations/`:

```
<benchmark_dir>/activations/
  Q1a.json
  Q1b.json
  Q2.json
  ...
```

### Step 5 — Validation

Run validation to ensure all outputs are complete:

```bash
uv run skills/rubric-activation-benchmark/scripts/validate_outputs.py <exam_yaml> <benchmark_dir> <pregrade_dir>
```

Example:
```bash
uv run skills/rubric-activation-benchmark/scripts/validate_outputs.py exam.yaml ./benchmark ./pregrade
```

Checks:
1. Every input batch has a matching output file
2. Number of assembled files matches number of questions with rubrics
3. Each file contains the correct number of students

---

## Output Schema (Final JSON)

```json
{
  "question_id": 0,
  "question_name": "Exercice 1",
  "rubrics": [
    {"description": "Uses correct formula", "value": 1},
    {"description": "Handles edge cases", "value": 0.5}
  ],
  "students": [
    {
      "firstname": "John",
      "lastname": "Doe",
      "rubric_assessments": [
        {
          "rubric_index": 0,
          "active": true,
          "confidence": 0.9,
          "justification": "Student used =COUNTIF correctly"
        },
        {
          "rubric_index": 1,
          "active": false,
          "confidence": 0.85,
          "justification": "No edge case handling mentioned"
        }
      ]
    }
  ]
}
```

---

## Next Steps

After this benchmark is generated, you can:
1. Compare with teacher grades from GradeScope to measure precision
2. Run the rubric-precision-benchmark skill for deeper analysis
