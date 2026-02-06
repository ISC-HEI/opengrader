---
name: inventory
description: Use this skill when starting a new grading session to scan the working directory, identify available files (questions, answers, rubrics), validate completeness, and guide the teacher through next steps. Use this at the beginning of any grading workflow.
---

# Inventory Skill

## Overview

This skill helps you conduct a thorough inventory of the teacher's workspace at the start of a grading session. It scans for files, validates completeness, and presents workflow options.

## When to Use

- At the start of any new grading session
- When the teacher says "I'm ready to start grading"
- When you need to understand what files are available
- Before any other grading operations

## Instructions

### Step 1: Scan the Working Directory

Use the `list_files` or similar tool to scan the working directory for:

1. **Question files**: Look for files that might contain exam questions
   - Markdown files (*.md)
   - LaTeX files (*.tex)
   - PDF files (*.pdf)
   - YAML files (questions.yaml, exam.yaml, etc.)

2. **Answer files**: Look for files that might contain student answers
   - JSON files (answers.json, students.json, etc.)
   - Individual student files (student_*.md, answer_*.txt, etc.)
   - PDF files (scanned exams)

3. **Rubric files**: Look for existing rubrics
   - YAML files (rubric.yaml, grading.yaml, etc.)
   - Markdown files (rubric.md, criteria.md, etc.)

4. **OpenGrader folder**: Check if `opengrader/` subfolder exists
   - If it exists, list its contents (previously generated files)
   - If it doesn't exist, note that it will be created

### Step 2: Analyze and Validate

For each type of file found:

1. **Question files**:
   - Count how many question files exist
   - Try to identify the format (markdown, LaTeX, PDF)
   - If multiple files, ask which one to use

2. **Answer files**:
   - Count how many answer files or individual student answers exist
   - Try to determine the number of students
   - Check if format is consistent

3. **Validation checks**:
   - Do we have at least one question file?
   - Do we have at least one answer file?
   - If we can count questions and answers, do the numbers roughly match?
   - Is there an existing rubric?

### Step 3: Report Findings

Present a clear summary to the teacher:

```
## Inventory Results

### Question Files
- Found: [list files]
- Format: [markdown/LaTeX/PDF]
- Estimated questions: [count if possible]

### Answer Files
- Found: [list files]
- Format: [JSON/individual files/PDF]
- Estimated students: [count]

### Rubric Files
- Found: [list files or "None"]

### OpenGrader Folder
- Status: [exists with X files / will be created]

### Validation
✓ Question file present
✓ Answer files present
⚠ [Any warnings about mismatches or missing files]
```

### Step 4: Prompt for Missing Files

If any critical files are missing:

1. **No question file**: "I couldn't find a question file. Please upload the exam questions (markdown, LaTeX, or PDF format)."

2. **No answer files**: "I couldn't find any student answers. Please upload the answers (JSON file or individual student files)."

3. **Mismatch in counts**: "I found [X] questions but [Y] student answers. This might indicate missing data. Would you like to proceed anyway or upload additional files?"

### Step 5: Present Workflow Options

Once files are validated, present the next steps:

```
## What would you like to do next?

1. **Extract questions**: Parse the question file to create a structured questions.yaml
   - Recommended if you haven't extracted questions yet
   - Will parse markdown/LaTeX and separate questions from solutions

2. **Create rubric**: Build a grading rubric with guided questions
   - Recommended for systematic grading
   - I'll ask you questions about grading criteria and point distribution

3. **Import existing rubric**: Use a rubric you've already created
   - If you have a rubric.yaml or similar file

4. **Grade without rubric**: Provide qualitative feedback only
   - No point assignment, just identify strengths and weaknesses
   - Faster but less structured

Which option would you like to pursue?
```

## Example Interaction

**Teacher**: "I'm ready to start grading."

**Agent** (using this skill):
```
Let me scan your workspace to see what we have...

## Inventory Results

### Question Files
- Found: sql.md
- Format: Markdown with LaTeX
- Estimated questions: 4 (2 paper questions, 2 computer questions)

### Answer Files
- Found: answers.json
- Format: JSON
- Estimated students: 25

### Rubric Files
- Found: None

### OpenGrader Folder
- Status: Will be created

### Validation
✓ Question file present (sql.md)
✓ Answer files present (answers.json with 25 students)
✓ Question count (4) matches answer structure
⚠ No existing rubric found

## What would you like to do next?

1. **Extract questions**: Parse sql.md to create opengrader/questions.yaml
2. **Create rubric**: Build a grading rubric with guided questions
3. **Grade without rubric**: Provide qualitative feedback only

Which option would you like to pursue?
```

## Important Notes

- Always use relative paths from the working directory
- Be helpful and conversational, not robotic
- If you're unsure about a file's purpose, ask the teacher
- Don't make assumptions about file contents without reading them
- Remember that the teacher is always present and can provide clarification
