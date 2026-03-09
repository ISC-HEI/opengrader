## Summary

### What's been done

Web Interface -> not done but found !

PDF generation from YAML exam file:
- Markdown generation for each student submission
- PDF generation from Markdown file
- Pages normalization from PDF files
- Template generation from PDF submissions


LLM traçability :
- Tested LLM broadcasting from OpenRouter to LangFuse

- Deployed LangFuse in local :
  - Deployed docker compose langfuse
  - Deployed LiteLLM proxy
  - Configured OpenCode to transmit requests trough proxy


Not done :
- Find a way to support more programming language for .md code block

- Analyze langfuse logging to debug thinking tokens ?
