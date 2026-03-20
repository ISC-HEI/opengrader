#!/usr/bin/env python3
"""
Validates the output YAML file structure for rubric precision benchmarking.
"""

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML


def validate_yaml(file_path: str) -> list[str]:
    """Validate the YAML file structure and return list of errors."""
    errors = []

    yaml_parser = YAML()
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml_parser.load(f)

    if "questions" not in data:
        errors.append("Missing 'questions' key in root")
        return errors

    questions = data["questions"]
    if not isinstance(questions, list):
        errors.append("'questions' must be a list")
        return errors

    student_counts = []
    for q_idx, question in enumerate(questions):
        if not isinstance(question, dict):
            errors.append(f"Question {q_idx} is not a dictionary")
            continue

        if "students_results" not in question:
            errors.append(f"Question {q_idx}: missing 'students_results'")
            continue

        students_results = question["students_results"]
        if not isinstance(students_results, list):
            errors.append(f"Question {q_idx}: 'students_results' must be a list")
            continue

        student_counts.append(len(students_results))

        for s_idx, student in enumerate(students_results):
            if not isinstance(student, dict):
                errors.append(
                    f"Question {q_idx}, Student {s_idx}: must be a dictionary"
                )
                continue

            required_fields = ["firstname", "lastname", "rubrics"]
            for field in required_fields:
                if field not in student or student[field] is None:
                    errors.append(
                        f"Question {q_idx}, Student {s_idx}: missing or empty '{field}'"
                    )

            if "rubrics" in student and isinstance(student["rubrics"], list):
                rubric_count = len(student["rubrics"])
                for r_idx, rubric in enumerate(student["rubrics"]):
                    if not isinstance(rubric, dict):
                        errors.append(
                            f"Question {q_idx}, Student {s_idx}, Rubric {r_idx}: must be a dictionary"
                        )
                        continue

                    rubric_fields = [
                        "rubric_description",
                        "rubric_value",
                        "rubric_obtained",
                    ]
                    for field in rubric_fields:
                        if field not in rubric or rubric[field] is None:
                            errors.append(
                                f"Question {q_idx}, Student {s_idx}, Rubric {r_idx}: missing or empty '{field}'"
                            )

    if len(set(student_counts)) > 1:
        errors.append(
            f"Students count mismatch across questions: {student_counts} (counts must be equal)"
        )

    rubric_counts_by_question = []
    for q_idx, question in enumerate(questions):
        if "students_results" not in question:
            continue
        rubric_counts = []
        for student in question["students_results"]:
            if "rubrics" in student and isinstance(student["rubrics"], list):
                rubric_counts.append(len(student["rubrics"]))
        if rubric_counts:
            rubric_counts_by_question.append((q_idx, rubric_counts))

    for q_idx, rubric_counts in rubric_counts_by_question:
        if len(set(rubric_counts)) > 1:
            errors.append(
                f"Question {q_idx}: rubric count mismatch across students: {rubric_counts}"
            )

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate rubric benchmark output YAML file"
    )
    parser.add_argument("yaml_file", help="Path to the YAML file to validate")
    args = parser.parse_args()

    file_path = Path(args.yaml_file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    errors = validate_yaml(str(file_path))

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    else:
        print("Validation passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
