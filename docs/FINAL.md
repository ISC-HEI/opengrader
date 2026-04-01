# OpenGrader - Project Summary

## What's Been Done

### Exam & Solution Parsing
- **Text files**: Parse solutions from `.py`, `.txt` and other text files
- **Markdown exams**: Parse exam files in Markdown format (ISC templates)
- **Text-based exams**: Parse from `.txt`, `.html`, `.doc`, `.rtf` formats

### Import from External Systems
- **Moodle HTML/CSV export**: Extract exam questions and student submissions
- **Moodle .mbz backup file**: Extract exam content and submissions from compressed Moodle backups
- **Hybrid Proctor**: Parse student submission files from Hybrid Proctor platform
- **Scanned exams** (partial): Extract answers from paper exam PDFs using OCR - *prototype exists but not production-ready*

### PDF Generation for GradeScope
- Generate blank exam PDFs from YAML exam files
- Generate student answer PDFs with normalized page counts
- Template generation for GradeScope import

#### Templates

Two templates are available for PDF generation:

**1. Markdown Template** (`models/template.jinja2`)
- Uses Jinja2 for templating + Pandoc (xelatex) for PDF generation
- Supports markdown syntax in question descriptions
- Scripts: `scripts/generate_pdfs.py`

**2. Typst Template** (`models/template.typst.jinja2`)
- Uses Jinja2 for templating + Typst for PDF generation
- Based on the ISC-HEI document template (`@preview/isc-hei-document:0.7.1`)
- Requires Typst fonts to be installed locally
- Scripts: `scripts/generate_pdfs_typst.py`

**Typst Template Features:**
- Uses `<Q0>`, `<Q1>`, etc. markers for page normalization
- Markdown to Typst conversion via `md2typst` library
- Code blocks converted to Typst's `#code()` syntax
- French language support by default

### Pre-Grading System
- Generate pre-grading reports analyzing student submissions against official solution keys
- Highlights strengths and errors without assigning points

### Research & Benchmarking
- **API cost research**: Analyzed costs with/without OCR capabilities
  - Without OCR: Can use free models
  - With OCR: ~$0.001 per document
- **Model benchmarking**: Tested multiple models (Qwen 9B, Qwen3.5 120B, Step 3.5 Fun, Gemini 3 Flash, Big Pickle)
- **Rubric activation benchmark**: Created skill to assess which rubric criteria were activated per student submission

### Observability
- OpenRouter broadcasting to LangFuse
- Local LiteLLM proxy deployment for full request logging

## What's Next

### Priority Items
1. **Add judge for benchmark comparison** - Implement a "natural language" comparison system to evaluate LLM grading precision against ground truth (teacher-created grades)

### Benchmark Testing
1. **Test with different models for pre-grading generation** - Evaluate how different LLMs handle the initial pre-grading step
2. **Test with different models for benchmark generation** - Compare rubric activation assessment across various models
3. **Test with no question text, only rubrics** - Assess if models can accurately grade using only the rubric criteria without the full question context
4. **Test with confidence scores** - Evaluate how models report their certainty in their assessments
5. **Test with different batch sizes** - Compare processing efficiency and accuracy at various batch sizes
6. **Compare errors between models** - Analyze if different models make similar or different mistakes

### Potential Improvements
- Improve scanned exam parsing (test with LaTeX intermediate representation)
- Restrict provider changes on OpenRouter to avoid cache clearing
- Expand programming language support for PDF code blocks
- Privacy research for data anonymization

### Future Features
- Unit test execution on student submissions (sandboxed)
- Automatic rubric generation assistance
- Full end-to-end autonomous correction testing
