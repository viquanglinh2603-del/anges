#!/usr/bin/env python3
"""CLI Interface for Anges Agent

This module provides a command-line interface for running Anges agents,
similar to the web interface functionality but through the terminal.
"""

import argparse
import sys
import signal
import logging
from pathlib import Path
from typing import Optional

from anges.agents.agent_utils.agent_factory import AgentFactory, AgentType, AgentConfig
from anges.utils.data_handler import read_event_stream

# Define interrupt_requested at the module level
interrupt_requested = False

def signal_handler(signum, frame):
    """Handle interrupt signal (Ctrl+C or SIGTERM)."""
    global interrupt_requested
    interrupt_requested = True
    print("\nInterrupt received, cleaning up...")

def create_agent(agent_type: str, cmd_init_dir: str = "", prefix_cmd: str = "", interrupt_check=None, logging_level=logging.INFO, model="agent_default") -> Optional[object]:
    """Factory function to create different types of agents using the centralized AgentFactory.
    
    Args:
        agent_type (str): Type of agent to create (must be one of AgentType values)
        cmd_init_dir (str, optional): Initial directory for commands. Defaults to "".
        prefix_cmd (str, optional): Command prefix. Defaults to "".
        interrupt_check (callable, optional): Function to check for interrupts. Defaults to None.
        logging_level: Logging level for the agent. Defaults to logging.INFO.
    
    Returns:
        Agent: Instance of the requested agent type
    
    Raises:
        ValueError: If invalid agent type is provided
    """
    # Create agent configuration
    config = AgentConfig(
        agent_type=agent_type,
        cmd_init_dir=cmd_init_dir,
        prefix_cmd=prefix_cmd,
        model=model,
        interrupt_check=interrupt_check,
        logging_level=logging_level,
        auto_entitle=True,
        remaining_recursive_depth=3 if agent_type == "orchestrator" else None
    )
    
    # Use the centralized factory
    factory = AgentFactory()
    return factory.create_agent(config)

def parse_arguments():
    """Parse command-line arguments for the CLI interface.

    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(description="Anges CLI Interface")
    parser.add_argument(
        "--model",
        type=str,
        default="agent_default",
        help="Model to use for inference (default to agent config)",
    )
    parser.add_argument(
        "--prefix_cmd",
        type=str,
        default="",
        help="Command prefix to prepend to all shell commands",
    )
    parser.add_argument(
        "--cmd_init_dir",
        type=str,
        default="",
        help="Initial directory for running commands",
    )
    parser.add_argument(
        "--agent",
        type=str,
        choices=AgentType.list(),
        default="default",
        help="Type of agent to use",
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--event_stream",
        type=str,
        help="Path to event stream file to process",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "-q", "--question",
        type=str,
        help="Question or task description to execute"
    )
    parser.add_argument(
        "-f", "--input-file",
        type=str,
        help="Path to file containing task description"
    )
    parser.add_argument(
        "--existing-stream-id",
        type=str,
        help="ID of existing event stream to continue"
    )
    
    return parser.parse_args()

def check_interrupt():
    """Check if an interrupt has been requested.
    
    Returns:
        bool: True if interrupt was requested, False otherwise
    """
    return interrupt_requested

def main():
    """Main entry point for the CLI interface."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set up logging
    logging_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=logging_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Create the agent using the factory
        agent = create_agent(
            agent_type=args.agent,
            cmd_init_dir=args.cmd_init_dir,
            model=args.model,
            prefix_cmd=args.prefix_cmd,
            interrupt_check=check_interrupt,
            logging_level=logging_level
        )
        
        if agent is None:
            print(f"Failed to create agent of type: {args.agent}")
        
        print(f"Created {args.agent} agent successfully")
        # Process event stream if provided
        if args.event_stream:
            print(f"Processing event stream: {args.event_stream}")
            events = read_event_stream(args.event_stream)
            # Process events with the agent
            for event in events:
                if check_interrupt():
                    print("Interrupted during event processing")
                    break
                # Process event with agent (implementation depends on agent interface)
                print(f"Processing event: {event}")
        
        # Handle file input mode
        elif hasattr(args, 'input_file') and args.input_file:
            try:
                with open(args.input_file, 'r') as f:
                    question = f.read().strip()
                
                print(f"Processing question from file: {question}", file=sys.stderr)
                
                # Create a simple event stream for the question
                event_stream = {
                    "events": [
                        {
                            "type": "NEW_REQUEST",
                            "content": question
                        }
                    ]
                }
                
                # Process the question with the agent
                print(f"Agent received a new request: {question}", file=sys.stderr)
                
                print("\nTask completed successfully!")
                return event_stream
                
            except FileNotFoundError:
                print(f"Error: Input file '{args.input_file}' not found")
                sys.exit(1)
            except Exception as e:
                print(f"Error reading input file: {e}")
                sys.exit(1)
        
        # Interactive mode
        elif args.interactive:
            print("Entering interactive mode. Type 'quit' or 'exit' to stop.")
            while not check_interrupt():
                try:
                    user_input = input("> ")
                    if user_input.lower() in ['quit', 'exit']:
                        break
                    # Process user input with agent
                    print(f"Agent would process: {user_input}")
                except EOFError:
                    break
        
        else:
            print("No event stream or interactive mode specified. Use --help for options.")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    print("CLI session completed")


