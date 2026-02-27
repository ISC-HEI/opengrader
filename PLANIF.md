# Planification

## TODO
- (1/4 - 1/2 day) - Parse unit tests 
- (1-3 day) - Find a way to run unit tests on students submissions -> Allows for pre-grade and Gradescope PDF generation. ==> Look with Louis to see what has been done for python
- (2-4 day) - Parse PDF files to allow for students answer extraction
- (1/2 day) - Parse solution from files (.py files, .txt files etc)
- (3-5 day) - Generate PDF files from YAML to allow for gradescope grading

### Unsure
- (1/2 - 1 day) - Find a way to parse any files for "unit tests" results. For unit tests not ran locally (like SQL request on moodle etc...)
- (1 - 2 day) - Generate pre-grading report from rubric for each student submission

### Delay
Minimum : 7.5 days ==> 3 weeks at 50%
Maximum: 11.5 days ==> 4-5 weeks at 50%


### Questions
What do we want for full paper exams ? Only generate pre-grading from rubric, student answers and solutions ?
Do we want a way to help the user to generate a rubric for the correction ? If so, do we want to integrate the rubric to the YAML file directly ? Do we want to check if we can export to Gradescope directly ?

If we want to import rubric from else where -> what format ?

For the github issue -> Is there a way to do this directly from opencode ?

## [DONE] Week one (23.02 - 27.02) 
Parsed files from moodle :
- Parsed exam questions number (Q1, Q2 etc...) and max points (no description)
- Parsed students answers (content, and graded points)

Parsed .md exam files (from ISC templates)
- Parsed questions description
- Parsed questions points (if any)

Parsed students submissions from HybridProctor
- Parsed students answers per questions
- Parsed students first/last name

## Week two (2.03 - 06.03)

Generate PDF files from YAML to allow for gradescope grading :
- Find a way to generate a .md file for each student submission
- Generate the PDF from the .md file
- Find a way to support programming language for .md code block (python, scala, SQL etc...)
- Generate the correct number of page for every student to fit each submission

## Week three (9.03 - 13.03)

Parse unit tests :
- SKILL to parse the unit tests for an exam and add them to the YAML

Find a way to run unit tests on students submissions :
- Start with easier language (probably `python`)
- Find a way to automate test running for each student submission. 
- Find a good way to manage automatic point attribution for unit tests results ? (Or do we leave that for the professor ?)
- Save unit tests results in the YAML file directly
- Add unit tests to the PDF generation for gradescope

Maybe add another language (probably `scala`) ?

## Week four (16.03 - 20.03)

Parse solution from files (.py files, .txt files etc): 
- Parse the exam solution from separate file (either .txt or .py)

Import rubric to YAML file:
- Create SKILL to import rubric

Generate pre-grading report:
- Generate pre-grading report per question with the rubric and the student submission

## Week five ? (23.03 - 27.03)

Normally everything is done :)

I think we might want to keep this empty, as we will probably encounter problems
