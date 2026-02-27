---
name: import-unit-tests
description: Import unit tests from a folder into an exam JSON file. Use this skill when the user wants to add unit test code to questions in an existing exam JSON file. The user will provide a folder containing unit test files and an exam JSON file.
---

# Import Unit Tests into Exam JSON

This skill imports unit test code from files in a folder into an existing exam JSON file.

## Workflow

### Step 1: Gather Information

Ask the user for:
1. **Path to the exam YAML file** (if not already provided)
2. **Path to the folder containing unit tests** (if not already provided)

### Step 2: Scan the Unit Tests Folder

List all files in the unit tests folder. Identify the file format (e.g., `.py`, `.js`, `.txt`).

### Step 3: Read the Exam YAML

Load the exam YAML and examine its questions. Note:
- Question IDs (keys in `questions` object)
- Question names
- Which questions already have `unit_tests` filled in

### Step 4: Match Unit Tests to Questions

Try to match each unit test file to a question using these methods:

1. **Filename matching**: Look for patterns like `test_0.py`, `question_1.py`, `ex1.py`, etc., where the number corresponds to a question ID
2. **Content matching**: Read the file content and look for function names that match the question's expected function (e.g., if question asks for `get_proba`, look for test files testing `get_proba`)
3. **Manual confirmation**: If a match is unclear, ASK the user. DO NOT guess.

Present your matching proposal to the user before proceeding:
```
I propose to match these files to questions:
- test_ex1.py → Question 0 (get_proba)
- test_ex2.py → Question 1 (plan_tour) 
- test_ex3.py → Question 2 (solve_level)
```

Wait for user confirmation before making any changes.

### Step 5: Handle Conflicts

If a question already has `unit_tests` populated:
- Inform the user clearly: "Question X already has unit tests. What would you like to do?"
- Present options:
  - **Overwrite**: Replace existing unit tests with the new ones
  - **Skip**: Keep existing tests, ignore new ones

Wait for user decision before proceeding.

### Step 6: Import the Unit Tests

After confirmation:
1. Read each matched unit test file
2. Copy the content as a string
3. Find the question wih the correct id
3. Update the exam YAML: `questions[<matching question id>].content = <file_content>`
4. Save the modified YAML file

### Step 7: Report Results

Summarize what was done:
- Which files were imported
- Which questions were updated
- Any conflicts that were resolved (and how)

## Output Format

The skill modifies the exam YAML file in place. No additional files are created.

## Edge Cases

- **Empty folder**: Inform the user that no unit test files were found
- **No matching files**: Inform the user and ask for guidance on how to match files to questions
- **Invalid YAML**: Report the error and do not modify the file
