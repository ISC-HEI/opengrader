#!/usr/bin/env python3
"""
LLM Stats Script - Compare grading results across multiple LLMs

Usage: python llm_stats.py file1.json file2.json ... [--out-dir out]
"""

import argparse
import json
import re
from pathlib import Path
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np


def extract_llm_name(filepath: str) -> str:
    """Extract LLM name from filename like gemini_v2.json -> gemini_v2"""
    match = re.search(r"(.+_v\d+)", Path(filepath).stem)
    if match:
        return match.group(1)
    return Path(filepath).stem


def load_assessment_data(filepath: str) -> dict:
    """Load and parse a JSON assessment file."""
    with open(filepath, "r") as f:
        data = json.load(f)

    llm_name = extract_llm_name(filepath)

    assessments = {}
    for question_id, question_data in data.get("questions", {}).items():
        for detail in question_data.get("all_details", []):
            key = (detail["student"], detail["rubric"], question_id)
            is_correct = detail["generated"] == detail["gradescope"]
            assessments[key] = {
                "correct": is_correct,
                "generated": detail["generated"],
                "gradescope": detail["gradescope"],
                "confidence": detail.get("confidence"),
            }

    summary = data.get("summary", {})

    return {
        "name": llm_name,
        "assessments": assessments,
        "summary": summary,
        "questions": list(data.get("questions", {}).keys()),
    }


def compute_precision_stats(llm_data: dict) -> dict:
    """Compute precision stats per LLM."""
    all_assessments = llm_data["assessments"]
    correct = sum(1 for a in all_assessments.values() if a["correct"])
    total = len(all_assessments)

    return {
        "correct": correct,
        "total": total,
        "precision": correct / total if total > 0 else 0,
    }


def compute_per_question_precision(llm_data: dict) -> dict:
    """Compute precision per question."""
    by_question = defaultdict(lambda: {"correct": 0, "total": 0})

    for (student, rubric, question_id), assessment in llm_data["assessments"].items():
        by_question[question_id]["total"] += 1
        if assessment["correct"]:
            by_question[question_id]["correct"] += 1

    result = {}
    for qid, stats in by_question.items():
        result[qid] = {
            "correct": stats["correct"],
            "total": stats["total"],
            "precision": stats["correct"] / stats["total"] if stats["total"] > 0 else 0,
        }

    return result


def get_error_keys(llm_data: dict) -> set:
    """Get set of (student, rubric, question) keys where LLM made an error."""
    return {
        key
        for key, assessment in llm_data["assessments"].items()
        if not assessment["correct"]
    }


def compute_error_overlap(llms_data: list) -> tuple:
    """Compute pairwise error overlap based on min errors between LLMs."""
    n = len(llms_data)
    error_sets = [get_error_keys(llm) for llm in llms_data]
    llm_names = [llm["name"] for llm in llms_data]

    jaccard_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i == j:
                jaccard_matrix[i, j] = 1.0
            else:
                intersection = len(error_sets[i] & error_sets[j])
                min_errors = min(len(error_sets[i]), len(error_sets[j]))
                jaccard_matrix[i, j] = (
                    intersection / min_errors if min_errors > 0 else 0
                )

    return llm_names, jaccard_matrix


def compute_per_question_error_overlap(llms_data: list) -> dict:
    """Compute pairwise error overlap per question."""
    all_questions = set()
    for llm in llms_data:
        all_questions.update(llm["questions"])
    all_questions = sorted(all_questions)

    n = len(llms_data)
    llm_names = [llm["name"] for llm in llms_data]

    result = {}
    for q in all_questions:
        error_sets = []
        for llm in llms_data:
            errors = {
                (student, rubric)
                for (student, rubric, qid), assessment in llm["assessments"].items()
                if qid == q and not assessment["correct"]
            }
            error_sets.append(errors)

        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                intersection = len(error_sets[i] & error_sets[j])
                min_errors = min(len(error_sets[i]), len(error_sets[j]))
                jaccard = intersection / min_errors if min_errors > 0 else 0
                pairs.append(
                    {
                        "llm1": llm_names[i],
                        "llm2": llm_names[j],
                        "jaccard": jaccard,
                    }
                )

        result[q] = pairs

    return result


def compute_all_agreement_errors(llms_data: list) -> dict:
    """Find assessments where ALL LLMs made the same error."""
    n = len(llms_data)
    error_sets = [get_error_keys(llm) for llm in llms_data]

    if n < 2:
        return {"count": 0, "keys": []}

    common_errors = error_sets[0]
    for es in error_sets[1:]:
        common_errors = common_errors & es

    return {
        "count": len(common_errors),
        "keys": list(common_errors),
    }


