# Runs all student × question answer extractions in parallel.
# Reads students.json + layout.json to build the full task list, then calls extract_answer.py
# for each pair concurrently. Skips pairs whose output JSON already exists.

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

DEFAULT_WORKERS = 8


def run_one(cmd: list[str]) -> tuple[str, bool, str]:
    """Run a single extraction command. Returns (label, success, output)."""
    label = " ".join(cmd[-4:])  # last few args as a short label
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = (result.stdout + result.stderr).strip()
    return label, result.returncode == 0, output


def main():
    parser = argparse.ArgumentParser(
        description="Run all answer extractions in parallel."
    )
    parser.add_argument("exam_yaml", help="Path to exam.yaml")
    parser.add_argument("folder", help="Exam folder containing scan PDFs and scan_results/")
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Number of parallel workers (default: {DEFAULT_WORKERS})",
    )
    args = parser.parse_args()

    folder = Path(args.folder)
    scan_results = folder / "scan_results"

    with open(scan_results / "students.json") as f:
        students = [s for s in json.load(f) if s.get("student_id")]

    with open(scan_results / "layout.json") as f:
        layout = json.load(f)

    question_ids = list(layout["questions"].keys())

    tasks = [
        (s["student_id"], int(qid))
        for s in students
        for qid in question_ids
    ]

    pending = [
        (sid, qid)
        for sid, qid in tasks
        if not (scan_results / f"q{qid}_{sid}.json").exists()
    ]

    print(f"Total pairs: {len(tasks)}  |  Already done: {len(tasks) - len(pending)}  |  To run: {len(pending)}")
    if not pending:
        print("Nothing to do.")
        return

    base_cmd = [
        "uv", "run",
        "skills/scan-to-yaml/scripts/extract_answer.py",
        "--exam", args.exam_yaml,
        "--layout", str(scan_results / "layout.json"),
        "--students", str(scan_results / "students.json"),
        "--folder", str(folder),
    ]

    cmds = [
        base_cmd + ["--student-id", sid, "--question-id", str(qid)]
        for sid, qid in pending
    ]

    failed = []
    done = 0

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_one, cmd): cmd for cmd in cmds}
        for future in as_completed(futures):
            label, success, output = future.result()
            done += 1
            status = "OK" if success else "FAIL"
            print(f"  [{done}/{len(pending)}] {status}  {output}")
            if not success:
                failed.append(label)

    print(f"\nDone: {len(pending) - len(failed)} OK, {len(failed)} failed.")
    if failed:
        print("Failed tasks:")
        for f in failed:
            print(f"  {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