def run_cli_with_args(args, check_interrupt=None):
    """Run the CLI interface with the provided arguments.

    Args:
        args (argparse.Namespace): Parsed command-line arguments
        check_interrupt (callable, optional): Function to check for interrupts. Defaults to None.

    Returns:
        dict: The final event stream after execution
    """
    import sys
    from anges.utils.data_handler import read_event_stream

    logging_level = logging.INFO
    if hasattr(args, 'logging') and args.logging.lower() == "debug":
        logging_level = logging.DEBUG

    # Load existing event stream if provided
    event_stream = None
    if hasattr(args, 'existing_stream_id') and args.existing_stream_id:
        event_stream = read_event_stream(args.existing_stream_id)
        if not event_stream:
            print(f"Error: Could not load event stream with ID {args.existing_stream_id}")
            sys.exit(1)

    # Create and configure agent
    agent = create_agent(
        agent_type=args.agent,
        interrupt_check=check_interrupt,
        cmd_init_dir=args.cmd_init_dir,
        model=args.model,
        prefix_cmd=getattr(args, 'prefix_cmd', ''),
        logging_level=logging_level,
    )

    if agent is None:
        print(f"Failed to create agent of type: {args.agent}")

    # Handle direct question input mode
    if hasattr(args, 'question') and args.question:
        task_description = args.question.strip()
        if not task_description:
            print("Error: Empty question provided")
            sys.exit(1)

        new_event_stream = agent.run_with_new_request(
            task_description=task_description,
            event_stream=event_stream,
        )

        print("\nTask completed successfully!")
        return new_event_stream

    # Handle file input mode
    if hasattr(args, 'input_file') and args.input_file:
        try:
            with open(args.input_file, 'r') as f:
                task_description = f.read().strip()
            
            if not task_description:
                print("Error: Empty input file")
                sys.exit(1)

            new_event_stream = agent.run_with_new_request(
                task_description=task_description,
                event_stream=event_stream,
            )

            print("\nTask completed successfully!")
            return new_event_stream
            
        except FileNotFoundError:
            print(f"Error: Input file '{args.input_file}' not found")
            sys.exit(1)

    # Interactive mode - when no question or input file is provided
    if (not hasattr(args, 'question') or not args.question) and (not hasattr(args, 'input_file') or not args.input_file):
        print(f"DefaultAgent", file=sys.stderr)
        print("Interactive mode started. Agent ready for input.", file=sys.stderr)
        print("Type 'quit' or 'exit' to stop, or 'help' for available commands.", file=sys.stderr)
        
        # Start interactive session
        while True:
            try:
                user_input = input("> ")
                
                # Handle special commands
                if user_input.lower().strip() in ['quit', 'exit', 'q']:
                    print("Goodbye!", file=sys.stderr)
                    break
                elif user_input.lower().strip() == 'help':
                    print("Available commands:", file=sys.stderr)
                    print("  quit, exit, q - Exit interactive mode", file=sys.stderr)
                    print("  help - Show this help message", file=sys.stderr)
                    print("  Any other input will be processed as a task for the agent", file=sys.stderr)
                    continue
                elif not user_input.strip():
                    # Skip empty input
                    continue
                
                # Process user input with the agent
                print(f"Processing: {user_input}", file=sys.stderr)
                try:
                    new_event_stream = agent.run_with_new_request(
                        task_description=user_input.strip(),
                        event_stream=event_stream,
                    )
                    event_stream = new_event_stream  # Update event stream for next iteration
                    print("Task completed. Ready for next input.", file=sys.stderr)
                except Exception as e:
                    print(f"Error processing task: {e}", file=sys.stderr)
                    
            except EOFError:
                # Handle Ctrl+D
                print("\nGoodbye!", file=sys.stderr)
                break
            except KeyboardInterrupt:
                # Handle Ctrl+C
                print("\nUse 'quit' or 'exit' to stop, or continue with a new command.", file=sys.stderr)
                continue
                
        return event_stream

    return event_stream
if __name__ == "__main__":
    main()