def plot_global_precision(llms_data: list, out_dir: Path):
    """Plot global precision comparison bar chart."""
    names = [llm["name"] for llm in llms_data]
    precisions = [compute_precision_stats(llm)["precision"] * 100 for llm in llms_data]

    fig, ax = plt.subplots(figsize=(max(6, len(names) * 1.5), 6))
    x = np.arange(len(names))
    width = 0.6

    colors = plt.cm.Set2(np.linspace(0, 1, len(names)))
    bars = ax.bar(x, precisions, width, color=colors, edgecolor="black", linewidth=1.5)

    ax.set_ylabel("Precision (%)", fontsize=12)
    ax.set_xlabel("LLM", fontsize=12)
    ax.set_title("Global Precision Comparison", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 105)
    ax.set_xticks(x)
    ax.set_xticklabels([n.replace("_", " ") for n in names], fontsize=11)
    ax.yaxis.grid(True, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)

    for bar, prec in zip(bars, precisions):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.5,
            f"{prec:.1f}%",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig(out_dir / "global_precision.png", dpi=150)
    plt.close()
    print(f"  Saved: {out_dir / 'global_precision.png'}")


def plot_per_question_precision(llms_data: list, out_dir: Path):
    """Plot per-question precision grouped bar chart."""
    all_questions = set()
    for llm in llms_data:
        all_questions.update(llm["questions"])
    all_questions = sorted(all_questions)

    llm_names = [llm["name"] for llm in llms_data]
    x = np.arange(len(all_questions))
    width = 0.8 / len(llms_data)

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = plt.cm.Set2(np.linspace(0, 1, len(llms_data)))

    for i, llm in enumerate(llms_data):
        precisions = []
        for q in all_questions:
            q_data = compute_per_question_precision(llm)
            precisions.append(q_data.get(q, {}).get("precision", 0) * 100)

        offset = (i - len(llms_data) / 2 + 0.5) * width
        bars = ax.bar(
            x + offset,
            precisions,
            width,
            label=llm_names[i],
            color=colors[i],
            edgecolor="black",
        )

    ax.set_ylabel("Precision (%)")
    ax.set_xlabel("Question")
    ax.set_title("Per-Question Precision Comparison")
    ax.set_xticks(x)
    ax.set_xticklabels([q.replace("_", " ") for q in all_questions])
    ax.legend()
    ax.set_ylim(0, 105)

    plt.tight_layout()
    plt.savefig(out_dir / "per_question_precision.png", dpi=150)
    plt.close()
    print(f"  Saved: {out_dir / 'per_question_precision.png'}")


def plot_error_overlap_matrix(llm_names: list, matrix: np.ndarray, out_dir: Path):
    """Plot pairwise error overlap heatmap."""
    fig, ax = plt.subplots(figsize=(8, 6))

    im = ax.imshow(matrix, cmap="YlOrRd", vmin=0, vmax=1)

    ax.set_xticks(np.arange(len(llm_names)))
    ax.set_yticks(np.arange(len(llm_names)))
    ax.set_xticklabels(
        [n.replace("_", " ") for n in llm_names], rotation=45, ha="right"
    )
    ax.set_yticklabels([n.replace("_", " ") for n in llm_names])

    for i in range(len(llm_names)):
        for j in range(len(llm_names)):
            text = ax.text(
                j,
                i,
                f"{matrix[i, j]:.2f}",
                ha="center",
                va="center",
                color="black",
                fontsize=10,
            )

    ax.set_title(
        "Pairwise Error Overlap (intersection / min(errors_llm1, errors_llm2))"
    )
    plt.colorbar(im, ax=ax, label="Overlap Index")

    plt.tight_layout()
    plt.savefig(out_dir / "error_overlap_matrix.png", dpi=150)
    plt.close()
    print(f"  Saved: {out_dir / 'error_overlap_matrix.png'}")


def plot_per_question_error_overlap(per_question_overlap: dict, out_dir: Path):
    """Plot per-question pairwise error overlap as grouped bar chart."""
    questions = list(per_question_overlap.keys())
    all_pairs = per_question_overlap[questions[0]]
    pair_names = [
        f"{p['llm1'].replace('_', ' ')} / {p['llm2'].replace('_', ' ')}"
        for p in all_pairs
    ]

    x = np.arange(len(questions))
    width = 0.8 / len(pair_names)

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.Set2(np.linspace(0, 1, len(pair_names)))

    for i, pair_name in enumerate(pair_names):
        values = [per_question_overlap[q][i]["jaccard"] for q in questions]
        offset = (i - len(pair_names) / 2 + 0.5) * width
        bars = ax.bar(
            x + offset,
            values,
            width,
            label=pair_name,
            color=colors[i],
            edgecolor="black",
        )

    ax.set_ylabel("Overlap Similarity")
    ax.set_xlabel("Question")
    ax.set_title(
        "Per-Question Error Overlap (intersection / min(errors_llm1, errors_llm2))"
    )
    ax.set_xticks(x)
    ax.set_xticklabels([q.replace("_", " ") for q in questions])
    ax.legend()
    ax.set_ylim(0, 1.1)

    plt.tight_layout()
    plt.savefig(out_dir / "per_question_error_overlap.png", dpi=150)
    plt.close()
    print(f"  Saved: {out_dir / 'per_question_error_overlap.png'}")


