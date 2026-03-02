from dataclasses import dataclass
from datetime import date as Date
from os import path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader
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
    answer: Optional[Answer]


@dataclass
class Exam:
    name: str
    date: Date
    questions: List[Question]
    authors: List[str]

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
    def from_yaml(data):
        res = []
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


def generate_exam(data: List[FilledExam], output_folder):
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("./models/template.jinja2")

    print(f"Generating {len(data)} markdown")

    for d in data:
        content = template.render(exam=d)
        with open(
            path.join(output_folder, d.firstname + "_" + d.lastname + ".md"),
            "w",
        ) as f:
            f.write(content)


def load_yaml(filepath: str):
    yaml = YAML()
    with open(filepath, "r") as f:
        data = yaml.load(f)

    filled_exams = FilledExam.from_yaml(data)

    return filled_exams


generate_exam(load_yaml("./exams/cc_2/cc_2.yaml"), "./exams/cc_2/")
