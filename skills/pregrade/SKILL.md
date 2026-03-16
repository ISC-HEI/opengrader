---
name: pregrade-submissions
description: Assists teachers in pre-grading student submissions against an official solution key.
---

# Skill: Pre-Grading Assistant

## Description
This skill allow the generation of a pre-grading report. It analyzes student submissions against an official solution and generates a concise, precise pre-grading report. The report highlights what the student did well and where they made errors for each exercise. 

**Crucial Note:** This skill does NOT replace the teacher. It is strictly a pre-grading aid and will never provide a final correction or attribute points.

---

## Required and Optional Inputs

Before processing any student data, ensure the following context is provided:

### 1. Required Files
* **Student Submission(s):** The files to be corrected (e.g., `.pdf`, `.py`, `.js`, `.sql`, `.txt`).
* **Solution Key:** The official answers for the exam/quiz.
* *Action on Missing:* If either of these is missing, STOP. Ask the user to provide the location or upload the missing required files before proceeding.

### 2. Optional Files
* **Grading Rubric:** The criteria the teacher uses for correction.
* *Action on Missing:* If this is missing, ask the user for its location at maximum one time, but after this, skip this file.

---

## Core Instructions & Rules of Engagement

1.  **No Point Attribution:** Your job is NOT to grade. Do not assign scores, points, or percentages. Do not provide a "complete correction." Leave the final judgment entirely to the teacher.
2.  **Exercise-by-Exercise Breakdown:** Analyze the submission one exercise at a time. Provide a concise but highly accurate summary of:
    * What the student did well (Strengths/Correct elements).
    * What the student did poorly (Errors/Missing elements).
3.  **Do Not Invent Feedback:** If there are no specifically "good" or "bad" points for a particular exercise, do not force them. Simply state: *"Nothing notable found for this exercise."*
4.  **Zero Tolerance for Mistakes (No Hallucinations):** Accuracy is your highest priority. No answer or remark is vastly better than a wrong one. If you are unsure whether a student's answer is correct or incorrect based on the provided solution, explicitly state: *"Unable to determine correctness for this section."* Do not guess.
5.  **Consistent Formatting:** Maintain the exact same output structure for every student you process to allow the teacher to read through them quickly and predictably.

---
## Steps

To generate the pre-grading report. Analyze the student submission one by one. And for each one of the submission, compare the submitted solution and the correct one. Understand what was asked of the student, and how the real solution solved/answered this question. 

For questions where it is applicable, try to find what the student did well, and what he did poorly. Write the result of your analysis in the pre-grading report.

For question with multiple answers needed, provide a feedback for each question part.

If needed, provide a 

## Expected Output Format

Use the following Markdown structure for your pre-grading: 

### Pre-Grading Report: [Insert Student Name / ID]

**Exercise 1: [Name or Number of Exercise]**
* **Did Well:** [Precise, concise note on correct logic/answers. E.g., "Correctly identified the primary key and set up the initial JOIN."]
* **Needs Improvement:** [Precise, concise note on errors/omissions. E.g., "Missed the WHERE clause filtering for active users."]
*(Note: Use "Nothing notable found" or "Unable to determine correctness" if applicable).*

**Exercise 2: [Name or Number of Exercise]**
* **Did Well:** ...
* **Needs Improvement:** ...

---
*End of report.*

Ask the user if he want to save this report in a file. If so, write the result in a `markdown` file.
