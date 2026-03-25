# Validates that all rubric-activation benchmark outputs are complete and consistent.

import argparse
import json
import sys
from pathlib import Path

from ruamel.yaml import YAML


def question_slug(name: str) -> str:
    import re

    return re.sub(r"[^A-Za-z0-9]", "", name)


def main():
    parser = argparse.ArgumentParser(
        description="Validate rubric-activation benchmark outputs."
    )
    parser.add_argument("exam_yaml", help="Path to the exam.yaml file")
    parser.add_argument("benchmark_dir", help="Path to benchmark directory")
    parser.add_argument("pregrade_dir", help="Path to pregrade output directory")
    args = parser.parse_args()

    exam_path = Path(args.exam_yaml)
    if not exam_path.exists():
        print(f"Error: {exam_path} not found", file=sys.stderr)
        sys.exit(1)

    benchmark_path = Path(args.benchmark_dir)
    pregrade_path = Path(args.pregrade_dir)

    yaml = YAML()
    with open(exam_path) as f:
        exam = yaml.load(f)

    questions = exam.get("questions", [])
    students = exam.get("student_response", [])
    inputs_dir = benchmark_path / "inputs"
    outputs_dir = benchmark_path / "outputs"
    activations_dir = benchmark_path / "activations"

    errors = []

    # Check 1: All input batches should have matching output files
    input_files = sorted(inputs_dir.glob("*_batch*.json"))
    for inp in input_files:
        out = outputs_dir / f"{inp.stem}.json"
        if not out.exists():
            errors.append(f"Missing output for input: {inp.name}")

    # Check 2: Each activation file should exist for each question with both rubrics AND pregrade feedback
    # (activation files are only created for questions that have pregrade outputs)
    expected_questions = [q for q in questions if q.get("rubrics")]
    activated_files = sorted(activations_dir.glob("*.json"))

    questions_with_feedback = []
    for q in expected_questions:
        slug = question_slug(str(q["name"]))
        if (pregrade_path / f"{slug}.md").exists():
            questions_with_feedback.append(q)

    if len(activated_files) != len(questions_with_feedback):
        errors.append(
            f"Expected {len(questions_with_feedback)} activation files (questions with rubrics AND pregrade feedback), found {len(activated_files)}"
        )

    # Check 3: Each activation file should contain correct number of students
    expected_students = len(students)
    for act_file in activated_files:
        data = json.loads(act_file.read_text())
        actual_students = len(data.get("students", []))
        if actual_students != expected_students:
            errors.append(
                f"{act_file.name}: expected {expected_students} students, got {actual_students}"
            )

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        sys.exit(1)

    print(
        f"Validation passed! {len(activated_files)} questions, {expected_students} students each."
    )


if __name__ == "__main__":
    main()
