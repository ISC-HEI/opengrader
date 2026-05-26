import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from datetime import date as DateObj, datetime
from os import mkdir, path
from typing import List, Optional
from jinja2 import Environment, FileSystemLoader
from md2typst import convert as md2typst_convert
from pypdf import PdfReader
from ruamel.yaml import YAML


def convert_code_blocks(text):
    def replace_code_block(match):
        lang = match.group(1) or ""
        code = match.group(2)
        code = code.rstrip()
        if lang:
            return f"#code(\n```{lang}\n{code}\n```\n)"
        else:
            return f"#code(\n```{code}\n```\n)"

    pattern = r"```(\w*)\n(.*?)```"
    return re.sub(pattern, replace_code_block, text, flags=re.DOTALL)


def markdown_to_typst(text):
    if not text:
        return ""
    # Strip a leading level-1 heading (the template already renders q.name as a heading)
    text = re.sub(r"^#[^#][^\n]*\n?", "", text.lstrip("\n"), count=1)
    result = md2typst_convert(text)
    result = convert_code_blocks(result)
    return result


@dataclass
class Answer:
    question_id: int
    content: str
    points: Optional[int]
    correction_details: Optional[str]
    test_results: Optional[dict] = None


@dataclass
class Question:
    id: int
    name: str
    description: str
    type: str
    max_point: Optional[float]
    linebreak: int
    answer: Optional[Answer]


