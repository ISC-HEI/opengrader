#!/usr/bin/env python3
"""
Import student answers into an exam YAML file.

Usage:
    python import_students_response.py <exam_filepath> --students '<json_list>'

Arguments:
    exam_filepath    Path to the destination exam YAML file

Options:
    -s, --students   JSON string containing a list of student dictionaries

Student list format:
    [
        {
            "firstname": "John",
            "lastname": "Doe",
            "submissions": {
                1: "path/to/answer.txt",
                2: "path/to/answer2.py"
            }
        }
    ]

Examples:
    # Basic usage
    python import_students_response.py "./exams/exam.yaml" --students '[{"firstname": "John", "lastname": "Doe", "submissions": {"1": "a.txt"}}]'

    # Multiple students
    python import_students_response.py "./exams/exam.yaml" --students '[{"firstname": "John", "lastname": "Doe", "submissions": {"1": "john/q1.txt"}}, {"firstname": "Jane", "lastname": "Smith", "submissions": {"1": "jane/q1.txt"}}]'

Notes:
    - If the exam file doesn't exist, it will be created
    - If a student (matched by firstname + lastname) already exists, their data will be updated
    - submissions is a dict mapping question_id (number as string) -> answer file path
    - The script reads the content from each answer file and stores it in the answers array
"""

import argparse
import json
from ruamel.yaml import YAML
from pathlib import Path

import argparse
import json
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString


yaml = YAML()
yaml.preserve_quotes = True
yaml.sort_base_mapping_type_on_output = False
yaml.default_flow_style = False


def import_students(exam_filepath: str, students: list):
    exam_path = Path(exam_filepath)

    if not exam_path.exists():
        raise FileNotFoundError(f"Exam file not found: {exam_filepath}")

    with open(exam_path, "r", encoding="utf-8") as f:
        exam_data = yaml.load(f) or {}

    if "student_response" not in exam_data or exam_data["student_response"] is None:
        exam_data["student_response"] = []

    existing_students = {
        s.get("firstname", "") + s.get("lastname", ""): i
        for i, s in enumerate(exam_data["student_response"])
    }

    for student in students:
        key = student.get("firstname", "") + student.get("lastname", "")
        submissions = student.get("submissions", {})

        answers = []
        for question_id_str, filepath in submissions.items():
            question_id = int(question_id_str)
            file_path = Path(filepath)

            assert file_path.exists()

            content = file_path.read_text(encoding="utf-8")

            answers.append(
                {
                    "question_id": question_id,
                    "content": LiteralScalarString(content),
                    "points": None,
                    "correction_details": None,
                }
            )

        student_entry = {
            "firstname": student.get("firstname", ""),
            "lastname": student.get("lastname", ""),
            "answers": answers,
        }

        if key in existing_students:
            exam_data["student_response"][existing_students[key]] = student_entry
        else:
            exam_data["student_response"].append(student_entry)

    exam_path.parent.mkdir(parents=True, exist_ok=True)

    with open(exam_path, "w", encoding="utf-8") as f:
        yaml.dump(exam_data, f)


def main():
    parser = argparse.ArgumentParser(
        description="Import student answers into exam YAML file"
    )
    parser.add_argument("exam_filepath", help="Destination exam YAML file path")
    parser.add_argument(
        "--students", "-s", required=True, help="JSON string of students list"
    )

    args = parser.parse_args()

    students = json.loads(args.students)

    import_students(args.exam_filepath, students)


if __name__ == "__main__":
    main()
