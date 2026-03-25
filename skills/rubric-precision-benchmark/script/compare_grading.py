import argparse
import csv
import sys
from pathlib import Path

from ruamel.yaml import YAML


def load_csv(filepath: str) -> tuple[list[str], list[dict]]:
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def normalize_name(name: str) -> str:
    return name.strip().lower() if name else ""


def compare_question(generated_csv: str, gradescope_csv: str) -> dict:
    gen_headers, gen_rows = load_csv(generated_csv)
    gs_headers, gs_rows = load_csv(gradescope_csv)

    gen_headers = [h.strip() for h in gen_headers]
    rubric_columns = [h for h in gen_headers if h not in ["First Name", "Last Name"]]

    gs_rubric_map = {}
    for row in gs_rows:
        if row.get("First Name") and row.get("Last Name"):
            key = (normalize_name(row["First Name"]), normalize_name(row["Last Name"]))
            gs_rubric_map[key] = {
                col: row.get(col, "").strip().lower() for col in rubric_columns
            }

    results = {
        "total": 0,
        "matches": 0,
        "mismatches": 0,
        "missing_in_generated": [],
        "missing_in_gradescope": [],
        "rubric_mismatches": [],
    }

    for gen_row in gen_rows:
        first_name = normalize_name(gen_row.get("First Name", ""))
        last_name = normalize_name(gen_row.get("Last Name", ""))
        key = (first_name, last_name)

        results["total"] += 1

        if key not in gs_rubric_map:
            results["missing_in_gradescope"].append(
                f"{gen_row.get('First Name')} {gen_row.get('Last Name')}"
            )
            continue

        gs_row = gs_rubric_map[key]

        for rubric in rubric_columns:
            gen_value = gen_row.get(rubric, "").strip().lower()
            gs_value = gs_row.get(rubric, "").strip().lower()

            if gen_value != gs_value:
                results["mismatches"] += 1
                results["rubric_mismatches"].append(
                    {
                        "student": f"{gen_row.get('First Name')} {gen_row.get('Last Name')}",
                        "rubric": rubric,
                        "generated": gen_value,
                        "gradescope": gs_value,
                    }
                )

    unmatched = set(gs_rubric_map.keys()) - {
        (
            normalize_name(r.get("First Name", "")),
            normalize_name(r.get("Last Name", "")),
        )
        for r in gen_rows
    }
    for fn, ln in unmatched:
        results["missing_in_generated"].append(f"{fn} {ln}")

    results["matches"] = results["total"] - results["mismatches"]

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Compare generated CSV grading against GradeScope exports"
    )
    parser.add_argument(
        "generated_folder", help="Folder containing generated CSV files"
    )
    parser.add_argument(
        "gradescope_folder", help="Folder containing GradeScope exported CSV files"
    )
    args = parser.parse_args()

    gen_dir = Path(args.generated_folder)
    gs_dir = Path(args.gradescope_folder)

    if not gen_dir.is_dir():
        print(f"Error: Generated folder not found: {gen_dir}")
        sys.exit(1)
    if not gs_dir.is_dir():
        print(f"Error: GradeScope folder not found: {gs_dir}")
        sys.exit(1)

    gen_files = {f.stem.split("_")[0]: f for f in gen_dir.glob("*_generated.csv")}
    gs_files = {f.stem.split("_")[0]: f for f in gs_dir.glob("*.csv")}

    all_questions = sorted(
        set(gen_files.keys()) | set(gs_files.keys()), key=lambda x: int(x)
    )

    print("=" * 70)
    print("RUBRIC PRECISION BENCHMARK RESULTS")
    print("=" * 70)
    print()

    total_students = 0
    total_matches = 0
    total_mismatches = 0

    question_results = []

    for qid in all_questions:
        gen_file = gen_files.get(qid)
        gs_file = gs_files.get(qid)

        if not gen_file:
            print(f"Question {qid}: Missing generated file")
            continue
        if not gs_file:
            print(f"Question {qid}: Missing GradeScope file")
            continue

        result = compare_question(str(gen_file), str(gs_file))
        question_results.append((qid, result))

        precision = (
            (result["matches"] / result["total"] * 100) if result["total"] > 0 else 0
        )

        status = "✓" if result["mismatches"] == 0 else "✗"
        print(f"Question {qid} {status}")
        print(
            f"  Students: {result['total']}, Matches: {result['matches']}, Mismatches: {result['mismatches']}"
        )
        print(f"  Precision: {precision:.1f}%")

        if result["missing_in_generated"]:
            print(
                f"  Missing in generated: {', '.join(result['missing_in_generated'][:3])}"
            )
            if len(result["missing_in_generated"]) > 3:
                print(f"    ... and {len(result['missing_in_generated']) - 3} more")
        if result["missing_in_gradescope"]:
            print(
                f"  Missing in gradescope: {', '.join(result['missing_in_gradescope'][:3])}"
            )
            if len(result["missing_in_gradescope"]) > 3:
                print(f"    ... and {len(result['missing_in_gradescope']) - 3} more")

        total_students += result["total"]
        total_matches += result["matches"]
        total_mismatches += result["mismatches"]

        print()

    print("=" * 70)
    print("OVERALL SUMMARY")
    print("=" * 70)

    if total_students > 0:
        overall_precision = total_matches / total_students * 100
    else:
        overall_precision = 0

    print(f"Total questions compared: {len(question_results)}")
    print(f"Total student-rubric pairs: {total_students}")
    print(f"Total matches: {total_matches}")
    print(f"Total mismatches: {total_mismatches}")
    print(f"Overall Precision: {overall_precision:.2f}%")

    all_mismatches = []
    for qid, result in question_results:
        all_mismatches.extend([(qid, m) for m in result["rubric_mismatches"]])

    if all_mismatches:
        print()
        print("DETAILED MISMATCHES (first 20):")
        for qid, m in all_mismatches[:20]:
            print(f"  Q{qid} - {m['student']}: {m['rubric']}")
            print(f"    Generated: {m['generated']} | GradeScope: {m['gradescope']}")

    if total_mismatches > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
