---
name: scan-to-yaml
description: |
  Use this skill to extract student answers from scanned paper exam PDFs into a unified YAML file.
  Handles multi-student scans (each PDF contains N students × M pages per student), name matching
  against an Excel student list, and per-question answer extraction via Gemini vision.
---

# Scan-to-YAML Skill

## Overview

This skill converts scanned exam PDFs into the unified YAML schema used by all OpenGrader skills.
It proceeds in four steps: question catalog, layout mapping, student identification, answer extraction.

## Required Inputs (in exam folder)

1. **Template pdf file** — the pdf that was printed and handed out to the students.
2. **Scan files** — one or more scan files, each containing multiple students (excluded: files starting with `__`)
3. **Student list** — Excel file with columns for firstname, lastname, and optionally login/username.

## Step 0: Generate the question catalog

Check whether an `exam.yaml` already exists in the exam folder.
If not, run the `exam-markdown-to-yaml` skill to produce it.
The exam YAML must have all questions filled in (name, id, type, description, max_points).
`student_response` might be `null` at this stage.

---

## Step 1: Analyze exam layout

Map each question to the page(s) it occupies in the exam PDF.

```bash
uv run skills/scan-to-yaml/scripts/analyze_layout.py <exam.yaml> <exam.pdf>
# writes → <exam_folder>/scan_results/layout.json
```

Review the output. Verify that every question has at least one page assigned.
If a question is missing, re-run or manually edit `layout.json`.

---

## Step 2: Identify students in scan files

Read the handwritten name from the cover page of each student's exam block and match to the Excel list.

```bash
uv run skills/scan-to-yaml/scripts/map_students.py <exam_folder> <students.xlsx>
# writes → <exam_folder>/scan_results/students.json
```

Review the output carefully:
- Any entry with `"student_id": null` is **unmatched** — fix it manually in `students.json` before continuing.
- Confirm the matched names look correct (fuzzy matching can mis-match similar names).

Do **not** proceed to Step 3 until all students are matched and `start_page` values look correct.

---

## Step 3a: Extract answers (one JSON per student × question)

Run all student × question pairs in parallel:

```bash
uv run skills/scan-to-yaml/scripts/run_extractions.py <exam.yaml> <exam_folder>
# writes → <exam_folder>/scan_results/q{question_id}_{student_id}.json  (one per pair)
```

Pairs whose output JSON already exists are skipped — safe to re-run after partial failures.
Failed pairs are reported at the end; re-run the same command to retry only those.

After all extractions, review files marked `"uncertain": true` and correct their `content` manually if needed.

---

## Step 3b: Assemble final YAML

Merge all individual JSON files into the final exam YAML:

```bash
uv run skills/scan-to-yaml/scripts/assemble_yaml.py <exam.yaml> <exam_folder>/scan_results/
# writes → <exam_folder>/<exam_stem>_answers.yaml
```

The script will warn about any missing `q{id}_{login}.json` files.
Fix missing files before treating the output as complete.

---

## General Rules

- **Never skip student review (Step 2).** A wrong `start_page` silently extracts the wrong student's pages.
- **`uncertain: true` means human review required** before grading. Flag these to the user.
- If a question spans multiple pages, all pages are sent to Gemini in a single call.
- The final YAML has `points: null` and `correction_details: null` for all answers — ready for the `pregrade` skill.

## Next Step

Once the final YAML is produced, offer the user to run the **`pregrade` skill** to generate a pre-grading report.
The output of this skill is the direct input to `pregrade` — no conversion needed.
