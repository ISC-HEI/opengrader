# Utility functions and classes for OpenGrader

import sys
import threading
import time
import logging
import json
from datetime import datetime
from pathlib import Path


def print_logo():
    """Print the OpenGrader ASCII logo."""
    logo = """
  ██████╗ ██████╗ ███████╗███╗   ██╗ ██████╗ ██████╗  █████╗ ██████╗ ███████╗██████╗ 
 ██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
 ██║   ██║██████╔╝█████╗  ██╔██╗ ██║██║  ███╗██████╔╝███████║██║  ██║█████╗  ██████╔╝
 ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██║   ██║██╔══██╗██╔══██║██║  ██║██╔══╝  ██╔══██╗
 ╚██████╔╝██║     ███████╗██║ ╚████║╚██████╔╝██║  ██║██║  ██║██████╔╝███████╗██║  ██║
  ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝
 
 OpenGrader is a modular agentic system to grade exams. Made with ❤️  by the ISC team.
 
    """
    print(logo)


def print_agent(message: str):
    """Print agent message in yellow color."""
    BLUE = "\033[94m"
    RESET = "\033[0m"
    print(f"{BLUE}OpenGrader: {message}{RESET}")


class ProgressSpinner:
    """Simple progress spinner for console output."""
    
    def __init__(self, message="Working"):
        self.message = message
        self.running = False
        self.thread = None
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.idx = 0
    
    def _spin(self):
        """Spinner animation loop."""
        while self.running:
            sys.stdout.write(f"\r{self.message} {self.spinner_chars[self.idx]}")
            sys.stdout.flush()
            self.idx = (self.idx + 1) % len(self.spinner_chars)
            time.sleep(0.1)
    
    def start(self):
        """Start the spinner."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._spin, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Stop the spinner and clear the line."""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=0.5)
            sys.stdout.write("\r" + " " * (len(self.message) + 3) + "\r")
            sys.stdout.flush()


def setup_logging(logger_name: str = "OpenGrader") -> logging.Logger:
    """
    Set up comprehensive logging for agent activity.

    Returns:
        Configured logger instance
    """
    # Create timestamp for log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{logger_name.lower()}_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
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
    console_handler.setLevel(logging.WARN)
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"{logger_name} logging initialized. Log file: {log_file}")
    
    return logger


def log_thought_signatures(logger: logging.Logger, response):
    """Extract and log thought signatures from model response."""
    try:
        # Check if response has choices and messages
        if hasattr(response, 'choices') and response.choices:
            for idx, choice in enumerate(response.choices):
                message = choice.message if hasattr(choice, 'message') else choice
                
                # Log tool calls with thought signatures (DEBUG level only)
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    logger.debug(f"Tool calls found in response (choice {idx})")
                    
                    for tool_idx, tool_call in enumerate(message.tool_calls):
                        logger.debug(
                            f"Tool call {tool_idx}: {tool_call.function.name if hasattr(tool_call, 'function') else 'unknown'}"
                        )
                        
                        # Extract thought signature
                        if hasattr(tool_call, 'provider_specific_fields'):
                            fields = tool_call.provider_specific_fields
                            if isinstance(fields, dict) and 'thought_signature' in fields:
                                thought_sig = fields['thought_signature']
                                # Log full signature at DEBUG level
                                logger.debug(f"Full thought signature: {thought_sig}")
                            elif hasattr(fields, 'get'):
                                thought_sig = fields.get('thought_signature')
                                if thought_sig:
                                    logger.debug(f"Full thought signature: {thought_sig}")
                        
                        # Log tool call arguments
                        if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'arguments'):
                            try:
                                args = json.loads(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments
                                logger.debug(f"Tool arguments: {json.dumps(args, indent=2)}")
                            except:
                                logger.debug(f"Tool arguments (raw): {tool_call.function.arguments}")
                
                # Log message content (DEBUG level only)
                if hasattr(message, 'content') and message.content:
                    logger.debug(f"Model response content: {message.content[:200]}{'...' if len(message.content) > 200 else ''}")
                    logger.debug(f"Full model response: {message.content}")
    
    except Exception as e:
        logger.error(f"Error extracting thought signatures: {e}", exc_info=True)


def log_agent_state(logger: logging.Logger, result):
    """Log detailed agent state and messages."""
    try:
        if result and isinstance(result, dict):
            # Log all messages in the result
            if "messages" in result:
                logger.debug(f"Agent returned {len(result['messages'])} messages")
                
                for idx, msg in enumerate(result['messages']):
                    msg_type = type(msg).__name__
                    logger.debug(f"Message {idx} type: {msg_type}")
                    
                    # Log message content
                    if hasattr(msg, 'content'):
                        content = msg.content
                        if content:
                            logger.debug(f"Message {idx} content: {content[:200]}{'...' if len(str(content)) > 200 else ''}")
                    
                    # Log tool calls (DEBUG level only - not shown on console)
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        logger.debug(f"Message {idx} contains {len(msg.tool_calls)} tool calls")
                        for tc_idx, tc in enumerate(msg.tool_calls):
                            if hasattr(tc, 'function'):
                                logger.debug(f"  Tool {tc_idx}: {tc.function.name}")
            
            # Log any other relevant state
            for key in result.keys():
                if key != "messages":
                    logger.debug(f"Result key '{key}': {type(result[key])}")
    
    except Exception as e:
        logger.error(f"Error logging agent state: {e}", exc_info=True)
