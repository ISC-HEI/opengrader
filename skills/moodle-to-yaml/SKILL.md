---
name: moodle-to-yaml
description: Extracts Moodle HTML responses and CSV grades into a unified yaml schema.
---

# Moodle-to-YAML Converter

This skill transforms Moodle exam exports into a structured YAML format. It uses a script for all mechanical extraction, leaving only semantic decisions to the LLM.

## Required Inputs

1. **Student Response File (`*-responses.html` or `*-réponses.html`):** Source for student names and answer text.
2. **Marks File (`*-notes.csv`):** Source for max points, obtained points, and question names.

### File Resolution

If a provided path does not exist, try to find the files in the same directory (or the current working directory if no directory was given), filter by the expected extension (`.html` for the responses file, `.csv` for the marks file), and identify the closest match by name. Try to find the files somewhere else within the same directory or current working directory. Ask the user: "I couldn't find `<provided path>`. Did you mean `<best match>`?" and wait for confirmation before proceeding.

---

## Step 1: Run the Extraction Script

Run this first. It does all the structural work: parsing both files, joining students by name, and extracting points.

```bash
uv run skills/moodle-to-yaml/scripts/moodle_to_yaml.py <responses.html> <notes.csv> [output.yaml]
```

The script produces a partial YAML with:
- All student answers and points extracted
- Question names and `max_points` from the CSV headers
- `FILL_IN` placeholders for `course_name` and `exam_date`
- `null` for `type` and `description` on each question (you must provide these)

---

## Step 2: Fill in Semantic Gaps

The script cannot infer meaning — that is your job.

### Global Metadata

* **`exam_name`**: The script extracts this from the HTML `<title>`. Verify it is correct and clean it up if needed.
* **`course_name`**: Ask the user.
* **`exam_date`**: Ask the user. Format: `YYYY-MM-DD`.
* **`authors`**: Optional. Ask the user. Omit if not provided.
* **`module`**: Optional. Extract from source files if present. If absent, omit (defaults to "000"). Do not ask the user.
* **`ue`**: Optional. Extract from source files if present. If absent, omit (defaults to "000"). Do not ask the user.

> **If a field is missing from the files and the user doesn't know:** use `null`. Inform the user which fields are null and why.

### Question Fields

For each question in the output YAML:

* **`description`**: The question text is **not** in the responses export. Ask the user to provide the description for each question (from the original exam document).
* **`type`**: Infer from the student answers already in the file. Valid values: `python`, `javascript`, `java`, `cpp`, `open`. If answers are Excel formulas, free text, or anything non-code, use `open`.

### Data Notes

* Points are already `null` if the student did not answer (`-`) or the exam is not yet graded (`Nécessite évaluation`).
* European decimal commas in the CSV are already converted to `.` by the script.

---

## Step 3: Validate the Output

Once you have filled in all fields, run the validator:

```bash
uv run skills/moodle-to-yaml/scripts/validate_exam_yaml.py <path-to-exam.yaml>
```

Fix any reported issues before declaring the skill complete. Common issues:
- `exam_date` missing or wrong format — must be `YYYY-MM-DD`
- A question missing `type` or `description`

---

## General Integrity Rules

1. **No Assumptions:** Do not invent values. If a field cannot be sourced from the files or the user, leave it `null`.
2. **Clarification over Completion:** If the file format deviates from expectations, describe the discrepancy and ask the user.
3. **Explicit Conflicts:** If a student name differs between CSV and HTML (the script will warn you), alert the user and ask for the correct mapping.
