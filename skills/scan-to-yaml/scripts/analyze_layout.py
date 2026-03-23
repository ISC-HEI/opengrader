# Analyzes exam PDF page layout and maps each question to its page number(s).
# Output: scan_results/layout.json

import argparse
import base64
import json
import os
import sys
from pathlib import Path

import fitz
from openai import OpenAI
from ruamel.yaml import YAML

MODEL = "google/gemini-3-flash-preview"


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


def ask_gemini(client: OpenAI, prompt: str, image_b64: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ],
    )
    return response.choices[0].message.content


def main():
    parser = argparse.ArgumentParser(
        description="Map exam questions to their page numbers in the exam PDF."
    )
    parser.add_argument("exam_yaml", help="Path to exam.yaml")
    parser.add_argument("exam_pdf", help="Path to exam statement PDF (e.g. cc_2026.pdf)")
    parser.add_argument("--output", help="Output layout.json path")
    args = parser.parse_args()

    exam_yaml_path = Path(args.exam_yaml)
    exam_pdf_path = Path(args.exam_pdf)
    output_path = (
        Path(args.output)
        if args.output
        else exam_pdf_path.parent / "scan_results" / "layout.json"
    )

    yaml = YAML()
    with open(exam_yaml_path) as f:
        exam = yaml.load(f)

    questions = exam.get("questions", [])
    question_list = [{"id": q["id"], "name": q["name"]} for q in questions]

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    doc = fitz.open(exam_pdf_path)
    n_pages = len(doc)
    doc.close()

    question_pages: dict[int, list[int]] = {q["id"]: [] for q in questions}

    prompt_template = (
        "You are analyzing one page of a printed exam.\n"
        "The exam contains these questions (id → name):\n"
        "{question_list}\n\n"
        "Look at page {page_num} and identify which question IDs have content on this page.\n"
        "A question 'has content' if its header, body text, or answer space appears on this page.\n"
        "Return ONLY a JSON object, e.g.: {{\"question_ids\": [0, 2]}}\n"
        "If no questions appear, return: {{\"question_ids\": []}}"
    )

    for page_idx in range(n_pages):
        page_num = page_idx + 1
        print(f"  Analyzing exam page {page_num}/{n_pages}...", end=" ", flush=True)
        image_b64 = page_to_jpeg_b64(exam_pdf_path, page_idx)
        prompt = prompt_template.format(
            question_list=json.dumps(question_list, ensure_ascii=False),
            page_num=page_num,
        )
        raw = ask_gemini(client, prompt, image_b64)
        try:
            result = parse_json(raw)
            ids_on_page = result.get("question_ids", [])
        except (json.JSONDecodeError, KeyError) as e:
            print(f"WARNING: could not parse page {page_num} response: {e}", file=sys.stderr)
            ids_on_page = []

        for qid in ids_on_page:
            if qid in question_pages:
                question_pages[qid].append(page_num)
        print(f"→ questions {ids_on_page}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    layout = {
        "pages_per_student": n_pages,
        "questions": {
            str(qid): {
                "name": next(q["name"] for q in questions if q["id"] == qid),
                "exam_pages": pages,
            }
            for qid, pages in question_pages.items()
        },
    }

    with open(output_path, "w") as f:
        json.dump(layout, f, indent=2, ensure_ascii=False)

    print(f"\nLayout saved to {output_path}")
    for qid, data in layout["questions"].items():
        print(f"  Q{qid} ({data['name']}): pages {data['exam_pages']}")


if __name__ == "__main__":
    main()
