# Validates an exam YAML file against the bundled schema (assets/schema.yaml).
# Exits with code 0 on success, 1 on failure with actionable error messages.

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML

SCHEMA_PATH = Path(__file__).parent.parent / "models" / "schema.yaml"


def _required(node: dict) -> list[str]:
    return node.get("required", []) if node else []


def _items(node: dict) -> dict:
    return node.get("items", {}) if node else {}


def load_schema(path: Path) -> dict:
    yaml = YAML()
    with open(path) as f:
        return yaml.load(f)


def validate(filepath: str, schema_path: Path = SCHEMA_PATH) -> list[str]:
    schema = load_schema(schema_path)
    yaml = YAML()
    with open(filepath) as f:
        data = yaml.load(f)

    errors = []
    props = schema.get("properties", {})

    # Top-level required fields
    for field in _required(schema):
        if field not in data or data[field] is None:
            errors.append(f"Missing required field: '{field}'")

    if errors:
        return errors

    # questions[*] required fields
    question_required = _required(_items(props.get("questions", {})))
    for i, q in enumerate(data.get("questions") or []):
        for field in question_required:
            if field not in q:
                errors.append(f"questions[{i}]: missing required field '{field}'")

    # student_response[*] required fields
    # Note: in the schema, student_response is defined at document root, not inside properties
    sr_schema = props.get("student_response") or schema.get("student_response", {})
    sr_items = _items(sr_schema)
    sr_required = _required(sr_items)
    for i, s in enumerate(data.get("student_response") or []):
        for field in sr_required:
            if field not in s:
                errors.append(
                    f"student_response[{i}]: missing required field '{field}'"
                )

        # answers[*] required fields
        answers_schema = (sr_items.get("properties") or {}).get("answers", {})
        answer_required = _required(_items(answers_schema))
        for j, a in enumerate(s.get("answers") or []):
            for field in answer_required:
                if field not in a:
                    errors.append(
                        f"student_response[{i}].answers[{j}]: missing required field '{field}'"
                    )

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate an exam YAML file against the schema"
    )
    parser.add_argument("input", help="Path to the exam YAML file")
    args = parser.parse_args()

    errors = validate(args.input)

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
