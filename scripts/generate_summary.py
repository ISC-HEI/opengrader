#!/usr/bin/env python3
"""
Generate a corrector summary (Markdown + PDF) from test_results.json + exam YAML.

Usage:
    uv run python scripts/generate_summary.py \
        -i labo_test_poo_2026.yaml \
        -r test_results.json \
        -o summary
    → summary.md  and  summary.pdf
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

from ruamel.yaml import YAML


STATUS_EMOJI = {
    "compile_error": "⚠ compile",
    "timeout":       "⏱ timeout",
    "parse_error":   "?",
    "empty":         "–",
}


def fmt(result: dict | None) -> str:
    """Format a single test result for the Markdown table."""
    if result is None:
        return "–"
    err = result.get("error")
    if err:
        return STATUS_EMOJI.get(err, f"⚠ {err}")
    p, t = result.get("passed", 0), result.get("total", 0)
    if t == 0:
        return "–"
    return f"{p}/{t}"


def fmt_typst(result: dict | None) -> str:
    """Format a single test result for the Typst table (no emoji)."""
    if result is None:
        return "--"
    err = result.get("error")
    if err == "compile_error":
        return "compile err"
    if err == "timeout":
        return "timeout"
    if err in ("parse_error", "empty") or err:
        return "?"
    p, t = result.get("passed", 0), result.get("total", 0)
    if t == 0:
        return "--"
    return f"{p}/{t}"


def color_typst(result: dict | None) -> str:
    """Return a Typst color expression for the cell."""
    if result is None:
        return "gray"
    err = result.get("error")
    if err:
        return "red" if err in ("compile_error", "timeout") else "gray"
    p, t = result.get("passed", 0), result.get("total", 0)
    if t == 0:
        return "gray"
    if p == t:
        return "green"
    if p == 0:
        return "red"
    return "orange"


def generate(exam_path: str, results_path: str, out_stem: str):
    yaml = YAML()
    with open(exam_path) as f:
        data = yaml.load(f)
    with open(results_path) as f:
        import json
        results = json.load(f)

    exam_name = data["exam_name"].replace("--", "–")
    questions = data["questions"]
    q_names = [q["name"] for q in questions]
    q_ids   = [q["id"]   for q in questions]
    q_max   = [q.get("max_points", "?") for q in questions]

    students = []
    for s in data.get("student_response", []):
        key = f"{s['firstname']}_{s['lastname']}"
        name = f"{s['firstname']} {s['lastname']}"
        qs = results.get(key, {})
        students.append((name, key, qs))
    students.sort(key=lambda x: x[0].lower())

    # ── Markdown ──────────────────────────────────────────────────────────
    header_cols = ["Étudiant"] + [f"Q{i} ({n})<br>/{m}" for i, n, m in zip(q_ids, q_names, q_max)]
    sep = [":---"] + [":---:"] * len(questions)

    md_lines = [
        f"# Résultats des tests — {exam_name}\n",
        "| " + " | ".join(header_cols) + " |",
        "| " + " | ".join(sep) + " |",
    ]
    for name, key, qs in students:
        cells = [name] + [fmt(qs.get(str(qid))) for qid in q_ids]
        md_lines.append("| " + " | ".join(cells) + " |")

    md_path = out_stem + ".md"
    Path(md_path).write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"Written {md_path}")

    # ── Typst → PDF ───────────────────────────────────────────────────────
    def cell(text: str, color: str = "black", bold: bool = False) -> str:
        t = f'text(fill: {color})[{text}]'
        if bold:
            t = f"strong[{text}]"
        return f"  table.cell[#{t}],"

    col_widths = ["1fr"] + ["auto"] * len(questions)
    authors = data.get("authors", ["—"])
    authors_typst = ", ".join(f'"{a}"' for a in authors)

    typ_lines = [
        '#import "@preview/isc-hei-document:0.7.1": *',
        "",
        "#show: project.with(",
        "  doc-type: \"document\",",
        "  show-cover: false,",
        "  show-toc: false,",
        "  fancy-line: false,",
        f'  title: "{exam_name}",',
        '  subtitle: [Résultats des tests — correcteurs],',
        f'  authors: ({authors_typst},),',
        "  logo: none,",
        ")",
        "",
        f'#table(',
        f'  columns: ({", ".join(col_widths)}),',
        "  table.header(",
        f'    table.cell[*Étudiant*],',
    ]
    for qid, qname, qm in zip(q_ids, q_names, q_max):
        typ_lines.append(f'    table.cell(align: center)[*Q{qid} – {qname}*\\ /{qm}],')
    typ_lines.append("  ),")

    for name, key, qs in students:
        typ_lines.append(f'  [{name}],')
        for qid in q_ids:
            r = qs.get(str(qid))
            txt = fmt_typst(r)
            col = color_typst(r)
            typ_lines.append(f'  table.cell(align: center)[#text(fill: {col})[{txt}]],')

    typ_lines.append(")")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        typ_file = tmp / "summary.typ"
        typ_file.write_text("\n".join(typ_lines), encoding="utf-8")

        result = subprocess.run(
            ["typst", "compile", str(typ_file), str(tmp / "summary.pdf")],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"Typst error:\n{result.stderr}")
        else:
            pdf_path = out_stem + ".pdf"
            import shutil
            shutil.copy(tmp / "summary.pdf", pdf_path)
            print(f"Written {pdf_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input",   required=True, help="Exam YAML")
    parser.add_argument("-r", "--results", required=True, help="test_results.json")
    parser.add_argument("-o", "--output",  required=True,
                        help="Output stem (e.g. 'summary' → summary.md + summary.pdf)")
    args = parser.parse_args()
    generate(args.input, args.results, args.output)


if __name__ == "__main__":
    main()
