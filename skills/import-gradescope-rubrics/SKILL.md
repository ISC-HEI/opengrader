---
name: import-gradescope-rubrics
description: Import rubrics for the correction of an exam from a gradescope export
---
# Skill: Gradescope Rubric to YAML Converter

## Context
You are an expert data parser specializing in educational technology formats. Your task is to ingest CSV data exported from Gradescope rubrics and transform them into a specific YAML schema used for exam configuration.

## Input Requirements
- **Input Types:** Raw CSV text, multiple CSV file contents, or a list of files from a directory.
- **Output file:** The YAML output file to fill in with the imported rubrics

## Logic & Transformation Rules

### Question matching

Each `csv` file correspond to a question in the already existing YAML file. The first task is to try to match each `csv` file with a question, to know which field to complete in the YAML file.

### Determine Scoring Method (`question.scoring_method`)
In the CSV, in the last line, the scoring method should be written
- Set to `false` for Negative Grading
- Set to `true` for Positive Grading
- **Default:** If mixed or unclear, **ask confirmation** to the user.

### Map Rubric Items (`question.rubrics`)

In each CSV, the n lasts column correspond to the different rubrics created by the teacher. You should transcribe them into the YAML file.

For each rubric, you need to find :
- `description`: The text found in the 'Description' or 'Title' column. Ensure it is a clean string.
- `value`: The numerical point value associated with that item.

## Output Schema (YAML)

The YAML schema you have to follow for the ouput is located here : `./assets/schema.yaml`

Here is an example of generation :

```yaml
question:
  # ... Other properties
  scoring_method: [true/false]
  rubrics:
    - description: "Text here"
      value: [number]
    - description: "Next item"
      value: [number]
```
