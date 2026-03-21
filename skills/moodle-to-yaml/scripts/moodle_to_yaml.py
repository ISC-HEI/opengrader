# Converts Moodle HTML responses + CSV grades into a partial exam YAML skeleton.
# Handles all structural extraction; question descriptions/types must be filled in manually.

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString


def _literal(s: str) -> LiteralScalarString:
    return LiteralScalarString(s)


def load_dataframe(html_path: Path, csv_path: Path) -> tuple[pd.DataFrame, str | None]:
    """Parse HTML answers and CSV grades, merge by row index into one DataFrame.

    Returns the merged DataFrame and the exam name extracted from the HTML title.
    Column layout after merge: [metadata...] [answer cols] [grade cols ending in ' /X']
    """
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Exam name from <title>
    title_tag = soup.find("title")
    exam_name = title_tag.get_text(strip=True) if title_tag else None
    if exam_name:
        exam_name = re.sub(r"-(réponses|responses)$", "", exam_name, flags=re.IGNORECASE).strip()

    # HTML table → DataFrame
    table = soup.find("table")
    if not table:
        raise ValueError(f"No <table> found in {html_path}")
    rows = table.find_all("tr")
    headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]
    data = [
        [td.get_text(separator="\n").strip() for td in row.find_all("td")]
        for row in rows[1:]
        if row.find_all("td")
    ]
    df_answers = pd.DataFrame(data, columns=headers)

    # CSV grades → DataFrame (drop last row which is the totals row)
    df_grades = pd.read_csv(csv_path, encoding="utf-8-sig")
    df_grades.drop(index=df_grades.index[-1], inplace=True)

    # Merge: add only grade columns not already present in the answers DataFrame
    cols_to_add = df_grades.columns.difference(df_answers.columns, sort=False)
    df_all = pd.merge(
        df_answers,
        df_grades[cols_to_add],
        left_index=True,
        right_index=True,
        how="outer",
    )
    # Sort by lastname (col 0)
    df_all.sort_values(by=df_all.columns[0], inplace=True, ignore_index=True)

    return df_all, exam_name


def to_yaml_data(df: pd.DataFrame, exam_name: str | None) -> dict:
    """Convert merged DataFrame into the exam YAML structure.

    Grade columns are detected by the ' /' pattern (e.g. 'Q. 1a /0,80').
    Answer columns are the N columns immediately to the left of the grade columns.
    Lastname and firstname are assumed to be columns 0 and 1.
    """
    all_cols = list(df.columns)

    grade_cols = [c for c in all_cols if " /" in c]
    if not grade_cols:
        raise ValueError("No grade columns found. Expected headers like 'Q. 1 /5.00'.")
    n = len(grade_cols)

    grade_start = all_cols.index(grade_cols[0])
    answer_cols = all_cols[grade_start - n : grade_start]

    questions = []
    for i, gc in enumerate(grade_cols):
        name, max_pts_str = gc.rsplit("/", 1)
        questions.append(
            {
                "id": i,
                "name": name.strip(),
                "type": None,
                "description": None,
                "max_points": float(max_pts_str.strip().replace(",", ".")),
                "solution": None,
                "unit_tests": None,
            }
        )

    student_responses = []
    for _, row in df.iterrows():
        lastname = str(row.iloc[0]).strip()
        firstname = str(row.iloc[1]).strip()

        answers = []
        for i, (ac, gc) in enumerate(zip(answer_cols, grade_cols)):
            raw = row.get(ac)
            content = str(raw).strip() if pd.notna(raw) and str(raw).strip() else None

            points = None
            grade_val = row.get(gc)
            if pd.notna(grade_val):
                try:
                    points = float(str(grade_val).replace(",", "."))
                except ValueError:
                    pass  # not yet graded or blank → stays None

            answers.append(
                {
                    "question_id": i,
                    "content": _literal(content) if content else None,
                    "points": points,
                    "correction_details": None,
                }
            )

        student_responses.append(
            {
                "lastname": lastname,
                "firstname": firstname,
                "answers": answers,
            }
        )

    return {
        "exam_name": exam_name or "FILL_IN",
        "course_name": "FILL_IN",
        "exam_date": "FILL_IN",
        "questions": questions,
        "student_response": student_responses,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Moodle HTML responses + CSV grades to a partial exam YAML."
    )
    parser.add_argument("html", help="Path to the *-réponses.html or *-responses.html file")
    parser.add_argument("csv", help="Path to the *-notes.csv file")
    parser.add_argument("output", nargs="?", help="Output YAML path (default: auto-derived)")
    args = parser.parse_args()

    html_path = Path(args.html)
    csv_path = Path(args.csv)

    if args.output:
        output_path = Path(args.output)
    else:
        stem = re.sub(r"-(réponses|responses)$", "", html_path.stem, flags=re.IGNORECASE)
        output_path = html_path.parent / f"{stem}.yaml"

    df, exam_name = load_dataframe(html_path, csv_path)
    data = to_yaml_data(df, exam_name)

    yaml = YAML()
    yaml.default_flow_style = False
    yaml.width = 4096
    yaml.best_sequence_indent = 2

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

    n_q = len([c for c in df.columns if " /" in c])
    print(f"Written: {output_path}")
    print(f"  Questions: {n_q}")
    print(f"  Students:  {len(df)}")
    print()
    print("Remaining steps for the LLM:")
    print("  1. Fill in course_name and exam_date (ask the user)")
    print("  2. Provide description for each question")
    print("  3. Set type for each question: python / javascript / java / cpp / open")


if __name__ == "__main__":
    main()
