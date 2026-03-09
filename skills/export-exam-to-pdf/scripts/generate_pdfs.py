import argparse
import glob
import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from datetime import date as Date
from os import mkdir, path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader
from pypdf import PdfReader
from ruamel.yaml import YAML


@dataclass
class Answer:
    question_id: int
    content: str
    points: Optional[int]
    correction_details: Optional[str]


@dataclass
class Question:
    id: int
    name: str
    description: str
    type: str
    linebreak: int
    answer: Optional[Answer]


@dataclass
class Exam:
    name: str
    date: Date
    questions: List[Question]
    authors: List[str]
    add_anchors: bool

    def __init__(self, data):
        self.name = data["exam_name"]
        self.date = data["exam_date"]
        self.authors = data["authors"]
        self.questions = []
        for q in data["questions"]:
            self.questions.append(
                Question(
                    id=q["id"],
                    name=q["name"],
                    description=q["description"],
                    type=q["type"],
                    answer=None,
                    linebreak=0,
                )
            )


@dataclass
class FilledExam(Exam):
    firstname: str
    lastname: str

    def __init__(
        self, data, firstname: str, lastname: str, answers: List[Answer]
    ):
        super().__init__(data)
        self.firstname = firstname
        self.lastname = lastname
        for q in self.questions:
            for a in answers:
                if a.question_id == q.id:
                    q.answer = a

    @staticmethod
    def from_yaml(data, add_anchors=False):
        res = [
            FilledExam(
                data, firstname="Template", lastname="Template", answers=[]
            )
        ]
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


def find_questions_in_pdf(pdf_path: str) -> dict[int, int]:
    """Find question markers (Q0, Q1, Q2...) in a single PDF.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Dict mapping question number -> page number (1-indexed)
        Example: {0: 1, 1: 3, 2: 5}

    """
    questions = {}
    reader = PdfReader(pdf_path)

    q_num = 0

    # We loop until no more question are found
    while True:
        q_num += 1
        pattern_start = f"Q{q_num}:start"
        pattern_end = f"Q{q_num}:end"
        page_num_start = None
        page_num_end = None

        for idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and pattern_start in text:
                page_num_start = idx

            if text and pattern_end in text:
                page_num_end = idx

            if page_num_start is not None and page_num_end is not None:
                break

        if page_num_start is not None:
            assert page_num_end is not None
            questions[q_num] = page_num_end - page_num_start
        else:
            break  # no more questions found

    return questions


def generate_exam(data: List[FilledExam], output_folder):
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("./models/template.jinja2")

    working_folder = f"/tmp/{uuid.uuid1()}"

    mkdir(working_folder)

    try:

        def generate(add_anchors):
            for d in data:
                d.add_anchors = add_anchors
                content = template.render(exam=d)
                base = d.firstname + "_" + d.lastname
                markdown_filename = base + ".md"
                markdown_filepath = path.join(working_folder, markdown_filename)

                with open(
                    markdown_filepath,
                    "w",
                ) as f:
                    f.write(content)
                subprocess.run(
                    ["isc-build-pandoc", "-i", markdown_filename],
                    cwd=working_folder,
                    stdout=subprocess.DEVNULL,
                )

        pages = []
        maxes = {}

        # We generate the markdown -> pdfs with the anchors
        generate(True)

        for d in data:
            base = d.firstname + "_" + d.lastname
            pdf_filepath = path.join(working_folder, base + ".pdf")
            page_n = find_questions_in_pdf(pdf_filepath)
            pages.append(page_n)
            for key, value in page_n.items():
                if not key in maxes or maxes[key] < value:
                    maxes[key] = value

        # This loop adds the right number of pagebreak to every exams.
        for e, p in zip(data, pages, strict=True):
            for i, q in enumerate(e.questions):
                q.linebreak = maxes[i] - p[i]

        # We then re-generate the markdown -> pdfs, but without the anchors this time
        generate(False)

        # Moving the generated files to the destination

        for pdf_path in glob.glob(os.path.join(working_folder, "*.pdf")):
            shutil.move(pdf_path, output_folder)

        # Removing the working folder
    finally:
        print("Cleaned working folder")
        subprocess.run(["rm", "-r", working_folder])

    print(f"Generated {len(data)} pdf files")


def load_yaml(filepath: str):
    yaml = YAML()
    with open(filepath, "r") as f:
        data = yaml.load(f)

    filled_exams = FilledExam.from_yaml(data)

    return filled_exams


def main():
    parser = argparse.ArgumentParser(
        description="Generate markdown files from exam YAML data"
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Path to input YAML file"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Path to output folder"
    )
    args = parser.parse_args()

    generate_exam(load_yaml(args.input), args.output)


if __name__ == "__main__":
    main()
