#!/usr/bin/env python3
"""
Basic Usage Example for Anges Framework

This example demonstrates the fundamental usage of the Anges framework,
including creating a default agent and running simple tasks.
"""

import logging
from anges.agents.default_agent import DefaultAgent
from anges.config import config
from anges.utils.inference_api import INFERENCE_FUNC_DICT


def basic_agent_example():
    """
    Demonstrates basic agent creation and task execution.
    """
    print("=== Basic Anges Agent Usage Example ===")
    
    # Create a default agent with basic configuration
    agent = DefaultAgent(
        cmd_init_dir="./",  # Working directory for shell commands
        logging_level=logging.INFO,
        auto_entitle=True  # Automatically generate titles for conversations
    )
    
    print(f"Created agent with ID: {agent.uid}")
    print(f"Agent type: DefaultAgent")
    print(f"Available actions: {[action.type for action in agent.registered_actions]}")
    
    # Example 1: Simple file operations task
    print("\n--- Example 1: File Operations Task ---")
    task1 = """
    Create a simple text file called 'hello.txt' with the content 'Hello, Anges Framework!' 
    and then display its contents.
    """
    
    try:
        result_stream = agent.run_with_new_request(task1)
        print(f"Task completed. Event stream has {len(result_stream.events_list)} events.")
        print(f"Final status: {result_stream.events_list[-1].type}")
    except Exception as e:
        print(f"Error running task: {e}")
    
    # Example 2: System information task
    print("\n--- Example 2: System Information Task ---")
    task2 = """
    Check the current working directory, list the files in it, 
    and show the current date and time.
    """
    
    try:
        result_stream = agent.run_with_new_request(task2)
        print(f"Task completed. Event stream has {len(result_stream.events_list)} events.")
        print(f"Final status: {result_stream.events_list[-1].type}")
    except Exception as e:
        print(f"Error running task: {e}")


def agent_with_custom_config_example():
    """
    Demonstrates creating an agent with custom configuration.
    """
    print("\n=== Agent with Custom Configuration Example ===")
    
    # Create agent with custom settings
    custom_agent = DefaultAgent(
        cmd_init_dir="/tmp",  # Different working directory
        prefix_cmd="echo 'Starting command:' && ",  # Prefix for shell commands
        max_consecutive_actions_to_summarize=3,  # Summarize after 3 actions
        logging_level=logging.DEBUG,
        auto_entitle=False
    )
    
    print(f"Created custom agent with ID: {custom_agent.uid}")
    print(f"Working directory: {custom_agent.cmd_init_dir}")
    print(f"Command prefix: {custom_agent.prefix_cmd}")
    
    # Run a task that will use the custom configuration
    task = """
    Create a temporary file in the current directory with today's date,
    then verify it was created successfully.
    """
    
    try:
        result_stream = custom_agent.run_with_new_request(task)
        print(f"Task completed with {len(result_stream.events_list)} events.")
    except Exception as e:
        print(f"Error running custom agent task: {e}")


def event_stream_inspection_example():
    """
    Demonstrates how to inspect and work with event streams.
    """
    print("\n=== Event Stream Inspection Example ===")
    
    agent = DefaultAgent(logging_level=logging.WARNING)  # Reduce logging noise
    
    task = "List the current directory contents and count the number of files."
    
    try:
        result_stream = agent.run_with_new_request(task)
        
        print(f"Event Stream ID: {result_stream.uid}")
        print(f"Total events: {len(result_stream.events_list)}")
        print(f"Event summaries: {len(result_stream.event_summaries_list)}")
        
        print("\n--- Event Details ---")
        for i, event in enumerate(result_stream.events_list):
            print(f"Event {i+1}:")
            print(f"  Type: {event.type}")
            print(f"  Reasoning: {event.reasoning[:100]}..." if len(event.reasoning) > 100 else f"  Reasoning: {event.reasoning}")
            if hasattr(event, 'message') and event.message:
                print(f"  Message: {event.message[:100]}..." if len(event.message) > 100 else f"  Message: {event.message}")
            print()
            
    except Exception as e:
        print(f"Error in event stream inspection: {e}")


def message_handler_example():
    """
    Demonstrates how to use custom message handlers to capture agent output.
    """
    print("\n=== Message Handler Example ===")
    
    # List to capture messages
    captured_messages = []
    
    def custom_message_handler(message: str):
        """Custom handler that captures messages."""
        captured_messages.append(message)
        print(f"[CAPTURED]: {message}")
    
    # Create agent and register the message handler
    agent = DefaultAgent(logging_level=logging.WARNING)
    agent.message_handlers.append(custom_message_handler)
    
    task = "Echo 'Hello from Anges!' and create a small test file."
    
    try:
        result_stream = agent.run_with_new_request(task)
        
        print(f"\nCaptured {len(captured_messages)} messages:")
        for i, msg in enumerate(captured_messages):
            print(f"  {i+1}. {msg[:100]}..." if len(msg) > 100 else f"  {i+1}. {msg}")
            
    except Exception as e:
        print(f"Error in message handler example: {e}")


if __name__ == "__main__":
    print("Anges Framework Basic Usage Examples")
    print("====================================\n")
    
    try:
        # Run all examples
        basic_agent_example()
        agent_with_custom_config_example()
        event_stream_inspection_example()
        message_handler_example()
        
        print("\n=== All Examples Completed ===")
        print("These examples demonstrate the core functionality of the Anges framework.")
        print("For more advanced usage, see the other example files in this directory.")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure you have the Anges framework properly installed and configured.")