@dataclass
class Exam:
    name: str
    date: DateObj
    questions: List[Question]
    authors: List[str]
    add_anchors: bool
    module: str
    ue: str
    course: str
    firstname: str = ""
    lastname: str = ""

    def __init__(self, data):
        self.name = data["exam_name"]
        exam_date_raw = data["exam_date"]
        if isinstance(exam_date_raw, DateObj):
            self.date = exam_date_raw
        elif isinstance(exam_date_raw, str):
            try:
                self.date = datetime.strptime(exam_date_raw, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(
                    f"Invalid exam date format: '{exam_date_raw}'. "
                    "Expected format: YYYY-MM-DD (e.g., 2025-05-20)"
                )
        else:
            raise ValueError(
                f"Invalid exam date type: {type(exam_date_raw).__name__}. "
                "Expected a date object or a string in YYYY-MM-DD format."
            )
        self.authors = data["authors"]
        self.module = data.get("module", "000")
        self.ue = data.get("ue", "000")
        self.course = data.get("course_name", "")
        self.questions = []
        for q in data["questions"]:
            self.questions.append(
                Question(
                    id=q["id"],
                    name=q["name"],
                    description=q["description"],
                    type=q["type"],
                    max_point=q.get("max_points"),
                    answer=None,
                    linebreak=0,
                )
            )


@dataclass
class FilledExam(Exam):
    def __init__(self, data, firstname: str, lastname: str, answers: List[Answer]):
        super().__init__(data)
        self.firstname = firstname
        self.lastname = lastname
        for q in self.questions:
            for a in answers:
                if a.question_id == q.id:
                    q.answer = a

    @staticmethod
    def from_yaml(data, add_anchors=False):
        res = [FilledExam(data, firstname="", lastname="", answers=[])]
        data["add_anchors"] = add_anchors
        for s in data["student_response"]:
            answers = []
            for a in s["answers"]:
                answers.append(Answer(**a))
            res.append(
                FilledExam(
                    data=data,
                    firstname=s["firstname"],
                    lastname=s["lastname"],
                    answers=answers,
                )
            )
        return res


def find_questions_in_pdfs(folder_path: str) -> dict[str, dict[int, int]]:
    """Find question markers (Q0, Q1, Q2...) in all PDFs within a folder.

    Args:
        folder_path: Path to folder containing PDF files

    Returns:
        Dict mapping PDF filename -> {question_number: page_number}
        Example: {"exam1.pdf": {0: 1, 1: 3, 2: 5}, "exam2.pdf": {0: 1}}

    """
    results = {}
    pdf_files = sorted(glob.glob(os.path.join(folder_path, "*.pdf")))

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        results[filename] = find_questions_in_pdf(pdf_path)

    return results


def find_questions_in_pdf(pdf_path: str, num_questions: int) -> dict[int, int]:
    """Find question markers in PDF and calculate page spans.

    Args:
        pdf_path: Path to PDF file
        num_questions: Total number of questions

    Returns:
        Dict mapping question number -> page span (number of pages)
        Example: {0: 1, 1: 2, 2: 1}
    """
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    question_pages = {}

    for q_num in range(num_questions):
        pattern = f"Q{q_num}:start"
        page_num = None

        for idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and pattern in text:
                page_num = idx
                break

        if page_num is not None:
            question_pages[q_num] = page_num

    questions = {}

    for q_num in range(num_questions):
        if q_num not in question_pages:
            questions[q_num] = 0
            continue

        start_page = question_pages[q_num]

        if q_num < num_questions - 1:
            next_q_page = None
            for next_q in range(q_num + 1, num_questions):
                if next_q in question_pages:
                    next_q_page = question_pages[next_q]
                    break

            if next_q_page:
                end_page = next_q_page - 1
            else:
                end_page = total_pages - 1
        else:
            end_page = total_pages - 1

        questions[q_num] = end_page - start_page + 1

    return questions


def generate_exam(data: List[FilledExam], output_folder, template_path: str):
    env = Environment(loader=FileSystemLoader("."))
    env.filters["markdown_to_typst"] = markdown_to_typst
    template = env.get_template(template_path)

    working_folder = f"/tmp/{uuid.uuid1()}"

    mkdir(working_folder)

    try:

        def generate(add_anchors):
            for d in data:
                d.add_anchors = add_anchors
                content = template.render(exam=d)
                base = d.firstname + "_" + d.lastname
                typst_filename = base + ".typ"
                typst_filepath = path.join(working_folder, typst_filename)

                with open(typst_filepath, "w") as f:
                    f.write(content)

                result = subprocess.run(
                    ["typst", "compile", typst_filename],
                    cwd=working_folder,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                if result.returncode != 0:
                    sys.stderr.write(
                        f"WARNING: typst failed for {typst_filename}: {result.stderr[:500]}\n"
                    )

        pages = []
        maxes = {}

        generate(True)

        num_questions = len(data[0].questions)

        for d in data:
            base = d.firstname + "_" + d.lastname
            pdf_filepath = path.join(working_folder, base + ".pdf")
            page_n = find_questions_in_pdf(pdf_filepath, num_questions)
            pages.append(page_n)
            for key, value in page_n.items():
                if not key in maxes or maxes[key] < value:
                    maxes[key] = value

        for e, p in zip(data, pages, strict=True):
            for i, q in enumerate(e.questions):
                q.linebreak = maxes[i] - p[i]

        generate(False)

        os.makedirs(output_folder, exist_ok=True)
        for pdf_path in glob.glob(os.path.join(working_folder, "*.pdf")):
            dst = path.join(output_folder, path.basename(pdf_path))
            if path.exists(dst):
                os.remove(dst)
            shutil.move(pdf_path, output_folder)

    finally:
        subprocess.run(["rm", "-r", working_folder])

    print(f"Generated {len(data)} PDFs to {output_folder}")


def load_yaml(filepath: str, test_results_path: Optional[str] = None):
    yaml = YAML()
    with open(filepath, "r") as f:
        data = yaml.load(f)

    filled_exams = FilledExam.from_yaml(data)

    if test_results_path:
        with open(test_results_path) as f:
            test_results = json.load(f)
        for exam in filled_exams:
            key = f"{exam.firstname}_{exam.lastname}"
            if key in test_results:
                student_results = test_results[key]
                for q in exam.questions:
                    if q.answer and str(q.id) in student_results:
                        q.answer.test_results = student_results[str(q.id)]

    return filled_exams


def main():
    parser = argparse.ArgumentParser(
        description="Generate PDF files from exam YAML data using Typst"
    )
    parser.add_argument("-i", "--input", required=True, help="Path to input YAML file")
    parser.add_argument("-o", "--output", required=True, help="Path to output folder")
    parser.add_argument(
        "-t",
        "--template",
        default="./models/template.typst.jinja2",
        help="Path to Typst Jinja2 template",
    )
    parser.add_argument(
        "--test-results",
        default=None,
        help="Path to test_results.json produced by run_tests.py",
    )
    args = parser.parse_args()

    generate_exam(load_yaml(args.input, args.test_results), args.output, args.template)


if __name__ == "__main__":
    main()
