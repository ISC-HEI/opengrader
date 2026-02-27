---
name: exam-markdown-to-yaml
description: Use this skill when the user wants to parse or transform an exam file in markdown format into a structured YAML file. This skill extracts exam metadata, questions, points, types, and solutions from .md exam files.
---

# Exam to YAML Skill

## Overview

This skill transforms an exam markdown file into a structured YAML file following a specific schema. It extracts exam metadata, questions, point values, question types, and solutions.

## When to Use

- User says "parse this exam file", "convert exam to YAML", "extract questions from exam"
- User wants to transform a `.md` exam file into YAML format
- User mentions loading/transforming exam file information
- User has an exam markdown file and wants structured data from it

## Input

- An exam markdown file (`.md` format)

## Output Schema

The output must match exactly the template given in the `assets/schema.yaml` file

**Note:** The `students_response` field should only be filled if student answers are provided in the input. If there is no student answers in the input, put this field to `null`

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

2. **type**: One of the available types in the YAML schema, determine with the question content:
   - If the question asks to produce a code output -> search for the corresponding programming language in the YAML schema
   - If the question ask a natural text answer -> you can use the `open` type. 
   
   Look for indicators like:
   - Python function definitions: `def function_name(...)`
   - Code blocks with ```python
   - Keywords like "implémenter", "écrire une fonction", "écrire le code"
   - Questions asking for algorithms or solutions

If you can't infer the question type, or are unsure of your solution, ASK CONFIRMATION from the user, DOT NOT GUESS silently.

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

### Step 6: Build the YAML

Construct the YAML object following the exact schema:
- Use string indices for questions: "0", "1", "2", etc.
- Ensure all numeric values are floats
- Use literal block scalar (|-) for every multiline string.
- Use `null` (not "null" string) for missing solutions
- Do *NOT* add fields that are not present in the model. If you feel like a field is missing, report it to the user.

### Step 7: Save the Output

Write the YAML file. Ask the user where they want to save it, or suggest a filename like `exam_name.yaml` in an appropriate location.

## Example

**Input:** An exam markdown file with YAML frontmatter containing course "Algorithmie" and title "Examen Semestriel", with 5 exercises.

**Output:**
```yaml
exam_name: Examen Semestriel
course_name: Algorithmie et structures de données
questions:
  - name: Q. 1
    type: python
    description: |-
      Exercice 1 - Mur d'expression

      [full question description with examples, sub-questions a-d]
    solution: null
    max_points: 1.0
  - name: Q. 2
    type: python
    description: |-
      Exercice 2 - La bibliothèque mystérieuse

      [full question description]
    solution: null
    max_points: 1.0
  ...
```

## Tips

- Be careful with point extraction: "0.2 point" = 0.2, "0.5 point" = 0.5
- Code questions often have function signatures like `def fonction(...)` for python
- Open questions are typically theoretical, analytical, or descriptive
- Preserve code blocks and formatting in descriptions
- Handle French exam terminology (points, questions, exercices)
- Don't hallucinate, if some data is missing, you can always ask the user.
- If you are unsure at any steps of this process, explain the situation to the user, and ask for guidance
