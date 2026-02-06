# OpenGrader agent using LangGraph deep agents with skills for exam grading

import os
import logging
import json
from datetime import datetime
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_litellm import ChatLiteLLM
import sqlite3


class OpenGraderAgent:
    """
    Conversational grading assistant with agentic capabilities.
    Uses LangGraph deep agents with filesystem backend and SQLite checkpointing.
    """
    
    def __init__(
        self,
        working_dir: str,
        skills_dir: str = None,
        db_path: str = None,
        api_key: str = None,
        log_dir: str = None
    ):
        """
        Initialize the OpenGrader agent.
        
        Args:
            working_dir: Directory where exam files are located (teacher's workspace)
            skills_dir: Path to skills directory (defaults to src/skills relative to this file)
            db_path: Path to SQLite database (defaults to opengrader.db in project root)
            api_key: Gemini API key (uses GEMINI_API_KEY env var if not provided)
            log_dir: Directory for log files (defaults to logs/ in project root)
        """
        self.working_dir = Path(working_dir).resolve()
        
        # Set up logging directory
        if log_dir is None:
            project_root = Path(__file__).parent.parent
            self.log_dir = project_root / "logs"
        else:
            self.log_dir = Path(log_dir)
        
        self.log_dir.mkdir(exist_ok=True)
        
        # Set up logging
        self._setup_logging()
        
        # Set up skills directory
        if skills_dir is None:
            # Default: src/skills relative to this file
            project_root = Path(__file__).parent.parent
            self.skills_dir = project_root / "src" / "skills"
        else:
            self.skills_dir = Path(skills_dir).resolve()
        
        # Set up database path
        if db_path is None:
            # Default: opengrader.db in project root
            project_root = Path(__file__).parent.parent
            self.db_path = project_root / "opengrader.db"
        else:
            self.db_path = Path(db_path)
        
        # Get API key
        gemini_api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError(
                "Gemini API key required. Provide via api_key parameter or GOOGLE_API_KEY env var"
            )
        
        # Set API key for LiteLLM
        os.environ["GEMINI_API_KEY"] = gemini_api_key
        
        # Create Gemini model via LiteLLM
        self.model = ChatLiteLLM(
            model="gemini/gemini-3-flash-preview",
            temperature=0.7,
        )
        
        # Create SQLite checkpointer
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.checkpointer = SqliteSaver(conn)
        
        # Create the agent
        self.agent = create_deep_agent(
            backend=FilesystemBackend(root_dir=str(self.working_dir)),
            skills=[str(self.skills_dir) + "/"],
            checkpointer=self.checkpointer,
            interrupt_on={
                "write_file": True,   # Always confirm file writes
                "read_file": False,   # No interrupts for reads
                "edit_file": True,    # Confirm file edits
            },
            model=self.model,  # Pass ChatGoogleGenerativeAI instance
        )
        
        # System context for the agent
        self.system_context = self._build_system_context()
    
    def _setup_logging(self):
        """Set up comprehensive logging for agent activity."""
        # Create timestamp for log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"opengrader_{timestamp}.log"
        
        # Create logger
        self.logger = logging.getLogger("OpenGrader")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # File handler - verbose logging
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler - less verbose
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"OpenGrader logging initialized. Log file: {log_file}")
        self.logger.info(f"Working directory: {self.working_dir}")
    
    def _log_thought_signatures(self, response):
        """Extract and log thought signatures from model response."""
        try:
            # Check if response has choices and messages
            if hasattr(response, 'choices') and response.choices:
                for idx, choice in enumerate(response.choices):
                    message = choice.message if hasattr(choice, 'message') else choice
                    
                    # Log tool calls with thought signatures
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        self.logger.debug(f"Tool calls found in response (choice {idx})")
                        
                        for tool_idx, tool_call in enumerate(message.tool_calls):
                            self.logger.info(
                                f"Tool call {tool_idx}: {tool_call.function.name if hasattr(tool_call, 'function') else 'unknown'}"
                            )
                            
                            # Extract thought signature
                            if hasattr(tool_call, 'provider_specific_fields'):
                                fields = tool_call.provider_specific_fields
                                if isinstance(fields, dict) and 'thought_signature' in fields:
                                    thought_sig = fields['thought_signature']
                                    # Log truncated version (signatures are very long)
                                    sig_preview = thought_sig[:100] + "..." if len(thought_sig) > 100 else thought_sig
                                    self.logger.info(f"Thought signature (preview): {sig_preview}")
                                    self.logger.debug(f"Full thought signature: {thought_sig}")
                                elif hasattr(fields, 'get'):
                                    thought_sig = fields.get('thought_signature')
                                    if thought_sig:
                                        sig_preview = thought_sig[:100] + "..." if len(thought_sig) > 100 else thought_sig
                                        self.logger.info(f"Thought signature (preview): {sig_preview}")
                                        self.logger.debug(f"Full thought signature: {thought_sig}")
                            
                            # Log tool call arguments
                            if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'arguments'):
                                try:
                                    args = json.loads(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments
                                    self.logger.debug(f"Tool arguments: {json.dumps(args, indent=2)}")
                                except:
                                    self.logger.debug(f"Tool arguments (raw): {tool_call.function.arguments}")
                    
                    # Log message content
                    if hasattr(message, 'content') and message.content:
                        self.logger.info(f"Model response content: {message.content[:200]}{'...' if len(message.content) > 200 else ''}")
                        self.logger.debug(f"Full model response: {message.content}")
        
        except Exception as e:
            self.logger.error(f"Error extracting thought signatures: {e}", exc_info=True)
    
    def _log_agent_state(self, result):
        """Log detailed agent state and messages."""
        try:
            if result and isinstance(result, dict):
                # Log all messages in the result
                if "messages" in result:
                    self.logger.debug(f"Agent returned {len(result['messages'])} messages")
                    
                    for idx, msg in enumerate(result['messages']):
                        msg_type = type(msg).__name__
                        self.logger.debug(f"Message {idx} type: {msg_type}")
                        
                        # Log message content
                        if hasattr(msg, 'content'):
                            content = msg.content
                            if content:
                                self.logger.debug(f"Message {idx} content: {content[:200]}{'...' if len(str(content)) > 200 else ''}")
                        
                        # Log tool calls
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            self.logger.info(f"Message {idx} contains {len(msg.tool_calls)} tool calls")
                            for tc_idx, tc in enumerate(msg.tool_calls):
                                if hasattr(tc, 'function'):
                                    self.logger.info(f"  Tool {tc_idx}: {tc.function.name}")
                
                # Log any other relevant state
                for key in result.keys():
                    if key != "messages":
                        self.logger.debug(f"Result key '{key}': {type(result[key])}")
        
        except Exception as e:
            self.logger.error(f"Error logging agent state: {e}", exc_info=True)
    
    def _build_system_context(self) -> str:
        """Build system context with conventions and workflow."""
        return """You are OpenGrader, an AI assistant for grading exams.

## Your Role
You help teachers grade exams through a conversational, step-by-step process. 
You have access to skills that help with specific tasks like extracting questions, building rubrics, and grading answers.

## File Conventions
- All generated files go in an `opengrader/` subfolder within the working directory
- Use YAML format for structured data (questions, rubrics, grades)
- YAML is preferred because it's human-readable, supports multi-line content, and allows comments

## Workflow Stages
1. **Inventory**: Scan working directory to identify what files are available (questions, answers, rubrics)
2. **Extract**: Extract questions from source files (markdown, LaTeX, PDF)
3. **Rubric**: Create or import grading rubric
4. **Grade**: Grade student answers using the rubric

## Human-in-the-Loop Philosophy
- Always confirm before major operations (creating files, grading, etc.)
- Present options and let the teacher choose the next step
- Validate that all required files are present before proceeding
- Ask clarifying questions when needed

## Working Directory
The working directory is: {self.working_dir}
Generated files will be saved to: {self.working_dir}/opengrader/

## Getting Started
When starting a new grading session, use the inventory skill to:
1. Scan for available files
2. Validate that required files are present
3. Prompt the teacher for any missing files
4. Present workflow options (create rubric, grade with/without rubric, import rubric)
"""
    
    def chat(self, message: str, thread_id: str = "default") -> str:
        """
        Send a message to the agent and get a response.
        
        Args:
            message: User message
            thread_id: Conversation thread ID (for maintaining context across sessions)
            
        Returns:
            Agent's response
        """
        self.logger.info("="*80)
        self.logger.info(f"User message (thread: {thread_id}): {message}")
        self.logger.info("="*80)
        
        # Add system context to first message if needed
        full_message = f"{self.system_context}\n\nUser: {message}"
        
        self.logger.debug(f"Full message with context: {full_message[:300]}...")
        
        try:
            result = self.agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": full_message,
                        }
                    ]
                },
                config={"configurable": {"thread_id": thread_id}},
            )
            
            self.logger.debug("Agent invocation completed")
            
            # Log detailed agent state
            self._log_agent_state(result)
            
            # Extract the last message from the agent
            if result and "messages" in result:
                last_message = result["messages"][-1]
                
                # Log thought signatures if present
                self._log_thought_signatures(last_message)
                
                if hasattr(last_message, "content"):
                    response_content = last_message.content
                    self.logger.info(f"Agent response: {response_content[:200]}{'...' if len(str(response_content)) > 200 else ''}")
                    self.logger.debug(f"Full agent response: {response_content}")
                    return response_content
                
                response_str = str(last_message)
                self.logger.info(f"Agent response (str): {response_str[:200]}{'...' if len(response_str) > 200 else ''}")
                return response_str
            
            self.logger.warning("No messages in agent result")
            return "No response from agent"
        
        except Exception as e:
            self.logger.error(f"Error during chat: {e}", exc_info=True)
            raise
    
    def start_session(self, thread_id: str = "default") -> str:
        """
        Start a new grading session with inventory check.
        
        Args:
            thread_id: Conversation thread ID
            
        Returns:
            Initial agent response with inventory
        """
        self.logger.info(f"Starting new grading session (thread: {thread_id})")
        return self.chat(
            "I'm ready to start grading.",
            thread_id=thread_id
        )


def main():
    """Example usage of OpenGrader agent."""
    import sys
    
    # Get working directory from command line or use default
    if len(sys.argv) == 0:
        print("Working directory is required")
        return
    working_dir = sys.argv[1]
    
    print(f"OpenGrader starting in: {working_dir}")
    print("-" * 60)    
    agent = OpenGraderAgent(working_dir=str(working_dir))
    # Start interactive session
    thread_id = "demo"
    response = agent.start_session(thread_id=thread_id)
    print(f"OpenGrader: {response}")
    print("-" * 60)
    
    # Interactive loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input or user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break
            
            response = agent.chat(user_input, thread_id=thread_id)
            print(f"\nOpenGrader: {response}")
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
