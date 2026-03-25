# Flight check: verifies that pregrade outputs are complete and consistent with exam.yaml.
# Checks batch coverage, JSON validity, question file count, and per-file student count.

import argparse
import json
import sys
from pathlib import Path

from ruamel.yaml import YAML


def main():
    parser = argparse.ArgumentParser(
        description="Validate pregrade outputs against the source exam.yaml."
    )
    parser.add_argument("exam_yaml", help="Path to the exam.yaml file")
    args = parser.parse_args()

    exam_path = Path(args.exam_yaml)
    pregrade_dir = exam_path.parent / "pregrade"
    inputs_dir = pregrade_dir / "inputs"
    outputs_dir = pregrade_dir / "outputs"

    yaml = YAML()
    with open(exam_path) as f:
        exam = yaml.load(f)

    expected_questions = len(exam.get("questions", []))
    expected_students = len(exam.get("student_response", []))

    errors = []

    print(f"Exam:              {exam_path.name}")
    print(f"Expected questions: {expected_questions}")
    print(f"Expected students:  {expected_students}")
    print()

    # --- Check 1: every input batch has a matching, valid output ---
    input_files = sorted(inputs_dir.glob("*_batch*.json"))
    output_files = {f.name for f in outputs_dir.glob("*_batch*.json")}

    missing_outputs = [f.name for f in input_files if f.name not in output_files]
    if missing_outputs:
        for name in missing_outputs:
            errors.append(f"Missing output for batch: {name}")

    for output_file in sorted(outputs_dir.glob("*_batch*.json")):
        try:
            json.loads(output_file.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            errors.append(f"Invalid JSON in {output_file.name}: {e}")

    if not missing_outputs:
        print(f"✓ All {len(input_files)} batch outputs present and valid JSON")

    # --- Check 2: assembled .md file count matches question count ---
    md_files = sorted(pregrade_dir.glob("*.md"))
    if len(md_files) != expected_questions:
        errors.append(
            f"Expected {expected_questions} assembled .md files, found {len(md_files)}: "
            + ", ".join(f.name for f in md_files)
        )
    else:
        print(f"✓ {len(md_files)} question file(s) assembled")

    # --- Check 3: student count in each .md matches expected ---
    for md_file in md_files:
        text = md_file.read_text()
        # Count level-2 headings — each represents one student
        student_sections = [line for line in text.splitlines() if line.startswith("## ")]
        count = len(student_sections)
        if count != expected_students:
            errors.append(
                f"{md_file.name}: expected {expected_students} students, found {count}"
            )

    if not errors:
        print(f"✓ All {len(md_files)} files contain exactly {expected_students} students")

    # --- Report ---
    print()
    if errors:
        print(f"FAILED — {len(errors)} error(s):")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print("All checks passed. Pregrade outputs are complete.")


if __name__ == "__main__":
    main()
