# Logging Quick Reference

## Quick Start

```python
from grader_agent2 import OpenGraderAgent

# Logging is automatic
agent = OpenGraderAgent(working_dir="./my_exams")
agent.chat("Hello")  # Everything is logged
```

## Log File Location

```
logs/opengrader_YYYYMMDD_HHMMSS.log
```

## What's Logged

| Item | Console | File | Format |
|------|---------|------|--------|
| User messages | ✅ Full | ✅ Full | Plain text |
| Agent responses | ⚠️ Truncated (200 chars) | ✅ Full | Plain text |
| Tool calls | ✅ Name only | ✅ Name + args | JSON |
| Thought signatures | ⚠️ Preview (100 chars) | ✅ Full | Base64 string |
| Agent state | ❌ | ✅ Full | Structured |
| Errors | ✅ Message | ✅ Full stack trace | Python traceback |

## Log Levels

| Level | Console | File | Use Case |
|-------|---------|------|----------|
| DEBUG | ❌ | ✅ | Development, detailed debugging |
| INFO | ✅ | ✅ | Normal operation, key events |
| WARNING | ✅ | ✅ | Potential issues |
| ERROR | ✅ | ✅ | Errors and exceptions |

## Common Log Patterns

### Session Start
```
INFO - OpenGrader logging initialized. Log file: logs/opengrader_20260206_143022.log
INFO - Working directory: /path/to/exams
INFO - Starting new grading session (thread: demo)
```

### User Message
```
INFO - ================================================================================
INFO - User message (thread: demo): What files do I have?
INFO - ================================================================================
```

### Tool Call with Thought Signature
```
INFO - Tool call 0: inventory_skill
INFO - Thought signature (preview): CpcHAdHtim9+q4rstcbvQC0ic4x1/vqQlCJWgE...
DEBUG - Full thought signature: CpcHAdHtim9+q4rstcbvQC0ic4x1/vqQlCJWgE+UZ6dTLYGHMMBkF...
DEBUG - Tool arguments: {
  "working_dir": "/path/to/exams"
}
```

### Agent Response
```
INFO - Agent response: I found the following files in your working directory...
DEBUG - Full agent response: I found the following files in your working directory:\n\n1. questions.md\n2. answers/...
```

## Searching Logs

### Find all thought signatures
```bash
grep "Thought signature" logs/opengrader_*.log
```

### Find all tool calls
```bash
grep "Tool call" logs/opengrader_*.log
```

### Find errors
```bash
grep "ERROR" logs/opengrader_*.log
```

### View latest log
```bash
tail -f logs/opengrader_*.log | tail -1
```

## Customization

### Change Console Log Level
```python
import logging

logger = logging.getLogger("OpenGrader")
for handler in logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setLevel(logging.DEBUG)  # More verbose
        # or
        handler.setLevel(logging.WARNING)  # Less verbose
```

### Custom Log Directory
```python
agent = OpenGraderAgent(
    working_dir="./my_exams",
    log_dir="./my_custom_logs"
)
```

## Troubleshooting

| Problem | Check Log For | Solution |
|---------|---------------|----------|
| No thought signatures | "Thought signature" entries | Verify using Gemini 3 model |
| Missing tool calls | "Tool call" entries | Check skill configuration |
| Context lost | Thought signatures in each turn | Verify signatures preserved |
| Slow responses | Timestamps between messages | Check model latency |
| Errors | "ERROR" or "Exception" | Read full stack trace |

## Performance Impact

- **File I/O**: ~1-5ms per log entry
- **Memory**: Minimal (streaming to file)
- **Disk Space**: ~1-10 MB per session (varies with activity)

## Best Practices

1. ✅ Keep logs for at least 7 days
2. ✅ Review logs after any unexpected behavior
3. ✅ Use DEBUG level during development
4. ✅ Monitor thought signatures in multi-turn conversations
5. ✅ Archive logs before major changes
6. ❌ Don't commit logs to git (already in .gitignore)
7. ❌ Don't disable logging in production

## Example Session

```bash
$ python example_with_logging.py
================================================================================
OpenGrader Logging Demonstration
================================================================================

Working directory: /path/to/my_exams
Log files will be saved to: /path/to/logs

Note: Check the log files for detailed information including:
  - Thought signatures from Gemini 3 model
  - All tool calls and arguments
  - Model responses and reasoning
  - Agent state transitions
================================================================================

INFO - OpenGrader logging initialized. Log file: logs/opengrader_20260206_143022.log
INFO - Working directory: /path/to/my_exams

Starting session...

INFO - Starting new grading session (thread: demo_with_logging)
INFO - Tool call 0: inventory_skill
INFO - Thought signature (preview): CpcHAdHtim9+q4rstcbvQC0ic4x1...

OpenGrader: I found the following files...
```

## Related Docs

- [Full Logging Documentation](logging.md)
- [Thought Signatures Explanation](logging.md#what-are-thought-signatures)
- [LiteLLM Gemini 3 Docs](https://docs.litellm.ai/blog/gemini_3)
