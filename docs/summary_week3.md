## Summary

### What's been done

- Full export test - Saved result
- Research on OCR capable models (many choices)
  - Chatgpt5 nano -> really bad
  - Gemini flash (3.0/2.5) -> Better, but not good enough for now
- Created sub agent -> Allow for OCR capable model to be used only to read image
- Created main agent -> Allow for custom prompt

- Started testing on correcting the FNL quizz -> Pretty bad result for now.
  - Maybe it is because of the intermediate representation which is not precise enough
  - We need to got to LaTeX -> As Sebastien Borloz did -> riding his wave


### What is left to do :

- Find a way to restrain provider change on openrouter

- For the precision of correction :
  - Create benchmarks and use blind judge to estimate precision

- General tasks :
  - Finish documentation
  - Adjust the main agent prompt for better results

- Excel exam correction :
  - Test data parsing from .mbz
  - Test autonomous correction

- Parse scan from student :
  - Test with latex intermediate representation
  - Test with OCR capable main model
