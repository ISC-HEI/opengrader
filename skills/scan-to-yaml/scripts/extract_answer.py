# Extracts one student's answer to one question from scanned exam pages via Gemini vision.
# Output: scan_results/q{question_id}_{student_id}.json  (skipped if already exists)

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


def parse_json(text: str | None) -> dict:
    """Parse JSON from a response that may include markdown code fences."""
    if text is None:
        raise ValueError("Empty response from model")
    text = text.strip()
    if text.startswith("```"):
        text = text[text.index("\n") + 1 :]
        if "```" in text:
            text = text[: text.rindex("```")]
    return json.loads(text.strip())


def main():
    parser = argparse.ArgumentParser(
        description="Extract one student's answer to one question from scanned pages."
    )
    parser.add_argument("--exam", required=True, help="Path to exam.yaml")
    parser.add_argument(
        "--layout", required=True, help="Path to scan_results/layout.json"
    )
    parser.add_argument(
        "--students", required=True, help="Path to scan_results/students.json"
    )
    parser.add_argument("--student-id", required=True, help="Student login/ID")
    parser.add_argument(
        "--question-id", required=True, type=int, help="Question ID (integer)"
    )
    parser.add_argument(
        "--folder", required=True, help="Exam folder containing scan PDFs"
    )
    parser.add_argument(
        "--output", help="Output JSON path (default: scan_results/q{id}_{login}.json)"
    )
    args = parser.parse_args()

    folder = Path(args.folder)
    output_path = (
        Path(args.output)
        if args.output
        else folder / "scan_results" / f"q{args.question_id}_{args.student_id}.json"
    )

    if output_path.exists():
        print(f"Skipping {output_path.name} (already exists)")
        return

    yaml = YAML()
    with open(args.exam) as f:
        exam = yaml.load(f)
    with open(args.layout) as f:
        layout = json.load(f)
    with open(args.students) as f:
        students = json.load(f)

    question = next((q for q in exam["questions"] if q["id"] == args.question_id), None)
    if question is None:
        print(
            f"Error: question id {args.question_id} not found in exam.yaml",
            file=sys.stderr,
        )
        sys.exit(1)

    student = next((s for s in students if s["student_id"] == args.student_id), None)
    if student is None:
        print(
            f"Error: student '{args.student_id}' not found in students.json",
            file=sys.stderr,
        )
        sys.exit(1)

    q_data = layout["questions"].get(str(args.question_id))
    if not q_data or not q_data.get("exam_pages"):
        print(
            f"Error: question {args.question_id} has no pages in layout.json",
            file=sys.stderr,
        )
        sys.exit(1)

    # exam_pages and start_page are both 1-indexed; convert to 0-indexed for fitz
    exam_pages = q_data["exam_pages"]
    scan_page_indices = [(student["start_page"] - 1) + (ep - 1) for ep in exam_pages]

    scan_path = folder / student["scan_file"]

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    content = [
        {
            "type": "text",
            "text": (
                f"You are extracting a student's handwritten answer from a scanned exam.\n\n"
                f"Question (id={args.question_id}, name={question['name']}):\n"
                f"{question['description']}\n\n"
                f"The image(s) below show the relevant page(s) from the student's exam copy.\n"
                f"Transcribe the student's handwritten answer verbatim and in full, exactly as written.\n"
                f"- The professor will read your transcription to verify it against the original scan, so accuracy is critical.\n"
                f"- Preserve all structure: checkboxes (checked/unchecked), tables, code, diagrams described in text, line breaks.\n"
                f"- Include crossed-out or corrected text (e.g. '~~wrong~~ correct').\n"
                f"- For drawings or diagrams (e.g. automata), describe them in structured text as faithfully as possible.\n"
                f"- Mark illegible parts with [?].\n"
                f"- Do NOT summarize, paraphrase, or omit anything.\n"
                f'- Set "uncertain" to true if significant parts are illegible or ambiguous.\n\n'
                f'Return ONLY a JSON object: {{"content": "...", "uncertain": false}}'
            ),
        }
    ]

    for page_idx in scan_page_indices:
        b64 = page_to_jpeg_b64(scan_path, page_idx)
        content.append(
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
        )

    raw = (
        client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": content}],
        )
        .choices[0]
        .message.content
    )

    try:
        result = parse_json(raw)
    except (json.JSONDecodeError, KeyError) as e:
        print(
            f"Warning: failed to parse JSON response ({e}), storing raw text",
            file=sys.stderr,
        )
        result = {"content": raw, "uncertain": True}

    output_data = {
        "student_id": args.student_id,
        "question_id": args.question_id,
        "content": result.get("content", ""),
        "uncertain": result.get("uncertain", False),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    flag = " [UNCERTAIN]" if output_data["uncertain"] else ""
    print(f"Saved {output_path.name}{flag}")


if __name__ == "__main__":
    main()
