---
name: rubric-precision-benchmark
description: Benchmark the precision of rubric precision benchmarking
---
# Rubric precision benchmark

This skill allow the generation of a benchmark to evaluate the precision of rubric based correction.

# Required Inputs

As input, a YAML exam file should be provided. This file should contains :
- **Student submissions:** One or more student submissions to base the benchmark on
- **Questions solution:** The official answer for the questions to benchmark
- **Question rubrics:** The rubric to base the correction on for each question

If not mentionned, generate the benchmark for every questions with all those pre-requisites filled. If mentionned, only generate the benchmark for the questions asked by the user.

# Core instructions and Rules of engagement

Your are a teacher trying to grade student submissions. Your role is to apply the rubrics of each question to every student submission.

Assign rubrics the fairest possible between students. As those are technical exams, do not count spelling errors, and the given solution might not be the only valid one ! If the student solution works too, do NOT remove points arbitrarily, only care about simplicity/efficience if mentionned in the rubrics.

Append you results to the output file for each question. Do not wait until the end to write everything in a single step. Each time you append a new text to the file, leave a comment anchors at the end of the edit, this will allow you to target your next edit with precision. The anchors should follow this format : `# Anchors: Q<Question name>`

# Progress tracking

To keep track of the progress made, use the tool to create a todo list containing one element per question, and a last element to validate the file

Ex :
- Question 1.1
- Question 1.2
- Question 2.1
- ...
- ...
- File validation

Keep this todo list up-to-date by writing which step has been done

# Output format

You will ouptut a `.yaml` file to the user requested location. If the user did not mention a location, ask for it.

The format will be the following :

```yaml
questions:
  - id: <question_id>
    name: <question_name>
    positive_scoring: <true|false>
    students_results:
      - firstname: <student_firstname>
        lastname: <student_lastname>
        rubrics:
          - rubric_description: <rubric description>
            rubric_value: <rubric_value>
            rubric_obtained: <true|false>
      - firstname: <student_firstname>
        lastname: <student_lastname>
        # ...
```

# Validation

To validate the generated file, you can use the script located here : `./scripts/output_validator.py`. The script usage is as follows :
```bash
uv run ./scripts/output_validator.py <path_to_generated_yaml_file>
```

# Next steps

Once this file is generated, ask the user if he want to continue by running the benchmarking.
If the user accepts, you will need an additionnal input : 
- **Path to the exported gradescope folder:** A path leading to a folder containing the exported corrections from gradescope.

In this folder, there is one file per exam question, you will then need to match each filename with the question in the YAML file.
