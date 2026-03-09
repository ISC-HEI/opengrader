# TODO
- Move resources inside skills directly
  - Done for single use resources -> for multi use resource -> parent skill ?
- Check if open code has a timeout for tool call -> if so, how much ? How to remove
  - [Here](https://opencode.ai/docs/config/#models)
- Try to have different models for orchestrator and sub-agents (for OCR for example)
  - [here](https://opencode.ai/docs/agents/) might have the solution
  - We might be able to create an agent to read pdfs for example, this could be cool !
- Cost estimation with/without OCR (check for input/output tokens etc..)
  - If agent is possible, cost should depend on the main model, we should try a free one, and check if it is enough or not
