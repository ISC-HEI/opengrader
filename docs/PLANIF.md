# Planification

## TODO
- (1/4 - 1/2 day) - Parse unit tests 
- (1-3 day) - Find a way to run unit tests on students submissions -> Allows for pre-grade and Gradescope PDF generation. ==> Look with Louis to see what has been done for python. We need to sandbox this
- (2-4 day) - Parse PDF files to allow for students answer extraction
- (1/2 day) - Parse solution from files (.py files, .txt files etc)
- (3-5 day) - Generate PDF files from YAML to allow for gradescope grading
- (1-3 day) - Research on privacy implication - We may find a solution to anonimize the data
- (1-3 day) - Create a SKILL to help professors create rubrics for corrections ? We may need to adapt those on the fly (Can talk with TC professors to gain experience on how to create them)
- (1/4 - 1/2 day) - Create a small user-friendly interface (Maybe the one from opencode is sufficient)
- (1/4 - 1/2 day) - Create a documentation to explain the usage of this tool
- (1/2 - 1 day) - Research on API cost. Make a full example to have some data on cost per usage
- (2-4 day) - Make some "unit tests" for skills -> Check as Antropic already has done something similar.

### Unsure
- (1/2 - 1 day) - Find a way to parse any files for "unit tests" results. For unit tests not ran locally (like SQL request on moodle etc...)
- (1 - 2 day) - Generate pre-grading report from rubric for each student submission

- Find a good way to manage automatic point attribution for unit tests results ? (Or do we leave that for the professor ?) -> for now we leave it to the prof


### Delay
Minimum : 7.5 days ==> 3 weeks at 50%
Maximum: 11.5 days ==> 4-5 weeks at 50%


### Questions
What do we want for full paper exams ? Only generate pre-grading from rubric, student answers and solutions ?
Do we want a way to help the user to generate a rubric for the correction ? If so, do we want to integrate the rubric to the YAML file directly ? Do we want to check if we can export to Gradescope directly ?

If we want to import rubric from else where -> what format ?

For the github issue -> Is there a way to do this directly from opencode ?

-> For now -> the PDF to upload to gradescope, only student answer 

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

## [DONE] Week two (2.03 - 06.03)

Generate PDF files from YAML to allow for gradescope grading :
- [DONE] Find a way to generate a .md file for each student submission
- [DONE] Generate the PDF from the .md file
- Find a way to support programming language for .md code block (python, scala, SQL etc...)
- [DONE] Generate the correct number of page for every student to fit each submission
- [DONE] Put them in gradescope -> and test if everything work or not

## Week three and four (9.03 - 20.03)

Fix provider jumping from openrouter -> avoid cache clearing during prompt (this cost more)

Parse scan from student answers :
- Research on what models can do OCR on pictures
- Find good intermediate representation to avoid doing OCR each time we want to loop on results
- Create skills to parse scanned document

Make cost estimation :
- Cost estimation for run without OCR (Either exported from moodle or, more likely, from hybrid proctor)
- Cost esimation for run with OCR -> probably extracted from FNL course

Estimate precision of correction by opengrader :
- Get CSV of ground truth from Renaud
- Create skill to correct exams
- Create blind judge agent to judge correction (between ground truth and LLM produced correction).

Real use case test on excel exam :
- Test data parsing from old exam
  - Test data parsing from .mbz (moodle compressed file)
  - Parse from csv/html otherwise
- Test autonomous correction
  - Test autonomous correction
  - Compare with ground truth from gradescope


## Week five ? (23.03 - 27.03)

Normally everything is done :)

I think we might want to keep this empty, as we will probably encounter problems
