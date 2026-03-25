import argparse
import csv
import sys
from pathlib import Path

from ruamel.yaml import YAML


def validate_csv_files(yaml_path: str, csv_files: list[str]) -> list[str]:
    errors = []
    yaml = YAML()
    with open(yaml_path) as f:
        data = yaml.load(f)

    questions = data.get("questions", [])
    student_responses = data.get("student_response", [])

    num_questions = len(questions)
    num_csv_files = len(csv_files)

    if num_csv_files != num_questions:
        errors.append(
            f"Number of CSV files ({num_csv_files}) does not match number of questions ({num_questions})"
        )
        return errors

    question_ids = {q["id"] for q in questions}
    expected_names = {f"{qid}_generated.csv" for qid in question_ids}
    csv_basenames = {Path(f).name for f in csv_files}

    missing = expected_names - csv_basenames
    if missing:
        errors.append(f"Missing CSV files: {', '.join(sorted(missing))}")

    extra = csv_basenames - expected_names
    if extra:
        errors.append(
            f"Unexpected CSV files (not matching question IDs): {', '.join(sorted(extra))}"
        )

    if errors:
        return errors

    csv_row_counts = {}
    for csv_file in csv_files:
        with open(csv_file) as f:
            reader = csv.reader(f)
            next(reader, None)
            row_count = sum(1 for _ in f)
        csv_row_counts[csv_file] = row_count

    unique_row_counts = set(csv_row_counts.values())
    if len(unique_row_counts) > 1:
        counts_str = ", ".join(
            f"{Path(f).name}: {c}" for f, c in csv_row_counts.items()
        )
        errors.append(f"CSV files have different row counts: {counts_str}")

    expected_row_count = len(student_responses)
    actual_row_count = next(iter(unique_row_counts), None)

    if actual_row_count is not None and actual_row_count != expected_row_count:
        errors.append(
            f"CSV row count ({actual_row_count}) does not match student_response count ({expected_row_count})"
        )

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate CSV files against exam YAML questions"
    )
    parser.add_argument("input", help="Path to the exam YAML file")
    parser.add_argument(
        "--files",
        nargs="*",
        help="CSV files to validate (format: <question_id>_generated.csv)",
    )
    args = parser.parse_args()

    if not args.files:
        print("Error: --files argument is required")
        sys.exit(1)

    errors = validate_csv_files(args.input, args.files)

    if errors:
        print(f"Validation FAILED for {args.input}:")
        for error in errors:
            print(f"  ✗ {error}")
        sys.exit(1)
    else:
        print(f"Validation passed for {args.input}")
        sys.exit(0)


if __name__ == "__main__":
    main()