def plot_per_question_error_overlap_heatmap(per_question_overlap: dict, out_dir: Path):
    """Plot per-question pairwise error overlap as heatmap."""
    questions = list(per_question_overlap.keys())
    all_pairs = per_question_overlap[questions[0]]
    pair_names = [
        f"{p['llm1'].replace('_', ' ')} / {p['llm2'].replace('_', ' ')}"
        for p in all_pairs
    ]

    matrix = np.array(
        [
            [per_question_overlap[q][i]["jaccard"] for i in range(len(all_pairs))]
            for q in questions
        ]
    )

    fig, ax = plt.subplots(
        figsize=(max(6, len(pair_names) * 2), max(4, len(questions) * 0.5))
    )

    im = ax.imshow(matrix, cmap="YlOrRd", vmin=0, vmax=1, aspect="auto")

    ax.set_xticks(np.arange(len(pair_names)))
    ax.set_yticks(np.arange(len(questions)))
    ax.set_xticklabels(pair_names, rotation=45, ha="right")
    ax.set_yticklabels([q.replace("_", " ") for q in questions])

    for i in range(len(questions)):
        for j in range(len(pair_names)):
            ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", fontsize=9)

    ax.set_title(
        "Per-Question Error Overlap (intersection / min(errors_llm1, errors_llm2))"
    )
    plt.colorbar(im, ax=ax, label="Overlap Index")

    plt.tight_layout()
    plt.savefig(out_dir / "per_question_error_overlap_heatmap.png", dpi=150)
    plt.close()
    print(f"  Saved: {out_dir / 'per_question_error_overlap_heatmap.png'}")


def main():
    parser = argparse.ArgumentParser(description="Compare LLM grading results")
    parser.add_argument("files", nargs="+", help="Input JSON files")
    parser.add_argument("--out-dir", default="out", help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {len(args.files)} files...")
    llms_data = []
    for filepath in args.files:
        data = load_assessment_data(filepath)
        llms_data.append(data)
        print(f"  - {data['name']}: {len(data['assessments'])} assessments")

    print("\n=== Global Precision ===")
    for llm in llms_data:
        stats = compute_precision_stats(llm)
        print(
            f"  {llm['name']}: {stats['precision'] * 100:.2f}% ({stats['correct']}/{stats['total']})"
        )

    print("\n=== Per-Question Precision ===")
    all_questions = set()
    for llm in llms_data:
        all_questions.update(llm["questions"])
    all_questions = sorted(all_questions)

    for q in all_questions:
        print(f"  Question {q}:")
        for llm in llms_data:
            q_data = compute_per_question_precision(llm)
            stats = q_data.get(q, {})
            prec = stats.get("precision", 0) * 100
            print(f"    {llm['name']}: {prec:.2f}%")

    print("\n=== Pairwise Error Overlap (Overlap) ===")
    llm_names, jaccard_matrix = compute_error_overlap(llms_data)
    print(f"  {'LLM':<20}", end="")
    for name in llm_names:
        print(f" {name[:10]:>10}", end="")
    print()
    for i, name in enumerate(llm_names):
        print(f"  {name:<20}", end="")
        for j in range(len(llm_names)):
            print(f" {jaccard_matrix[i, j]:>10.2f}", end="")
        print()

    print("\n=== All-Agreement Errors ===")
    all_agree = compute_all_agreement_errors(llms_data)
    print(f"  Assessments where ALL LLMs made the same error: {all_agree['count']}")

    print("\n=== Per-Question Error Overlap (Overlap) ===")
    per_q_overlap = compute_per_question_error_overlap(llms_data)
    for q in per_q_overlap:
        print(f"  {q}:")
        for p in per_q_overlap[q]:
            print(f"    {p['llm1']} / {p['llm2']}: {p['jaccard']:.2f}")

    print("\n=== Generating Charts ===")
    plot_global_precision(llms_data, out_dir)
    plot_per_question_precision(llms_data, out_dir)
    plot_error_overlap_matrix(llm_names, jaccard_matrix, out_dir)
    plot_per_question_error_overlap(per_q_overlap, out_dir)
    plot_per_question_error_overlap_heatmap(per_q_overlap, out_dir)

    print(f"\nDone! Output saved to {out_dir}/")


if __name__ == "__main__":
    main()
