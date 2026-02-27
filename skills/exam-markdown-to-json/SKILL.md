---
name: exam-markdown-to-json
description: Use this skill when the user wants to parse or transform an exam file in markdown format into a structured JSON file. This skill extracts exam metadata, questions, points, types, and solutions from .md exam files.
---

# Exam to JSON Skill

## Overview

This skill transforms an exam markdown file into a structured JSON file following a specific schema. It extracts exam metadata, questions, point values, question types, and solutions.

## When to Use

- User says "parse this exam file", "convert exam to JSON", "extract questions from exam"
- User wants to transform a `.md` exam file into JSON format
- User mentions loading/transforming exam file information
- User has an exam markdown file and wants structured data from it

## Input

- An exam markdown file (`.md` format)
- Optionally, a reference to the output JSON model/schema

## Output Schema

The output must match exactly the template given in the `assets/model.json` file

**Note:** The `students_response` field should only be filled if student answers are provided in the input. If there is no student answers in the 

## Parsing Instructions

### Step 1: Read the Exam File

Read the markdown file provided by the user.

### Step 2: Extract YAML Frontmatter

Look for YAML frontmatter at the top of the file (between `---` markers):

- `exam_name`: Extract from `title` field, or from the first heading if no title
- `course_name`: Extract from `course` field in frontmatter

### Step 3: Identify Questions

Questions are typically found under headings like:
- `# Exercice 1` or `# Exercice 1 - Title`
- `# Question 1` or `# Q1`
- `## Exercice 1` (sub-heading)

Iterate through each question section and assign sequential indices (0, 1, 2, ...).

### Step 4: Extract Question Details

For each question, extract:

1. **name**: The question name/title. Should look like : "Exercise 1", "Question 1" etc...

2. **type**: One of [`python`, `open`], determine with the question content:
   - `"python"`: If the question requires code implementation, has function definitions, code blocks with Python, or asks to write a function
   - `"open"`: For theoretical questions, written answers, analysis questions.

   Look for indicators like:
   - Python function definitions: `def function_name(...)`
   - Code blocks with ```python
   - Keywords like "implémenter", "écrire une fonction", "écrire le code"
   - Questions asking for algorithms or solutions

3. **description**: The main question text, including any context, examples, or sub-questions. Include everything from the question header until:
   - The next question section
   - A solution block (`\ifsolution`, or "Solution:" heading)
   - End of file

4. **solution**: 
   - Extract solution content if present (marked with `\ifsolution`, "Solution:", or similar)
   - Set to `null` if no solution is provided

5. **max_points**: Extract point values from headers or sub-questions:
   - Look for patterns like `(0.2 point)`, `[3 pts]`, `3 points`
   - Sum up points from all sub-parts of a question
   - Convert to float (e.g., 0.2 → 0.2, 3 → 3.0)

### Step 5: Handle Sub-questions

If a question has sub-parts (a, b, c, d), include them within the same question's description. The max_points should be the sum of all sub-parts. Do NOT create a new field for the sub questions

### Step 6: Build the JSON

Construct the JSON object following the exact schema:
- Use string indices for questions: "0", "1", "2", etc.
- Ensure all numeric values are floats
- Use `null` (not "null" string) for missing solutions
- Do *NOT* add fields that are not present in the model. If you feel like a field is missing, report it to the user.

### Step 7: Save the Output

Write the JSON file. Ask the user where they want to save it, or suggest a filename like `exam_name.json` in an appropriate location.

## Example

**Input:** An exam markdown file with YAML frontmatter containing course "Algorithmie" and title "Examen Semestriel", with 5 exercises.

**Output:**
```json
{
  "exam_name": "Examen Semestriel",
  "course_name": "Algorithmie et structures de données",
  "questions": {
    "0": {
      "name": "Q. 1",
      "type": "python",
      "description": "Exercice 1 - Mur d'expression\n\n[full question description with examples, sub-questions a-d]",
      "solution": null,
      "max_points": 1.0
    },
    "1": {
      "name": "Q. 2",
      "type": "python",
      "description": "Exercice 2 - La bibliothèque mystérieuse\n\n[full question description]",
      "solution": null,
      "max_points": 1.0
    },
    ...
  }
}
```

## Tips

- Be careful with point extraction: "0.2 point" = 0.2, "0.5 point" = 0.5
- Python questions often have function signatures like `def fonction(...)`
- Open questions are typically theoretical, analytical, or descriptive
- Preserve code blocks and formatting in descriptions
- Handle French exam terminology (points, questions, exercices)
- Don't hallucinate, if some data is missing, you can always ask the user.
