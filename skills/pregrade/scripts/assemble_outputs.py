# Merges per-batch JSON outputs from sub-agents into per-question Markdown files.
# Output: pregrade/Q1a.md, pregrade/Q1b.md, ...

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Assemble sub-agent batch outputs into per-question Markdown files."
    )
    parser.add_argument("pregrade_dir", help="Path to the pregrade/ directory")
    args = parser.parse_args()

    pregrade_dir = Path(args.pregrade_dir)
    outputs_dir = pregrade_dir / "outputs"

    if not outputs_dir.exists():
        print(f"Error: {outputs_dir} not found", file=sys.stderr)
        sys.exit(1)

    # Group output files by question slug (filename prefix before _batch)
    by_question: dict[str, list[Path]] = defaultdict(list)
    for f in outputs_dir.glob("*_batch*.json"):
        slug = f.stem.rsplit("_batch", 1)[0]
        by_question[slug].append(f)

    if not by_question:
        print("No output files found in", outputs_dir, file=sys.stderr)
        sys.exit(1)

    for slug, files in sorted(by_question.items()):
        all_students = []
        question_meta = {}

        for f in sorted(files):
            data = json.loads(f.read_text())
            if not question_meta:
                question_meta = data.get("question", {})
            all_students.extend(data.get("students", []))

        # Sort alphabetically by first name, then last name
        all_students.sort(key=lambda s: (s["firstname"].lower(), s["lastname"].lower()))

        q_name = question_meta.get("name", slug)
        q_desc = question_meta.get("description") or ""
        header = f"# Pre-Grading: {q_name}"
        if q_desc:
            header += f" — {q_desc}"

        lines = [header, ""]
        for student in all_students:
            name = f"{student['lastname']}, {student['firstname']}"
            lines.append(f"## {name}")
            lines.append("")
            lines.append(student.get("feedback", "_No feedback generated._"))
            lines.append("")
            lines.append("---")
            lines.append("")

        out_file = pregrade_dir / f"{slug}.md"
        out_file.write_text("\n".join(lines))
        print(f"  {out_file.name}  ({len(all_students)} students)")

    print(f"\nAssembled {len(by_question)} question file(s) in {pregrade_dir}/")


if __name__ == "__main__":
    main()
