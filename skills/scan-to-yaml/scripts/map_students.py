# Identifies students in scan PDFs by reading handwritten names, matches against Excel list.
# Output: scan_results/students.json

import argparse
import base64
import json
import os
import sys
from difflib import get_close_matches
from pathlib import Path

import fitz
import pandas as pd
from openai import OpenAI

MODEL = "google/gemini-3-flash-preview"

PROMPT_READ_NAME = (
    "This is the first page of a student's handwritten exam.\n"
    "The page has printed fields 'Nom :' (last name) and 'Prénom :' (first name) "
    "with handwritten entries next to them.\n"
    "Read the handwritten name carefully.\n"
    "Return ONLY a JSON object: {\"lastname\": \"...\", \"firstname\": \"...\"}\n"
    "If you cannot read a field, use null for that field."
)


def page_to_jpeg_b64(pdf_path: Path, page_idx: int) -> str:
    doc = fitz.open(pdf_path)
    page = doc[page_idx]
    pix = page.get_pixmap(dpi=150)
    doc.close()
    return base64.b64encode(pix.tobytes("jpeg")).decode()


def parse_json(text: str) -> dict:
    """Parse JSON from a response that may include markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        text = text[text.index("\n") + 1 :]
        if "```" in text:
            text = text[: text.rindex("```")]
    return json.loads(text.strip())


def load_student_list(excel_path: Path) -> list[dict]:
    """Load Excel student list, auto-detecting name and login columns."""
    df = pd.read_excel(excel_path, engine="openpyxl")
    cols_lower = [c.lower().strip() for c in df.columns]

    def find_col(candidates: list[str]) -> str | None:
        for c in candidates:
            if c in cols_lower:
                return df.columns[cols_lower.index(c)]
        return None

    login_col = find_col(["login", "username", "identifiant"])
    firstname_col = find_col(["firstname", "first_name", "prénom", "prenom"])
    lastname_col = find_col(["lastname", "last_name", "nom", "surname"])

    if not (firstname_col and lastname_col):
        print("Could not auto-detect name columns. Available columns:", list(df.columns), file=sys.stderr)
        print("Expected columns like: firstname/prénom, lastname/nom", file=sys.stderr)
        sys.exit(1)

    students = []
    for _, row in df.iterrows():
        firstname = str(row[firstname_col]).strip()
        lastname = str(row[lastname_col]).strip()
        if login_col:
            student_id = str(row[login_col]).strip()
        else:
            student_id = f"{firstname.lower()}.{lastname.lower()}"
        students.append({"student_id": student_id, "firstname": firstname, "lastname": lastname})
    return students


def fuzzy_match(lastname: str, firstname: str, student_list: list[dict]) -> dict | None:
    """Find the best match in the student list by full name similarity."""
    query = f"{lastname} {firstname}".lower().strip()
    names = [f"{s['lastname']} {s['firstname']}".lower() for s in student_list]
    matches = get_close_matches(query, names, n=1, cutoff=0.5)
    if matches:
        return student_list[names.index(matches[0])]
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Identify students in scan PDFs by reading handwritten names."
    )
    parser.add_argument("folder", help="Exam folder containing scan PDFs")
    parser.add_argument("students_excel", help="Excel file with student list")
    parser.add_argument(
        "--pages-per-student",
        type=int,
        default=None,
        help="Pages per student exam (auto-read from layout.json if omitted)",
    )
    parser.add_argument("--output", help="Output students.json path")
    args = parser.parse_args()

    folder = Path(args.folder)
    output_path = (
        Path(args.output) if args.output else folder / "scan_results" / "students.json"
    )

    pages_per_student = args.pages_per_student
    layout_path = folder / "scan_results" / "layout.json"
    if pages_per_student is None and layout_path.exists():
        with open(layout_path) as f:
            pages_per_student = json.load(f).get("pages_per_student", 8)
    elif pages_per_student is None:
        pages_per_student = 8

    print(f"Pages per student: {pages_per_student}")

    student_list = load_student_list(Path(args.students_excel))
    print(f"Loaded {len(student_list)} students from Excel")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    scan_files = sorted(
        p for p in folder.glob("*.pdf")
        if not p.name.startswith("__") and p.name.startswith("scan")
    )

    students = []
    unmatched = []

    for scan_file in scan_files:
        doc = fitz.open(scan_file)
        n_pages = len(doc)
        doc.close()

        n_students = n_pages // pages_per_student
        print(f"\n{scan_file.name}: {n_pages} pages → {n_students} students")

        for i in range(n_students):
            start_page = i * pages_per_student + 1  # 1-indexed
            cover_page_idx = i * pages_per_student  # 0-indexed for fitz

            print(f"  Student {i + 1}/{n_students} (starts page {start_page})...", end=" ", flush=True)

            image_b64 = page_to_jpeg_b64(scan_file, cover_page_idx)
            raw = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT_READ_NAME},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                        ],
                    }
                ],
            ).choices[0].message.content

            try:
                result = parse_json(raw)
                lastname = (result.get("lastname") or "").strip()
                firstname = (result.get("firstname") or "").strip()
            except (json.JSONDecodeError, KeyError):
                lastname, firstname = "", ""

            print(f"→ '{firstname} {lastname}'", end=" ", flush=True)

            match = fuzzy_match(lastname, firstname, student_list)
            entry = {
                "student_id": match["student_id"] if match else None,
                "firstname": match["firstname"] if match else firstname,
                "lastname": match["lastname"] if match else lastname,
                "scan_file": scan_file.name,
                "start_page": start_page,
            }
            students.append(entry)

            if match:
                print(f"→ matched: {match['student_id']}")
            else:
                unmatched.append(entry)
                print("→ UNMATCHED")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(students, f, indent=2, ensure_ascii=False)

    print(f"\nStudents saved to {output_path}")
    print(f"  Matched: {len(students) - len(unmatched)}/{len(students)}")
    if unmatched:
        print(f"  UNMATCHED ({len(unmatched)}):")
        for u in unmatched:
            print(f"    '{u['firstname']} {u['lastname']}' in {u['scan_file']} p.{u['start_page']}")
        print("\nFix unmatched entries in students.json before proceeding to extract_answer.py.")


if __name__ == "__main__":
    main()
