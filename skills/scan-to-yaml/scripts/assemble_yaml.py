# Assembles the final exam YAML from per-student-question JSON extractions.
# Reads scan_results/q{id}_{login}.json files and populates student_response in exam.yaml.

import argparse
import json
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString


def main():
    parser = argparse.ArgumentParser(
        description="Assemble final exam YAML from extracted answer JSONs."
    )
    parser.add_argument("exam_yaml", help="Path to exam.yaml (question catalog, no student answers)")
    parser.add_argument("scan_results", help="Path to scan_results/ directory")
    parser.add_argument("--output", help="Output YAML path (default: exam_yaml parent / <stem>_answers.yaml)")
    args = parser.parse_args()

    exam_yaml_path = Path(args.exam_yaml)
    scan_results_path = Path(args.scan_results)

    yaml = YAML()
    with open(exam_yaml_path) as f:
        exam = yaml.load(f)

    with open(scan_results_path / "students.json") as f:
        students = json.load(f)

    question_ids = [q["id"] for q in exam.get("questions", [])]

    student_response = []
    missing = []

    for student in students:
        sid = student["student_id"]
        if sid is None:
            print(
                f"Skipping unmatched student: {student['firstname']} {student['lastname']}",
                file=sys.stderr,
            )
            continue

        answers = []
        for qid in question_ids:
            json_path = scan_results_path / f"q{qid}_{sid}.json"
            if not json_path.exists():
                missing.append(json_path.name)
                continue
            with open(json_path) as f:
                data = json.load(f)
            answers.append(
                {
                    "question_id": qid,
                    "content": LiteralScalarString(data.get("content", "")),
                    "points": None,
                    "correction_details": None,
                }
            )

        student_response.append(
            {
                "firstname": student["firstname"],
                "lastname": student["lastname"],
                "answers": answers,
            }
        )

    if missing:
        print(f"Warning: {len(missing)} answer file(s) missing:", file=sys.stderr)
        for m in missing:
            print(f"  {m}", file=sys.stderr)

    exam["student_response"] = student_response

    output_path = (
        Path(args.output)
        if args.output
        else exam_yaml_path.parent / f"{exam_yaml_path.stem}_answers.yaml"
    )

    with open(output_path, "w") as f:
        yaml.dump(exam, f)

    print(
        f"Assembled {len(student_response)} students × {len(question_ids)} questions → {output_path}"
    )


if __name__ == "__main__":
    main()
