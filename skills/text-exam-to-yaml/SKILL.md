---
name: text-exam-to-yaml
description: Use this skill when the user wants to parse or transform any text-based exam file (txt, html, doc, rtf, etc.) into a structured YAML file. This skill extracts exam metadata, questions, points, types, and solutions from unstructured or semi-structured exam documents.
---

# Text Exam to YAML Skill

## Overview

This skill transforms any text-based exam file into a structured YAML file following a specific schema. Unlike the markdown-to-yaml skill, this skill handles **any text format** without relying on a specific structure. The LLM must analyze the document to identify exam elements.

## When to Use

- User says "parse this exam", "convert exam to YAML", "extract questions from exam"
- User wants to transform a `.txt`, `.html`, `.doc`, `.rtf`, or any text-based exam file into YAML format
- User mentions loading/transforming exam file information from a non-markdown format
- User has an exam document (any text format) and wants structured data from it

## Input

- Any text-based exam file (`.txt`, `.html`, `.doc`, `.rtf`, or similar)

## Output Schema

The output must match exactly the template given in the `assets/schema.yaml` file.

**Note:** The `students_response` field should only be filled if student answers are provided in the input. If there are no student answers in the input, set this field to `null`

## Critical Principle

**When in doubt, ask the user.** This skill has no fixed format to guide extraction, so uncertainty is expected. Never guess silently — if you cannot confidently extract information, ask the user for clarification or confirmation.

---

## Parsing Instructions

### Step 1: Read the Exam File

Read the entire exam file provided by the user. Get familiar with its structure, formatting, and content.

### Step 2: Identify the Document Structure

Since there is no fixed format, analyze the document to find patterns:

**Common exam elements to look for:**
- **Question markers**: "Exercice", "Question", "Q.", "Problem", numbered lists, or numbered headings
- **Point values**: "(X points)", "[X pts]", "X pts", "Score:", "Note:"
- **Headers**: Course name, exam title, date, professor name (usually at the top)
- **Solution markers**: "Solution:", "Answer:", "Corrigé:", "\ifsolution", code blocks marked as solutions
- **Sub-questions**: (a), (b), (c) or a., b., c. parts within a question

**Document organization patterns:**
- Questions separated by blank lines or headings
- Questions numbered sequentially (1, 2, 3... or Exercice 1, Exercice 2...)
- Questions grouped under sections or chapters

### Step 3: Extract Metadata

Extract the following from the document:

1. **exam_name**: The exam title/name (often near the top, after course name)
2. **course_name**: The course name (usually at the very top)
3. **exam_date**: The exam date (format: YYYY-MM-DD)
4. **authors**: Professor/instructor name(s), if present
5. **module**: Module code if present, otherwise omit (defaults to "000")
6. **ue**: UE code if present, otherwise omit (defaults to "000")

**If any metadata is unclear or missing:** Ask the user. For example:
- "I couldn't find the course name in the document. What is the name of the course?"
- "The exam date doesn't appear in a standard format. What date should I use?"

### Step 4: Identify and Extract Questions

Iterate through the document and identify each question:

1. **name**: Question identifier (e.g., "Exercice 1", "Question 1", "Q1")

2. **type**: Determine the question type from the content:
   - Contains code/function definitions → use `python`, `javascript`, `java`, or `cpp`
   - Theoretical or descriptive → use `open`
   
   Look for indicators:
   - Programming keywords: "écrire une fonction", "implement", "codez", "définir"
   - Code blocks with language indicators
   - Ask the user if unsure: "I can't determine the type for Question 1. Is it a coding question or a free-text question?"

3. **description**: The full question text including:
   - The question prompt
   - Any examples or context
   - Sub-questions (a), (b), (c), etc.
   
   Extract until:
   - The next question starts
   - A solution block appears
   - End of document

4. **solution**: 
   - Extract solution content if clearly marked
   - Set to `null` if no solution is provided or unclear

5. **max_points**: Extract point values:
   - Look for patterns: "(2 points)", "[5 pts]", "2pts", "Score: 5"
   - Sum points from all sub-parts of a question
   - If points are unclear: "I found 'Exercice 1 (environ 5 points)' but the exact value isn't specified. What should I use?"

### Step 5: Handle Sub-questions

Include sub-parts within the same question's description. The max_points should be the sum of all sub-parts. Do NOT create separate question entries for sub-questions.

### Step 6: Build the YAML

Construct the YAML object following the exact schema:
- Ensure all numeric values are floats
- Use literal block scalar (`|-`) for every multiline string
- Use `null` (not "null" string) for missing solutions
- Do *NOT* add fields that are not present in the model
- Assign sequential IDs to questions (0, 1, 2, ...)

### Step 7: Save the Output

Write the YAML file. Ask the user where they want to save it, or suggest a filename like `exam_name.yaml` in an appropriate location.

---

## Validation

After creating the YAML, validate it:

```bash
uv run skills/moodle-to-yaml/scripts/validate_exam_yaml.py <path-to-exam.yaml>
```

Fix any issues reported by the validator.

---

## Example Scenarios

### Scenario 1: Simple Text Exam

**Input:** A plain text exam file with questions numbered 1-5.

**Your approach:**
1. Scan document for "Question" or "Exercice" patterns
2. Extract course name from top line
3. Ask user for exam date if not clearly formatted
4. For each question, extract name, description, points
5. Ask user to confirm question types you're unsure about

### Scenario 2: HTML Exam Export

**Input:** An HTML file exported from a learning management system.

**Your approach:**
1. Parse HTML to extract text content
2. Look for table structures that might contain questions
3. Identify question boundaries from layout
4. Extract metadata from headers/footers
5. Ask user for missing information

---

## Tips

- **No format assumptions**: The document could be anything — analyze first, then extract
- **Pattern recognition**: Look for repeating structures that indicate questions
- **Preserve formatting**: Keep code blocks, bullet points, and special formatting in descriptions
- **Point extraction**: Be flexible — "0.2 point", "0.2pts", "0,2 point" all mean 0.2
- **Language handling**: Exams may be in any language — adapt extraction accordingly
- **Don't hallucinate**: If data is missing or unclear, ask the user
- **When uncertain**: Always ask the user for guidance rather than guessing incorrectly
