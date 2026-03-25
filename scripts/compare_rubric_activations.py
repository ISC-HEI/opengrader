import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path


def normalize_name(name: str) -> str:
    return name.strip().lower() if name else ""


def load_gradescope_csv(filepath: Path) -> tuple[dict, list[str]]:
    rubric_descriptions = []
    student_data = {}

    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        rubric_columns = [
            h
            for h in headers
            if h
            not in [
                "Assignment Submission ID",
                "Question Submission ID",
                "First Name",
                "Last Name",
                "SID",
                "Email",
                "Score",
                "Submission Time",
                "Adjustment",
                "Comments",
                "Grader",
                "Tags",
            ]
        ]
        rubric_descriptions = rubric_columns

        for row in reader:
            if row.get("First Name") and row.get("Last Name"):
                key = (
                    normalize_name(row["First Name"]),
                    normalize_name(row["Last Name"]),
                )
                student_data[key] = {
                    "firstname": row["First Name"],
                    "lastname": row["Last Name"],
                    "rubric_activations": {
                        desc: row.get(desc, "").strip().lower() in ("true", "1", "yes")
                        for desc in rubric_columns
                    },
                }

    return student_data, rubric_descriptions


def load_generated_json(filepath: Path) -> tuple[dict, list[str]]:
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    question = data.get("question", {})
    rubrics = question.get("rubrics", [])
    rubric_descriptions = [r.get("description", "") for r in rubrics]

    student_data = {}
    for student in data.get("students", []):
        key = (
            normalize_name(student.get("firstname", "")),
            normalize_name(student.get("lastname", "")),
        )

        activations = {}
        for assessment in student.get("rubric_assessments", []):
            idx = assessment.get("rubric_index", 0)
            activations[idx] = {
                "active": assessment.get("active", False),
                "confidence": assessment.get("confidence", 0.0),
                "justification": assessment.get("justification", ""),
            }

        student_data[key] = {
            "firstname": student.get("firstname", ""),
            "lastname": student.get("lastname", ""),
            "rubric_activations": activations,
        }

    return student_data, rubric_descriptions


