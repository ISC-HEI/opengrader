# Rubric Creation Process

## Context
Creating a grading rubric for programming exam questions. Students are 1st year CS engineering learning imperative programming in Scala.

## Input Files
- `questions.yaml`: Contains exam questions with `given` (problem statement) and `solution` (reference solution)
- `answers.json`: Contains student answers extracted from PDFs

## Goal
Create a simple, binary rubric where each criterion is either achieved (1 point) or not (0 points).

## Process

### Step 1: Read the materials
Read both `questions.yaml` and `answers.json` to understand:
- What the questions ask for
- What the reference solution looks like
- What kind of answers students provided

### Step 2: Ask clarifying questions

Ask these questions (numbered, with lettered options):

**1. Point distribution:**
   - A. Total points per question?
   - B. Binary or partial credit?
   - C. If partial: percentage breakdown?

**2. Grading priorities for beginners:**
   - A. Credit for correct logic with syntax errors?
   - B. Credit for working but inefficient code?
   - C. Credit for incomplete but conceptually sound attempts?

**3. Edge case handling:**
   - A. Should edge cases (empty arrays, modulo, etc.) be required?
   - B. Should optional features be required or bonus?
   - C. Penalty for missing formatting requirements?

**4. Language-specific requirements:**
   - A. Strictness on syntax variations?
   - B. Strictness on mutability (var vs val)?
   - C. Credit for correct imperative approach even if not idiomatic?

**5. Common errors tolerance:**
   - A. Off-by-one errors: minor or major?
   - B. Missing return statements (if code works anyway)?
   - C. Incomplete solutions showing understanding?

**6. Structure:**
   - A. Preferred format (table, list, bullet points)?
   - B. Include concrete error examples?

**7-8. Question-specific criteria:**
For each question, ask what specific aspects should be graded and how many points each.

**9. Edge cases for deductions:**
   - A. Non-compiling code: 0 or partial credit?
   - B. Wrong logic but OK syntax: max points?
   - C. Almost correct with minor bugs: penalty?

### Step 3: Build the rubric

Based on answers, create a rubric with this structure:

```markdown
## Question X - [function name] (N points)

**Critères à vérifier (1 point chacun si achieved):**

1. **[Criterion 1]**: brief description
2. **[Criterion 2]**: brief description
3. **[Criterion 3]**: brief description
4. **[Criterion 4]**: brief description

**Note**: [Any optional features or clarifications]
```

### Key principles for rubric creation:
- Keep it simple: binary achieved/not achieved
- Focus on 4-6 main criteria per question
- Prioritize logic over syntax for beginners
- Be lenient on language-specific quirks
- Separate required features from bonus/optional ones
- Write in French (or requested language)

## Example Output

See `rubric.yaml` for the final format used in the grading system.

## Usage Prompt

When creating a new rubric, paste this to the LLM:

```
You will be given exam answers from students. This is a programming assessment for 1st year CS engineering students learning imperative programming in [LANGUAGE].

Questions are in @questions.yaml, student answers in @answers.json.

Help me build a rubric for the [N] questions.

Before you do that, ask me clarifying questions following this process:
1. Point distribution (total per question, binary vs partial credit)
2. Grading priorities for beginners (logic vs syntax, efficiency, partial credit)
3. Edge case handling requirements
4. Language-specific strictness
5. Common error tolerance
6. Rubric structure preferences
7-8. Question-specific criteria breakdown
9. Edge cases for deductions

Number your questions (1, 2, 3) and label answer options (a, b, c, ...). Keywords are fine.

After I answer, create a simple rubric with 4-6 binary criteria per question (achieved = 1 point, not achieved = 0 points).

All rubric in [LANGUAGE].
```
