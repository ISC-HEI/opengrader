---
name: moodle-to-yaml
description: Extracts Moodle HTML responses and CSV grades into a unified yaml schema.
---

# Moodle-to-YAML Converter

This skill transforms Moodle exam exports into a structured YAML format. It requires reconciling qualitative text data from HTML and quantitative grade data from CSV.

## Role: Direct Data Transformer
**Constraint:** Do NOT write or suggest a automatic method, or any external tool to perform this task. **You** are the engine. Process the provided text and files directly and output the final YAML.

## Required Inputs

1.  **Student Response File (`*-responses.html`):** The source for student names and the text of their answers.
2.  **Marks File (`*-notes.csv`):** The source for max points, obtained points, and question names.

## Data Mapping & Schema

The output must strictly follow the `./assets/schema.yaml` structure:

1. **Identify the Gap:** Check for fields like `exam_name`, `course_name` or `question.name`.
2. **Consult the User:** If missing, pause the transformation and ask the user:
   > "I couldn't find the [Exam Name / Course Name / ...] in the files. Could you please provide it so I can complete the JSON?"
3. **Defaulting:** Only use "Unknown" if the user explicitly tells you they don't know or don't care.

### 1. Global Metadata
* **`exam_name`**: Extract from the header of the HTML or the filename.
* **`course_name`**: Extract from the HTML breadcrumbs or header.

### 2. The `questions` Object (Dictionary)
* **Key**: Use a zero-based index string (e.g., `"0"`, `"1"`).
* **`name`**: The question label (e.g., "Q. 1"). Match this with the CSV column headers.
* **`type`**: Infer from content. Valid values are available in the YAML schema files
* **`max_points`**: Extract from the CSV header (e.g., from `Q. 1 /5.00`, extract `5.0`).

### 3. The `students_response` Array
* **`firstname` / `lastname`**: Split the student name found in the HTML table or CSV "Nom/Prénom" columns.
* **`answers`**: A dictionary where keys match the `questions` object IDs.
    * **`content`**: The raw text/code response from the HTML.
    * **`points`**: The value from the corresponding CSV cell. Convert to `float`. If the question is not yet graded (marked as `-`), use `null`.

---

## Parsing Logic & Constraints

* **Primary Key Alignment:** Use the student's full name to join the HTML row with the CSV row. 
* **Data Cleaning:** * Strip HTML tags from student responses but **preserve whitespace/indentation** for `"python"` type questions.
    * Convert European decimal commas (`,`) in the CSV to periods (`.`) for valid JSON floats.
* **Missing Data:** If a student appears in the CSV but has no response in the HTML, create the entry but set `content` to `null`.

## Validation Checklist
1. Is the `questions` ID (e.g., `"0"`) consistent between the global definitions and the student `answers`?
2. Are all `points` and `max_points` represented as numbers or `null`, never strings?
3. Did you capture the "Description" of the question from the HTML?

## General Principles & Integrity (Strict Mode)

To ensure data accuracy and prevent hallucination, the following rules apply globally:

1. **No Assumptions:** If a data point is missing from the source files and is not explicitly defined in this document, **do not invent a value.** 
2. **Clarification over Completion:** If an instruction is ambiguous or a file format deviates from the expected structure, pause and describe the discrepancy to the user.
3. **Explicit Errors:** If you encounter a conflict (e.g., a student is listed in the CSV but has a different name format in the HTML), alert the user and ask for the preferred mapping.
4. **"I don't know" is a valid output:** If a specific JSON key cannot be populated with factual data from the provided files, it must remain `null`. Inform the user which fields were left null and why.
