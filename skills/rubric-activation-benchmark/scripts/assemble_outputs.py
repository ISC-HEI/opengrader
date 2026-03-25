# Merges per-batch JSON outputs from sub-agents into per-question JSON files.
# Output: benchmark/activations/Q1a.json, Q1b.json, ...

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Assemble sub-agent batch outputs into per-question JSON files."
    )
    parser.add_argument("benchmark_dir", help="Path to the benchmark/ directory")
    args = parser.parse_args()

    benchmark_dir = Path(args.benchmark_dir)
    outputs_dir = benchmark_dir / "outputs"
    activations_dir = benchmark_dir / "activations"
    activations_dir.mkdir(parents=True, exist_ok=True)

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
        rubrics = []

        for f in sorted(files):
            data = json.loads(f.read_text())
            if not question_meta:
                question_meta = data.get("question", {})
                rubrics = question_meta.get("rubrics", [])
            all_students.extend(data.get("students", []))

        # Sort alphabetically by last name, then first name
        all_students.sort(key=lambda s: (s["lastname"].lower(), s["firstname"].lower()))

        q_id = question_meta.get("id", 0)
        q_name = question_meta.get("name", slug)

        output_data = {
            "question_id": q_id,
            "question_name": q_name,
            "rubrics": rubrics,
            "students": all_students,
        }

        out_file = activations_dir / f"{slug}.json"
        out_file.write_text(json.dumps(output_data, indent=2, ensure_ascii=False))
        print(f"  {out_file.name}  ({len(all_students)} students)")

    print(f"\nAssembled {len(by_question)} question file(s) in {activations_dir}/")


if __name__ == "__main__":
    main()
