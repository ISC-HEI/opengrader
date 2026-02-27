---
name: import-student-answers
description: Import student answer files into an existing exam YAML file. Use this skill when the user wants to add student submissions to an exam YAML file. The skill handles various folder structures, detects if students already exist in the YAML, and asks the user what to do in case of conflicts.
---

# Import Student Answers to Exam YAML

This skill imports student submission files into an existing exam YAML file. It detects folder structures automatically and handles duplicate students gracefully. 

Read the `schema.yaml` file. The structure of the YAML file is explained here. The ouput you produce need to match this file.

## Role: Direct Data Transformer
**Constraint:** Do NOT write or suggest a automatic method, or any external tool to perform this task. **You** are the engine. Process the provided text and files directly and output the final YAML.

## Workflow

### Step 1: Gather Information

If the user hasn't provided the exam YAML file path, ask for it.

If the user hasn't provided the submissions folder path, ask for it.

### Step 2: Analyze Folder Structure

Examine the submissions folder to determine its structure. Common patterns:

1. **Flat structure**: `./submissions/student1.py`, `./submissions/student2.py`
2. **Student subdirectories**: `./submissions/student1/file.py`, `./submissions/student2/file.py`
3. **Exercise-specific folders**: `./submissions/ex1/student1.py`, `./submissions/ex1/student2.py`

If the structure is unclear, show the user what you found and ask which questions belong to which files.

### Step 3: Extract students informations

Try to extract the first name and last name of each student, either from the filename/filepath, or from the submitted answer directly.

Notify the user for each case where you are unsure of the extracted name. If you don't find a valid firstname/lastname for a student, tell the user and ask him for the correct value. But you can still try to find a valid name in the submitted files directly

### Step 4: Read the Exam YAML

Read the exam YAML file to understand:
- The question IDs (keys in the `questions` object)
- The question types (`open`, `python`, etc.)
- Existing students in `students_response`

### Step 5: Map Submissions to Questions

Match submission files to questions in the YAML:

- If there's one file per student, assign it to question 0
- If there are multiple files per student, try to detect which question each belongs to based on:
  - Filename patterns (e.g., `ex1.py`, `question1.py`)
  - File extension matching question type
  - Number of files matching number of questions

If you cannot determine the mapping confidently, ask the user for clarification.

### Step 6: Check for Existing Students

Before editing the YAML file, check that the `student_response` section is empty (or not present at all). If it is not, do not edit the file directly, ask for the user what to do.
The actions to be taken could be :
- Replace: Empty the actual `student_response` and fill it with the new content. Be very clear that this option will REMOVE anything already present in this field
- Cancel : Do nothing and stop here
- Merge: Try to add the new student submissions to the `student_response` field, if you find that you have the same student two times (same first and lastname), tell the user and ask what to do (keep the one already in the file and skip the new one, or replace the current one with the new entry. Be very clear on each options, with their consequences)


### Step 7: Use script to import submissions into YAML file

For this step, the `import_students_response.py` script should be used.

To use it, you need 2 parameters :
- YAML destination filepath -> this correspond to the YAML exam file.
- A JSON string of a list of student dictionnary following this format :

```json
[
    {
        "firstname": "John",
        "lastname": "Doe",
        "submissions": {
            "1": "path/to/answer1.txt",
            "2": "path/to/answer2.py",
            <Question id>: <Path to answer>,
            ...
        }
    }
]
```

Use the extracted firstname/lastname of Step 3 to fill in those parameters

This script will add every student submission you give it into the yaml file.

#### Basic usage
python import_students_response.py "./exams/exam.yaml" --students '[{"firstname": "John", "lastname": "Doe", "submissions": {"1": "a.txt"}}]'

#### Multiple students
python import_students_response.py "./exams/exam.yaml" --students '[{"firstname": "John", "lastname": "Doe", "submissions": {"1": "john/q1.txt"}}, {"firstname": "Jane", "lastname": "Smith", "submissions": {"1": "jane/q1.txt"}}]'

### Step 8: Validate

Checks :
- Check that every students present in the submission folder was correctly imported. If there is student missing, import them.
- Check that the `firstname` and `lastname` you parsed make sense (ex `asdaf` is not a name). If one field is wrong, tell the user and ask for guidance
- Check that each student have a answer for each question. If an answer is missing, tell the user and ask for guidance
- Check that the YAML still follow the schema given in `schema.yaml`


## Example

User says: "Import student answers from ./submissions to exam.yaml"

You:
1. Ask for the exam.yaml path (if not provided)
2. Discover folder structure: `./submissions/JohnDoe/ex1.py`, `./submissions/JohnDoe/ex2.py`
3. Read exam.yaml, see questions "0" and "1"
4. Map ex1.py → question "0", ex2.py → question "1"
5. Check if John Doe exists in students_response
6. Add student with their answers
7. Save and summarize

## Edge Cases

- **Empty folder**: Tell the user no submission files were found
- **No matching questions**: If a student submits 3 files but exam has 2 questions, ask for clarification
- **Invalid JSON**: If the exam file is corrupted, report the error and don't modify it
- **Read-only files**: If you can't write to the JSON file, report the error
