# LLM Grading Benchmark

Compare grading performance across multiple LLMs against GradeScope ground truth.

## Requirements

```bash
pip install matplotlib numpy
```

## Usage

```bash
python llm_stats.py sources/*.json --out-dir out
```

## Input Format

Each JSON file contains assessment data with this structure:

```json
{
  "summary": { "precision_percent": 78.9, ... },
  "questions": {
    "question_id": {
      "all_details": [
        {
          "student": "Student Name",
          "rubric": "Rubric criterion",
          "generated": true,    // LLM's grading decision
          "gradescope": true,  // Ground truth
          "confidence": 0.95
        },
        ...
      ]
    }
  }
}
```

## Output

Generates 5 visualization charts in the output directory:

| Chart | Description |
|-------|-------------|
| `global_precision.png` | Bar chart comparing overall precision per LLM |
| `per_question_precision.png` | Grouped bar chart of precision per question |
| `error_overlap_matrix.png` | Heatmap of pairwise error overlap (Jaccard similarity) |
| `per_question_error_overlap.png` | Grouped bar chart of error overlap per question |
| `per_question_error_overlap_heatmap.png` | Heatmap of error overlap per question |

## Metrics

- **Precision**: % of LLM grading decisions matching GradeScope
- **Error Overlap**: Intersection / min(errors_llm1, errors_llm2) — how often two LLMs make the same mistakes
- **All-Agreement Errors**: Assessments where ALL LLMs made the same error
