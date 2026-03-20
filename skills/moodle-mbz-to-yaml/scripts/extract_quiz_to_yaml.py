#!/usr/bin/env python3
"""
Moodle Quiz XML to YAML Extractor

Extracts quiz data from Moodle XML export and produces a YAML file
matching the exam schema. Outputs missing fields summary for manual completion.
"""

import argparse
import os
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.scalarstring import LiteralScalarString


SCRIPT_DIR = Path(__file__).parent.resolve()
DEFAULT_SCHEMA_PATH = SCRIPT_DIR.parent / "assets" / "schema.yaml"


def parse_schema(schema_path: str | Path | None = None) -> dict:
    """Parse schema.yaml to extract required fields."""
    if schema_path is None:
        schema_path = DEFAULT_SCHEMA_PATH
    yaml_parser = YAML()
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml_parser.load(f)
    return schema


def find_missing_fields(data: dict, schema: dict) -> list:
    """Find fields that need manual completion based on schema."""
    missing = []

    def check_required(obj: dict, path: str, required_fields: list):
        for field in required_fields:
            field_path = f"{path}.{field}" if path else field
            if field not in obj or obj[field] is None:
                missing.append(field_path)
            elif isinstance(obj[field], list) and field in schema.get("properties", {}):
                items_schema = schema["properties"][field].get("items", {})
                if isinstance(items_schema, dict):
                    item_required = items_schema.get("required", [])
                    for idx, item in enumerate(obj[field]):
                        if isinstance(item, dict):
                            item_path = f"{field_path}[{idx}]"
                            check_required(item, item_path, item_required)

    schema_required = schema.get("required", [])
    check_required(data, "", schema_required)

    return missing


def parse_users_xml(users_path: str) -> dict:
    """Parse users.xml to build userid -> {firstname, lastname} mapping."""
    users = {}
    tree = ET.parse(users_path)
    root = tree.getroot()

    for user in root.findall(".//user"):
        user_id = user.get("id")
        if user_id:
            firstname = user.findtext("firstname", "").strip()
            lastname = user.findtext("lastname", "").strip()
            if firstname or lastname:
                users[user_id] = {"firstname": firstname, "lastname": lastname}

    return users


def parse_quiz_xml(quiz_path: str) -> dict:
    """Parse quiz.xml to extract quiz metadata, questions, and attempts."""
    tree = ET.parse(quiz_path)
    root = tree.getroot()

    quiz = root.find(".//quiz")
    exam_name = quiz.findtext("name", "").strip()
    intro = quiz.findtext("intro", "").strip()
    timeopen = quiz.findtext("timeopen", "")
    timelimit = quiz.findtext("timelimit", "0")

    exam_date = None
    if timeopen:
        try:
            exam_date = datetime.fromtimestamp(int(timeopen)).strftime("%Y-%m-%d")
        except:
            pass

    questions = OrderedDict()

    for attempt in root.findall(".//attempt"):
        for q_attempt in attempt.findall(".//question_attempt"):
            slot = q_attempt.findtext("slot", "")
            maxmark = q_attempt.findtext("maxmark", "0")
            questionsummary = q_attempt.findtext("questionsummary", "").strip()

            if slot and slot not in questions:
                questions[slot] = {
                    "text": questionsummary,
                    "max_points": float(maxmark) if maxmark else 0.0,
                }

    students_data = []

    for attempt in root.findall(".//attempt"):
        userid = attempt.findtext("userid", "")
        attemptnum = attempt.findtext("attemptnum", "1")
        timestart = attempt.findtext("timestart", "")
        state = attempt.findtext("state", "")

        answers = []
        for q_attempt in attempt.findall(".//question_attempt"):
            slot = q_attempt.findtext("slot", "")

            content = None
            for step in q_attempt.findall(".//step"):
                response_elem = step.find('.//variable[@name="answer"]')
                if response_elem is not None:
                    content = response_elem.findtext("value", "").strip()
                    break

            if not content:
                responsesummary = q_attempt.findtext("responsesummary", "").strip()
                if responsesummary:
                    content = responsesummary

            if content:
                try:
                    question_id = int(slot) - 1
                except:
                    question_id = 0

                answers.append(
                    {
                        "question_id": question_id,
                        "content": LiteralScalarString(content),
                        "points": None,
                        "correction_details": None,
                    }
                )

        students_data.append(
            {
                "userid": userid,
                "attemptnum": attemptnum,
                "timestart": timestart,
                "state": state,
                "answers": answers,
            }
        )

    return {
        "exam_name": exam_name,
        "intro": intro,
        "exam_date": exam_date,
        "timelimit": timelimit,
        "questions": questions,
        "students_data": students_data,
    }


def build_yaml_output(quiz_data: dict, users: dict) -> dict:
    """Build the YAML output structure matching the schema."""
    questions_list = []
    for idx, (slot, q_data) in enumerate(quiz_data["questions"].items()):
        questions_list.append(
            {
                "name": f"Q. {idx + 1}",
                "id": idx,
                "type": "open",
                "description": LiteralScalarString(q_data["text"])
                if q_data["text"]
                else None,
                "max_points": q_data["max_points"],
                "solution": None,
                "unit_tests": None,
            }
        )

    student_responses = []
    for attempt in quiz_data["students_data"]:
        userid = attempt["userid"]
        user_info = users.get(userid, {})

        if not user_info.get("firstname") and not user_info.get("lastname"):
            print(f"Warning: No user info found for userid {userid}")

        student_responses.append(
            {
                "firstname": user_info.get("firstname", ""),
                "lastname": user_info.get("lastname", ""),
                "answers": attempt["answers"],
            }
        )

    output = {
        "exam_name": quiz_data["exam_name"],
        "course_name": None,
        "exam_date": quiz_data["exam_date"],
        "authors": [],
        "questions": questions_list,
        "student_response": student_responses,
    }

    return output


def main():
    parser = argparse.ArgumentParser(description="Extract Moodle quiz to YAML")
    parser.add_argument("--quiz", required=True, help="Path to quiz.xml")
    parser.add_argument("--users", required=True, help="Path to users.xml")
    parser.add_argument("--output", required=True, help="Output YAML path")
    args = parser.parse_args()

    print(f"Parsing schema from: {DEFAULT_SCHEMA_PATH}")
    schema = parse_schema()

    print(f"Parsing users from: {args.users}")
    users = parse_users_xml(args.users)
    print(f"Found {len(users)} users")

    print(f"Parsing quiz from: {args.quiz}")
    quiz_data = parse_quiz_xml(args.quiz)
    print(f"Found quiz: {quiz_data['exam_name']}")
    print(f"Found {len(quiz_data['questions'])} unique questions")
    print(f"Found {len(quiz_data['students_data'])} attempts")

    output = build_yaml_output(quiz_data, users)

    yaml = YAML()
    yaml.default_flow_style = False
    yaml.preserve_quotes = True

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f)
    print(f"Wrote YAML to: {output_path}")

    missing = find_missing_fields(output, schema)
    if missing:
        print("\n=== MISSING FIELDS (need manual completion) ===")
        for field in missing:
            print(f"  - {field}")
    else:
        print("\nAll fields populated successfully!")

    return 0


if __name__ == "__main__":
    exit(main())
