## Remarks 

-> Move scripts (everything) inside 

Does opencode have a timeout ? How does a long script handling is done ?


This week -> Try to do the pipeline on FNL exercise (treat scans)

How do we get questions from moodle -> Explore mbz -> check if we can extract everything from here

for OCR -> use less powerful model (Gemini 3.0 flash for steacher)

Opencode -> try to keep a big model as the orchestrator -> try to use a smaller one for the OCR

Cost estimation -> how much to do OCR for 20 students * 2 pages for students

check for total input token

Give estimation for model change

for precision -> check by hand on a small subset. Keep it as an end-to-end ()
no intermediate check


idea : Loop on small subset to adjust corrections parameters, then launch big correction on all students


Check help omn correction without rubric

On OCR -> force model to not correct the code that the student produced !!

Évaluation ? -> scans loop -> will make some sort of evaluation -> check with ground truth (Renaud CSV)

Idea : 
Find a way to download rubric from gradescope -> export evaluation ?

Download ground truth from gradescope (PimP semstriel 2025)
Extract rubric -> 


Correction with unit test :
moodle -> tronc commun informatique -> downloaded from moodle -> mbz with unit test, exam source, submissions, and points
Gradescope -> Rubric -> ground truth correction

Then, find a way to run the unit tests on python code -> take the results of the unit tests

To do pre-grading -> loop with LLM on unit tests results -> correct student code -> rerun unit test until success
-> When success -> tell LLM to ouput everything that needs to be changed for the student code to work

-> then build on this result to make the positive and negative with the rubric



skills.sh -> check that out



## TODO this week

Start on FNL quizz -> OCR on scans -> cost estimation -> Judge agent on correction vs CSV correction from Renaud

Add intermediate representation (maybe json)

After this -> Excel parsing from Data engeeniring

-> After this -> TC -> unit test pythons

Check providers from openrouter -> on switch, we lost cache :(
in opencode config -> fix provider
