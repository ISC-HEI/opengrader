# OpenGrader agent using LangGraph deep agents with skills for exam grading

import sys
import os
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_litellm import ChatLiteLLM
import sqlite3
from utils import ProgressSpinner, setup_logging, log_thought_signatures, log_agent_state, print_logo, print_agent


class OpenGraderAgent:
    """
    Conversational grading assistant with agentic capabilities.
    Uses LangGraph deep agents with filesystem backend and SQLite checkpointing.
    """
    
    def __init__(
        self,
        working_dir: str,
        skills_dir: str = None,
    ):
        """
        Initialize the OpenGrader agent.
        
        Args:
            working_dir: Directory where exam files are located (teacher's workspace)
            skills_dir: Path to skills directory (defaults to ./skills)
        """
        self.working_dir = Path(working_dir).resolve()
        
        # Set up logging
        self.logger = setup_logging()
        self.logger.info(f"Working directory: {self.working_dir}")
        
        # Set up skills directory
        if skills_dir is None:
            # Default: skills relative to this file
            project_root = Path(__file__).parent
            self.skills_dir = project_root / "skills"
        else:
            self.skills_dir = Path(skills_dir).resolve()
        assert os.path.exists(self.skills_dir), f"Skills directory {self.skills_dir} does not exist"
                
        # LiteLLM loads OPENROUTER_API_KEY from .env automatically.
        model_name = os.getenv("OPENGRADER_MODEL", "openrouter/google/gemini-3-flash-preview")
        self.model = ChatLiteLLM(
            model=model_name,
            temperature=0.7,
        )
        
        # Create SQLite checkpointer
        conn = sqlite3.connect("opengrader.db", check_same_thread=False)
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
            model=self.model,
        )
        
        # System context for the agent
        self.system_context = self._build_system_context()
    
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
        
        self.logger.debug(f"Full message with context: {full_message}...")
        
        progress_spinner = ProgressSpinner("Thinking")
        progress_spinner.start()
        
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
            log_agent_state(self.logger, result)
            
            # Extract the last message from the agent
            if result and "messages" in result:
                last_message = result["messages"][-1]
                
                # Log thought signatures if present
                log_thought_signatures(self.logger, last_message)
                
                if hasattr(last_message, "content"):
                    response_content = last_message.content
                    # Log full response to DEBUG only
                    self.logger.debug(f"Full agent response: {response_content}")
                    return response_content
                
                response_str = str(last_message)
                self.logger.debug(f"Agent response (str): {response_str}")
                return response_str
            
            self.logger.warning("No messages in agent result")
            return "No response from agent"
        
        except Exception as e:
            self.logger.error(f"Error during chat: {e}", exc_info=True)
            raise
        
        finally:
            if progress_spinner:
                progress_spinner.stop()
    
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
    
    print_logo()
    
    # Get working directory from command line or die
    if len(sys.argv) == 0:
        print("Working directory is required")
        return
    working_dir = sys.argv[1]
    
    print(f"\nStarting in: {working_dir}")
    print("-" * 60)    
    agent = OpenGraderAgent(working_dir=str(working_dir))
    # Start interactive session
    thread_id = "demo"
    response = agent.start_session(thread_id=thread_id)
    print_agent(response)
    print("-" * 60)
    
    # Interactive agent loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input or user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break
            
            response = agent.chat(user_input, thread_id=thread_id)
            print()
            print_agent(response)
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
