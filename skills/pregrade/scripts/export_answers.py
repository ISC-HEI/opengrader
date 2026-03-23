# Reads exam.yaml and writes each student answer to a separate file per question.
# Output: code/Q1a/Lastname_Firstname.py, code/Q1b/Lastname_Firstname.txt, ...

import argparse
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

EMPTY_ANSWER_PLACEHOLDER = "(no answer from student to this question)"

EXTENSIONS = {
    "python": "py",
    "javascript": "js",
    "java": "java",
    "cpp": "cpp",
    "open": "txt",
}


def question_slug(name: str) -> str:
    """Converts a question name like 'Q. 1a' to a filesystem-safe slug 'Q1a'."""
    return re.sub(r"[^A-Za-z0-9]", "", name)


def main():
    parser = argparse.ArgumentParser(
        description="Export student answers to individual files, one per question per student."
    )
    parser.add_argument("exam_yaml", help="Path to the exam.yaml file")
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

    output_root = exam_path.parent / "code"
    total_files = 0

    for question in questions:
        q_id = question["id"]
        slug = question_slug(str(question["name"]))
        ext = EXTENSIONS.get(question.get("type", ""), "txt")

        q_dir = output_root / slug
        q_dir.mkdir(parents=True, exist_ok=True)

        for student in students:
            lastname = student["lastname"].strip()
            firstname = student["firstname"].strip()
            filename = f"{firstname}_{lastname}.{ext}"

            answer = next(
                (a for a in student.get("answers", []) if a["question_id"] == q_id),
                None,
            )
            content = (answer["content"] if answer and answer.get("content") else None) or EMPTY_ANSWER_PLACEHOLDER

            (q_dir / filename).write_text(content, encoding="utf-8")
            total_files += 1

        print(f"  {slug}/  ({len(students)} files, .{ext})")

    print(f"\nExported {total_files} file(s) to {output_root.relative_to(exam_path.parent)}/")


if __name__ == "__main__":
    main()
