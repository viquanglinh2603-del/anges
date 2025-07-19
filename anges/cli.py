#!/usr/bin/env python3
"""
Main CLI entry point for Anges.

This module serves as the unified command-line interface for all Anges functionality,
providing access to both the CLI agent interface and the web interface.
"""

import argparse
import sys
import os
import importlib
from typing import Optional, List
from anges.cli_interface import cli_runner
import traceback

def main():
    """
    Main entry point for the Anges CLI.
    
    Parses command-line arguments and dispatches to the appropriate functionality:
    - Interactive mode
    - File input mode
    - Direct question mode
    - Web interface
    """
    parser = argparse.ArgumentParser(description="Anges - AI Agent System")
    
    # Create subparsers for different command modes
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Default command (interactive mode or with parameters)
    default_parser = parser.add_argument_group("Interactive mode")
    default_parser.add_argument("--cmd_prefix", type=str, default="", 
                               help="Command prefix to prepend to all shell commands")
    default_parser.add_argument("--path", "--cmd_init_dir", type=str, default="", 
                               help="Initial directory for running commands")
    default_parser.add_argument("--agent", type=str, default="default",
                               choices=["default", "task_executor", "task_analyzer", "orchestrator"],
                               help="Agent type to use")
    default_parser.add_argument("--model", type=str, default="agent_default",
                               help="Model to use for inference")
    default_parser.add_argument("--logging", type=str, default="info",
                               choices=["info", "debug", "warning", "error", "critical"],
                               help="Logging level")
    default_parser.add_argument("--existing_stream_id", type=str,
                               help="Existing event stream ID to continue from")
    # File input mode
    parser.add_argument("-f", "--input-file", type=str, 
                        help="Run with an input file")
    
    # Direct question mode
    parser.add_argument("-q", "--question", type=str,
                        help="Run with a direct text input")
    
    # Interactive mode flag
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="Enter interactive mode")
    
    # Web interface mode
    ui_parser = subparsers.add_parser("ui", help="Launch the web interface")
    ui_parser.add_argument("--host", type=str, default="127.0.0.1",
                          help="Host address to bind")
    ui_parser.add_argument("--password", type=str,
                          help="Web interface password")
    ui_parser.add_argument("--port", type=int, default=5000,
                          help="Port number to bind")
    args = parser.parse_args()
    
    # Check if no arguments provided (should show help)
    if len(sys.argv) == 1:
        parser.print_help()
        return 0
    
    # Handle web interface mode
    if args.command == "ui":
        run_web_interface(host=args.host, password=args.password, port=args.port)
        return
    
    # Handle file input mode
    if args.input_file:
        run_cli_interface(
            input_file=args.input_file,
            cmd_prefix=args.cmd_prefix,
            cmd_init_dir=args.path,
            agent=args.agent,
            model=args.model,
            logging_level=args.logging,
            existing_stream_id=args.existing_stream_id
        )
        return
    
    # Handle direct question mode
    if args.question:
        # Create a temporary file with the question
        import tempfile
        temp_filename = tempfile.mktemp(suffix=".txt")
        try:
            with open(temp_filename, "w") as f:
                f.write(args.question)
            run_cli_interface(
                input_file=temp_filename,
                cmd_prefix=args.cmd_prefix,
                cmd_init_dir=args.path,
                agent=args.agent,
                model=args.model,
                logging_level=args.logging,
                existing_stream_id=args.existing_stream_id
            )
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
        return
    
    # Handle interactive mode (only when -i flag is explicitly provided)
    if args.interactive:
        run_cli_interface(
            input_file=None,
            cmd_prefix=args.cmd_prefix,
            cmd_init_dir=args.path,
            agent=args.agent,
            model=args.model,
            logging_level=args.logging,
            existing_stream_id=args.existing_stream_id
        )
        return
    
    # If we reach here, no valid mode was specified, show help
    parser.print_help()
    return 0

def run_cli_interface(
    question: Optional[str] = None,
    input_file: Optional[str] = None,
    cmd_prefix: str = "",
    cmd_init_dir: str = "",
    agent: str = "default",
    model: str = "agent_default",
    logging_level: str = "debug",
    existing_stream_id: Optional[str] = None,
) -> int:
    """Run the CLI interface with the given parameters.

    Args:
        question: Direct question to ask
        input_file: Path to file containing task description
        cmd_prefix: Command prefix to prepend to all shell commands
        cmd_init_dir: Initial directory for running commands
        agent: Type of agent to use
        model: Model to use for inference
        logging_level: Logging level
        existing_stream_id: Existing event stream ID to continue from

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        # Import the CLI runner module directly from the correct path
        # cli_runner = importlib.import_module('anges.cli_interface.cli_runner')

        # Create an argparse.Namespace object with the appropriate attributes
        args = argparse.Namespace()
        args.question = question
        args.input_file = input_file
        args.prefix_cmd = cmd_prefix
        args.cmd_init_dir = cmd_init_dir
        args.agent = agent
        args.model = model
        args.logging = logging_level.lower()  # Ensure lowercase for compatibility
        args.existing_stream_id = existing_stream_id

        # Call the run_cli_with_args function with our namespace object
        cli_runner.run_cli_with_args(args)
        return 0
    except ImportError as e:
        print(f"Error in run_cli_interface: Could not import CLI runner: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error in run_cli_interface: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1

def run_web_interface(
    host: str = "127.0.0.1",
    password: Optional[str] = None,
    port: int = 5000
):
    """Run the web interface with the given parameters.

    Args:
        host: Host address to bind (default: 127.0.0.1)
        password: Password for accessing the web interface (optional)
        port: Port number to listen on (default: 5000)
    """
    if isinstance(port, str):
        port = int(port)

    try:
        # Import the web interface module using importlib
        web_interface = importlib.import_module('anges.web_interface.web_interface')

        # Set password if provided
        if password:
            # Try to use the set_password function if it exists, otherwise set APP_PASSWORD directly
            try:
                web_interface.set_password(password)
            except AttributeError:
                # Fallback: set APP_PASSWORD directly if set_password function is not available
                web_interface.APP_PASSWORD = password
                print("Note: Using fallback method to set password")

        # Run the app
        web_interface.run_app(
            web_interface.app,
            host=host,
            port=port,
            debug=False
        )

        return 0
    except ImportError as e:
        print(f"Error: Could not import web interface: {e}", file=sys.stderr)
        sys.exit(1)  # Exit with error code 1 for import errors
    except Exception as e:
        print(f"Error in run_web_interface: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
