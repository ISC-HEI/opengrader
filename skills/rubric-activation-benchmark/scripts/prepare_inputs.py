# Reads exam.yaml and pregrade outputs, writes per-question batch JSON files for LLM sub-agents.
# Output: benchmark/inputs/Q1a_batch0.json, Q1a_batch1.json, ...

import argparse
import json
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML


def question_slug(name: str) -> str:
    """Converts a question name like 'Q. 1a' to a filesystem-safe slug 'Q1a'."""
    return re.sub(r"[^A-Za-z0-9]", "", name)


def parse_pregrade_feedback(pregrade_file: Path) -> dict[tuple[str, str], str]:
    """Parse a pregrade markdown file and extract feedback per student.

    Returns dict: {(firstname, lastname): feedback_text}
    """
    if not pregrade_file.exists():
        return {}

    content = pregrade_file.read_text(encoding="utf-8")
    student_feedback = {}

    current_student = None
    current_feedback_lines = []

    for line in content.split("\n"):
        # Look for "## Lastname, Firstname" pattern
        if line.startswith("## "):
            # Save previous student if exists
            if current_student:
                student_feedback[current_student] = "\n".join(
                    current_feedback_lines
                ).strip()

            # Parse new student name
            name_part = line[3:].strip()  # Remove "## "
            if "," in name_part:
                lastname, firstname = name_part.split(",", 1)
                current_student = (firstname.strip(), lastname.strip())
            else:
                current_student = (name_part.strip(), "")
            current_feedback_lines = []
        elif current_student and line.strip():
            current_feedback_lines.append(line)
        elif current_student and not line.strip():
            # Empty line between sections - continue collecting
            if current_feedback_lines:
                current_feedback_lines.append(line)

    # Save last student
    if current_student:
        student_feedback[current_student] = "\n".join(current_feedback_lines).strip()

    return student_feedback


def main():
    parser = argparse.ArgumentParser(
        description="Prepare per-question batch input files for rubric-activation sub-agents."
    )
    parser.add_argument("exam_yaml", help="Path to the exam.yaml file")
    parser.add_argument("pregrade_dir", help="Path to pregrade output directory")
    parser.add_argument("benchmark_dir", help="Path to benchmark directory")
    parser.add_argument(
        "--batch-size", type=int, default=10, help="Students per batch (default: 10)"
    )
    args = parser.parse_args()

    exam_path = Path(args.exam_yaml)
    if not exam_path.exists():
        print(f"Error: {exam_path} not found", file=sys.stderr)
        sys.exit(1)

    pregrade_path = Path(args.pregrade_dir)
    if not pregrade_path.exists():
        print(f"Error: {pregrade_path} not found", file=sys.stderr)
        sys.exit(1)

    benchmark_path = Path(args.benchmark_dir)
    benchmark_path.mkdir(parents=True, exist_ok=True)
    (benchmark_path / "inputs").mkdir(parents=True, exist_ok=True)
    (benchmark_path / "outputs").mkdir(parents=True, exist_ok=True)

    yaml = YAML()
    with open(exam_path) as f:
        exam = yaml.load(f)

    questions = exam.get("questions", [])
    students = exam.get("student_response", [])

    created = []
    skipped_no_rubric = []
    skipped_no_pregrade = []

    for question in questions:
        q_id = question["id"]
        slug = question_slug(str(question["name"]))

        rubrics = question.get("rubrics") or []
        if not rubrics:
            skipped_no_rubric.append(slug)
            continue

        pregrade_file = pregrade_path / f"{slug}.md"
        feedback_map = parse_pregrade_feedback(pregrade_file)

        if not feedback_map:
            skipped_no_pregrade.append(slug)
            continue

        # Collect and sort answers for this question
        student_data = []
        for student in students:
            key = (student["firstname"], student["lastname"])
            feedback = feedback_map.get(key, "")

            answer = next(
                (a for a in student.get("answers", []) if a["question_id"] == q_id),
                None,
            )
            student_data.append(
                {
                    "firstname": student["firstname"],
                    "lastname": student["lastname"],
                    "answer": answer["content"] if answer else None,
                    "pregrade_feedback": feedback,
                }
            )

        # Sort alphabetically by last name, then first name
        student_data.sort(key=lambda s: (s["lastname"].lower(), s["firstname"].lower()))

        total_batches = max(
            1, (len(student_data) + args.batch_size - 1) // args.batch_size
        )

        for batch_num, offset in enumerate(
            range(0, len(student_data), args.batch_size)
        ):
            batch_students = student_data[offset : offset + args.batch_size]

            payload = {
                "question": {
                    "id": q_id,
                    "name": str(question["name"]),
                    "type": question.get("type"),
                    "max_points": question.get("max_points"),
                    "rubrics": rubrics,
                },
                "batch": batch_num,
                "total_batches": total_batches,
                "students": batch_students,
            }

            out_file = benchmark_path / "inputs" / f"{slug}_batch{batch_num}.json"
            out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
            created.append(out_file)
            print(f"  {out_file}")

    print(f"\nCreated {len(created)} input file(s) in {benchmark_path}/inputs/")

    if skipped_no_pregrade:
        print(
            f"Skipped {len(skipped_no_pregrade)} question(s) due to missing pregrade feedback: {', '.join(skipped_no_pregrade)}"
        )

    return created


if __name__ == "__main__":
    main()
