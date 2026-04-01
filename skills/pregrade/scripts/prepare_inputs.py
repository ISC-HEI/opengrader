# Reads exam.yaml and writes per-question, per-batch JSON files for LLM sub-agents.
# Output: pregrade/inputs/Q1a_batch0.json, Q1a_batch1.json, ...

import argparse
import json
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML


def question_slug(name: str) -> str:
    """Converts a question name like 'Q. 1a' to a filesystem-safe slug 'Q1a'."""
    return re.sub(r"[^A-Za-z0-9]", "", name)


def main():
    parser = argparse.ArgumentParser(
        description="Prepare per-question batch input files for pregrade sub-agents."
    )
    parser.add_argument("exam_yaml", help="Path to the exam.yaml file")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Students per batch (default: 10)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for pregrade files (default: <exam_yaml_parent>/pregrade)",
    )
    args = parser.parse_args()

    exam_path = Path(args.exam_yaml)
    if not exam_path.exists():
        print(f"Error: {exam_path} not found", file=sys.stderr)
        sys.exit(1)

    yaml = YAML()
    with open(exam_path) as f:
        exam = yaml.load(f)

    questions = exam.get("questions", [])
    students = exam.get("student_response", [])

    base_dir = args.output_dir or exam_path.parent / "pregrade"
    output_dir = base_dir / "inputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "outputs").mkdir(parents=True, exist_ok=True)

    created = []

    for question in questions:
        q_id = question["id"]
        slug = question_slug(str(question["name"]))

        student_answers = []
        for student in students:
            answer = next(
                (
                    a
                    for a in student.get("answers", [])
                    if a["question_id"] == q_id
                ),
                None,
            )
            student_answers.append(
                {
                    "firstname": student["firstname"],
                    "lastname": student["lastname"],
                    "answer": answer["content"] if answer else None,
                }
            )
        student_answers.sort(
            key=lambda s: (s["firstname"].lower(), s["lastname"].lower())
        )

        total_batches = max(
            1, (len(student_answers) + args.batch_size - 1) // args.batch_size
        )

        for batch_num, offset in enumerate(
            range(0, len(student_answers), args.batch_size)
        ):
            batch_students = student_answers[offset : offset + args.batch_size]

            payload = {
                "question": {
                    "name": str(question["name"]),
                    "description": question.get("description"),
                    "type": question.get("type"),
                    "max_points": question.get("max_points"),
                    "solution": question.get("solution"),
                    "rubrics": question.get("rubric"),
                },
                "batch": batch_num,
                "total_batches": total_batches,
                "students": batch_students,
            }

            out_file = output_dir / f"{slug}_batch{batch_num}.json"
            out_file.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False)
            )
            created.append(out_file)
            print(f"  {out_file}")

    pregrade_dir = exam_path.parent / "pregrade"
    print(f"\nCreated {len(created)} input file(s) in {output_dir}/")
    print(f"Pregrade directory: {pregrade_dir}")
    return created


if __name__ == "__main__":
    main()
