#!/usr/bin/env python3
"""
Compile and run ScalaTest unit tests for each student submission.

Usage:
    uv run python scripts/run_tests.py -i labo_test_poo_2026.yaml -o test_results.json
    uv run python scripts/run_tests.py -i labo_test_poo_2026.yaml -o test_results.json -j 6

Output JSON format:
    {
      "Adrien_gaillard": {
        "0": {"passed": 5, "total": 10},
        "1": {"passed": 0, "total": 0, "error": "compile_error", "details": "..."}
      },
      ...
    }
"""
import argparse
import json
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ruamel.yaml import YAML

INTELLIJ = Path("/home/pmudry/git/CS101/exams/s2/exam-final/25_26/intellij")

QUESTION_MAP = {
    0: ("WordList",   "tests.solutions.WordListTest"),
    1: ("Paysan",     "tests.solutions.PaysanTest"),
    2: ("Sort",       "tests.solutions.SortTest"),
    3: ("Crosswords", "tests.solutions.CrosswordsTest"),
}


def lib_cp() -> str:
    return ":".join(str(j) for j in sorted((INTELLIJ / "lib").glob("*.jar")))


def fetch_scala_cp() -> str:
    r = subprocess.run(
        ["cs", "fetch", "--classpath", "org.scala-lang:scala-library:2.13.12"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"cs fetch failed: {r.stderr[:500]}")
    return r.stdout.strip()


def compile_common(full_cp: str) -> str:
    """Compile all solution + test files once into a shared output directory."""
    out = tempfile.mkdtemp(prefix="opengrader_common_")
    srcs = (
        list((INTELLIJ / "src/exercises/solutions").glob("*.scala"))
        + list((INTELLIJ / "src/tests/solutions").glob("*.scala"))
    )
    r = subprocess.run(
        ["cs", "launch", "scalac:2.13.12", "--",
         "-classpath", full_cp, "-d", out]
        + [str(s) for s in srcs],
        capture_output=True, text=True, cwd=str(INTELLIJ),
    )
    if r.returncode != 0:
        shutil.rmtree(out, ignore_errors=True)
        raise RuntimeError(f"Common compilation failed:\n{r.stderr[:1000]}")
    return out


def extract_implementation(code: str) -> str:
    """
    Keep only the first Scala file in the content block.
    Students for Q1 submitted both implementation + test class; we only want
    the implementation (everything up to the second 'package' declaration).
    """
    lines = code.split("\n")
    pkg_count = 0
    cut = len(lines)
    for i, line in enumerate(lines):
        if line.startswith("package "):
            pkg_count += 1
            if pkg_count == 2:
                cut = i
                break
    return "\n".join(lines[:cut])


def run_student_test(code: str, question_id: int, common_out: str, full_cp: str) -> dict:
    """
    Compile student code for one question and run the matching ScalaTest suite.
    The student's compiled class shadows the reference solution in the classpath.
    Returns a dict with keys: passed, total, and optionally error/details.
    """
    if question_id not in QUESTION_MAP:
        return {"passed": 0, "total": 0, "error": "unknown_question"}
    if not code or not code.strip():
        return {"passed": 0, "total": 0, "error": "empty"}

    exercise_name, test_class = QUESTION_MAP[question_id]

    # Strip any embedded test class (students sometimes submit impl + tests together)
    code = extract_implementation(code)

    # Rename student package exercises → exercises.solutions so tests can find it
    fixed = re.sub(
        r"^package\s+exercises\b",
        "package exercises.solutions",
        code, count=1, flags=re.MULTILINE,
    )

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        student_out = tmp / "out"
        student_out.mkdir()
        src = tmp / f"{exercise_name}.scala"
        src.write_text(fixed, encoding="utf-8")

        # Compile student file (common_out is on the classpath for cross-deps)
        cr = subprocess.run(
            ["cs", "launch", "scalac:2.13.12", "--",
             "-classpath", f"{common_out}:{full_cp}",
             "-d", str(student_out), str(src)],
            capture_output=True, text=True, cwd=str(INTELLIJ),
        )
        if cr.returncode != 0:
            return {"passed": 0, "total": 0, "error": "compile_error",
                    "details": cr.stderr[:600]}

        # Run ScalaTest: student_out first so student class shadows reference solution
        run_cp = f"{student_out}:{common_out}:{full_cp}"
        try:
            rr = subprocess.run(
                ["java", "-classpath", run_cp,
                 "org.scalatest.tools.Runner",
                 "-s", test_class, "-o"],
                capture_output=True, text=True,
                cwd=str(INTELLIJ), timeout=90,
            )
        except subprocess.TimeoutExpired:
            return {"passed": 0, "total": 0, "error": "timeout"}

        output = rr.stdout
        m = re.search(r"Tests: succeeded (\d+), failed (\d+)", output)
        if m:
            passed, failed = int(m.group(1)), int(m.group(2))
            return {"passed": passed, "total": passed + failed}

        return {"passed": 0, "total": 0, "error": "parse_error",
                "details": (output + rr.stderr)[:400]}


def main():
    parser = argparse.ArgumentParser(description="Run ScalaTest suites for all students")
    parser.add_argument("-i", "--input", required=True, help="Exam YAML file")
    parser.add_argument("-o", "--output", required=True, help="Output JSON file")
    parser.add_argument("-j", "--jobs", type=int, default=4,
                        help="Parallel compilation workers (default: 4)")
    args = parser.parse_args()

    yaml = YAML()
    with open(args.input) as f:
        data = yaml.load(f)

    print("Fetching Scala 2.13.12 library via coursier…")
    scala_cp = fetch_scala_cp()
    full_cp = f"{lib_cp()}:{scala_cp}"

    print("Compiling reference solutions + test suites…")
    common_out = compile_common(full_cp)
    print(f"  → {common_out}")

    try:
        # Build task list: (student_key, question_id, code)
        tasks = []
        student_keys = {}
        for student in data.get("student_response", []):
            key = f"{student['firstname']}_{student['lastname']}"
            student_keys[key] = True
            for ans in student.get("answers", []):
                tasks.append((key, ans["question_id"], ans.get("content") or ""))

        print(f"Running {len(tasks)} test jobs with {args.jobs} workers…\n")

        results: dict[str, dict[str, dict]] = {k: {} for k in student_keys}

        def run_task(t):
            name, qid, code = t
            res = run_student_test(code, qid, common_out, full_cp)
            status = (f"{res['passed']}/{res['total']}"
                      if "error" not in res
                      else res["error"])
            print(f"  {name:40s} Q{qid}: {status}")
            return name, qid, res

        with ThreadPoolExecutor(max_workers=args.jobs) as ex:
            futures = {ex.submit(run_task, t): t for t in tasks}
            for fut in as_completed(futures):
                try:
                    name, qid, res = fut.result()
                    results[name][str(qid)] = res
                except Exception as e:
                    print(f"  [ERROR] unexpected exception: {e}")

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\nResults written to {args.output}")

    finally:
        shutil.rmtree(common_out, ignore_errors=True)


if __name__ == "__main__":
    main()