def compare_activations(
    gs_data: dict, gen_data: dict, rubric_descriptions: list[str]
) -> dict:
    results = {
        "total": 0,
        "correct": 0,
        "wrong": 0,
        "missing_in_generated": [],
        "missing_in_gradescope": [],
        "all_details": [],
        "mismatch_details": [],
    }

    correct_confidences = []
    wrong_confidences = []

    for key, gen_student in gen_data.items():
        if key not in gs_data:
            results["missing_in_gradescope"].append(
                f"{gen_student['firstname']} {gen_student['lastname']}"
            )
            continue

        gs_student = gs_data[key]
        gs_activations = gs_student["rubric_activations"]
        gen_activations = gen_student["rubric_activations"]

        for idx, desc in enumerate(rubric_descriptions):
            results["total"] += 1

            gs_active = (
                gs_activations.get(desc, False)
                if isinstance(gs_activations.get(desc), bool)
                else False
            )
            if isinstance(gs_activations.get(desc), str):
                gs_active = gs_activations.get(desc, "").lower() in ("true", "1", "yes")

            gen_assessment = gen_activations.get(idx, {})
            gen_active = gen_assessment.get("active", False)
            confidence = gen_assessment.get("confidence", 0.0)

            is_correct = gs_active == gen_active
            results["correct" if is_correct else "wrong"] += 1

            if is_correct:
                correct_confidences.append(confidence)
            else:
                wrong_confidences.append(confidence)

            results["all_details"].append(
                {
                    "student": f"{gen_student['firstname']} {gen_student['lastname']}",
                    "rubric": desc,
                    "generated": gen_active,
                    "gradescope": gs_active,
                    "confidence": confidence,
                    "justification": gen_assessment.get("justification", ""),
                }
            )

            if not is_correct:
                results["mismatch_details"].append(
                    {
                        "student": f"{gen_student['firstname']} {gen_student['lastname']}",
                        "rubric": desc,
                        "generated": gen_active,
                        "gradescope": gs_active,
                        "confidence": confidence,
                        "justification": gen_assessment.get("justification", ""),
                    }
                )

    unmatched = set(gs_data.keys()) - set(gen_data.keys())
    for fn, ln in unmatched:
        results["missing_in_generated"].append(f"{fn} {ln}")

    results["avg_confidence_correct"] = (
        sum(correct_confidences) / len(correct_confidences)
        if correct_confidences
        else 0.0
    )
    results["avg_confidence_wrong"] = (
        sum(wrong_confidences) / len(wrong_confidences) if wrong_confidences else 0.0
    )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Compare LLM-generated rubric assessments against GradeScope exports"
    )
    parser.add_argument(
        "generated_folder", help="Folder containing generated JSON files"
    )
    parser.add_argument(
        "gradescope_folder", help="Folder containing GradeScope exported CSV files"
    )
    parser.add_argument("-o", "--output", help="Output JSON file for detailed results")
    args = parser.parse_args()

    gen_dir = Path(args.generated_folder)
    gs_dir = Path(args.gradescope_folder)

    if not gen_dir.is_dir():
        print(f"Error: Generated folder not found: {gen_dir}")
        sys.exit(1)
    if not gs_dir.is_dir():
        print(f"Error: GradeScope folder not found: {gs_dir}")
        sys.exit(1)

    gen_files = {f.stem: f for f in gen_dir.glob("*.json")}
    gs_files = {f.stem: f for f in gs_dir.glob("*.csv")}

    all_questions = sorted(set(gen_files.keys()) | set(gs_files.keys()))

    print("=" * 70)
    print("RUBRIC ACTIVATION BENCHMARK RESULTS")
    print("=" * 70)
    print()

    all_results = {}
    total_correct = 0
    total_wrong = 0
    total_total = 0

    for qid in all_questions:
        gen_file = gen_files.get(qid)
        gs_file = gs_files.get(qid)

        if not gen_file:
            print(f"Question {qid}: Missing generated file")
            continue
        if not gs_file:
            print(f"Question {qid}: Missing GradeScope file")
            continue

        gs_data, gs_rubrics = load_gradescope_csv(gs_file)
        gen_data, gen_rubrics = load_generated_json(gen_file)

        rubric_descriptions = gs_rubrics if gs_rubrics else gen_rubrics

        result = compare_activations(gs_data, gen_data, rubric_descriptions)
        all_results[qid] = result

        precision = (
            (result["correct"] / result["total"] * 100) if result["total"] > 0 else 0
        )
        wrong_pct = (
            (result["wrong"] / result["total"] * 100) if result["total"] > 0 else 0
        )

        status = "✓" if result["wrong"] == 0 else "✗"
        print(f"Question {qid} {status}")
        print(f"  Students: {len(gen_data)}, Assessments: {result['total']}")
        print(f"  Correct: {result['correct']} ({precision:.1f}%)")
        print(f"  Wrong: {result['wrong']} ({wrong_pct:.1f}%)")
        print(f"  Avg confidence (correct): {result['avg_confidence_correct']:.2f}")
        print(f"  Avg confidence (wrong): {result['avg_confidence_wrong']:.2f}")

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

        total_correct += result["correct"]
        total_wrong += result["wrong"]
        total_total += result["total"]

        print()

    print("=" * 70)
    print("OVERALL SUMMARY")
    print("=" * 70)

    overall_precision = total_correct / total_total * 100 if total_total > 0 else 0
    overall_wrong_pct = total_wrong / total_total * 100 if total_total > 0 else 0

    print(f"Total questions compared: {len(all_results)}")
    print(f"Total rubric assessments: {total_total}")
    print(f"Correct predictions: {total_correct} ({overall_precision:.1f}%)")
    print(f"Wrong predictions: {total_wrong} ({overall_wrong_pct:.1f}%)")

    if total_total > 0:
        all_correct_conf = []
        all_wrong_conf = []
        for res in all_results.values():
            all_correct_conf.append(res["avg_confidence_correct"] * res["correct"])
            all_wrong_conf.append(res["avg_confidence_wrong"] * res["wrong"])

        total_correct_conf = sum(c for c in all_correct_conf if c > 0)
        total_wrong_conf = sum(c for c in all_wrong_conf if c > 0)

        print(
            f"Overall avg confidence (correct): {total_correct_conf / total_correct if total_correct > 0 else 0:.2f}"
        )
        print(
            f"Overall avg confidence (wrong): {total_wrong_conf / total_wrong if total_wrong > 0 else 0:.2f}"
        )

    if all_results and total_wrong > 0:
        print(f"\n{total_wrong} mismatch(es) - see detailed results in output JSON")

    if args.output:
        output_data = {
            "summary": {
                "total_questions": len(all_results),
                "total_assessments": total_total,
                "correct": total_correct,
                "wrong": total_wrong,
                "precision_percent": overall_precision,
            },
            "questions": {},
        }
        for qid, res in all_results.items():
            output_data["questions"][qid] = {
                "total": res["total"],
                "correct": res["correct"],
                "wrong": res["wrong"],
                "precision_percent": (res["correct"] / res["total"] * 100)
                if res["total"] > 0
                else 0,
                "avg_confidence_correct": res["avg_confidence_correct"],
                "avg_confidence_wrong": res["avg_confidence_wrong"],
                "all_details": res["all_details"],
                "mismatch_details": res["mismatch_details"],
            }

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\nDetailed results written to: {args.output}")

    sys.exit(0 if total_wrong == 0 else 1)


if __name__ == "__main__":
    main()
