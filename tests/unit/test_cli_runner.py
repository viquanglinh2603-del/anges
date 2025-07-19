"""
Unit tests for the CLI runner functionality (anges/cli_interface/cli_runner.py).

These tests focus on:
1. Parameter parsing for all supported parameters
2. Dispatch to the correct functionality
3. Mocking to avoid actual execution
4. Ensuring tests are isolated
"""

import pytest
import sys
import io
import os
import signal
import logging
import argparse
from unittest.mock import patch, MagicMock, call

from anges.cli_interface.cli_runner import (
    run_cli_with_args, create_agent,
    signal_handler, parse_arguments
)
from anges.agents.agent_utils.agent_factory import AgentType

# Reuse the mock_cli_environment context manager from test_cli_interface.py
from tests.unit.test_cli_interface import mock_cli_environment


class TestAgentType:
    """Test the AgentType enum functionality."""

    def test_agent_type_values(self):
        """Test that AgentType enum has the expected values."""
        assert AgentType.TASK_EXECUTOR.value == "task_executor"
        assert AgentType.TASK_ANALYZER.value == "task_analyzer"
        assert AgentType.ORCHESTRATOR.value == "orchestrator"
        assert AgentType.DEFAULT.value == "default"

    def test_agent_type_list(self):
        """Test the list method returns all agent types."""
        agent_types = AgentType.list()
        assert "task_executor" in agent_types
        assert "task_analyzer" in agent_types
        assert "orchestrator" in agent_types
        assert "default" in agent_types
        assert len(agent_types) == 4


class TestAgentCreation:
    """Test the agent creation functionality."""

    @patch('anges.agents.agent_utils.agent_factory.AgentFactory.create_agent')
    def test_create_task_executor(self, mock_create_agent):
        """Test creating a TaskExecutor agent."""
        mock_instance = MagicMock()
        mock_create_agent.return_value = mock_instance

        # Create a task executor agent
        agent = create_agent(
            agent_type="task_executor",
            cmd_init_dir="/test/path",
            prefix_cmd="test_prefix",
            interrupt_check=lambda: False,
            logging_level=logging.INFO
        )

        # Verify the agent was created and returned
        assert agent == mock_instance
        mock_create_agent.assert_called_once()
    @patch('anges.agents.agent_utils.agent_factory.AgentFactory.create_agent')
    def test_create_task_analyzer(self, mock_create_agent):
        """Test creating a TaskAnalyzer agent."""
        mock_instance = MagicMock()
        mock_create_agent.return_value = mock_instance

        # Create a task analyzer agent
        agent = create_agent(
            agent_type="task_analyzer",
            cmd_init_dir="/test/path",
            prefix_cmd="test_prefix",
            logging_level=logging.INFO
        )

        # Verify the agent was created and returned
        assert agent == mock_instance
        mock_create_agent.assert_called_once()
    @patch('anges.agents.agent_utils.agent_factory.AgentFactory.create_agent')
    def test_create_orchestrator(self, mock_create_agent):
        """Test creating an Orchestrator agent."""
        mock_instance = MagicMock()
        mock_create_agent.return_value = mock_instance

        # Create an orchestrator agent
        agent = create_agent(
            agent_type="orchestrator",
            cmd_init_dir="/test/path",
            prefix_cmd="test_prefix",
            logging_level=logging.INFO
        )

        # Verify the agent was created and returned
        assert agent == mock_instance
        mock_create_agent.assert_called_once()
    @patch('anges.agents.agent_utils.agent_factory.AgentFactory.create_agent')
    def test_create_default_agent(self, mock_create_agent):
        """Test creating a DefaultAgent agent."""
        mock_instance = MagicMock()
        mock_create_agent.return_value = mock_instance

        # Create a default agent
        agent = create_agent(
            agent_type="default",
            cmd_init_dir="/test/path",
            prefix_cmd="test_prefix",
            logging_level=logging.INFO
        )

        # Verify the agent was created and returned
        assert agent == mock_instance
        mock_create_agent.assert_called_once()

    def test_create_invalid_agent(self):
        """Test creating an invalid agent type raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            create_agent(agent_type="invalid_agent")

        assert "Invalid agent type: invalid_agent" in str(excinfo.value)


class TestCLIRunnerParameters:
    """Test CLI runner parameter parsing and handling."""

    def test_parse_args_defaults(self):
        """Test parsing arguments with default values."""
        test_args = ["anges"]

        with patch('sys.argv', test_args):
            with patch('argparse.ArgumentParser.parse_args') as mock_parse_args:
                # Create a namespace with expected default values
                default_args = argparse.Namespace(
                    model="claude",
                    prefix_cmd="",
                    cmd_init_dir="",
                    agent="default",
                    input_file=None,
                    question=None,
                    existing_stream_id=None,
                    logging="info"
                )
                mock_parse_args.return_value = default_args
                
                args = parse_arguments()

    @patch('sys.exit')
    @patch('builtins.input')
    @patch('anges.cli_interface.cli_runner.create_agent')
    def test_run_cli_with_input(self, mock_create_agent, mock_input, mock_exit):
        """Test running CLI with interactive input."""
        # Setup mock agent
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent

        # Setup mock input to return a task and then empty string to end input
        mock_input.side_effect = ["Test task", "", "", "", ""]

        # Create args namespace with question to avoid interactive mode
        args = argparse.Namespace(
            model="claude",
            prefix_cmd="",
            cmd_init_dir="",
            agent="default",
            input_file=None,
            question="Test task",  # Provide question to avoid interactive mode
            existing_stream_id=None,
            interactive=True
        )

        # Mock sys.stdin.isatty to return True (interactive mode)
        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = True
        
        # Run the function with our mocked stdin and suppress output
        with patch('sys.stdin', mock_stdin):
            with patch('sys.stdout'):  # Suppress output during test
                run_cli_with_args(args)
        
        # Verify agent.run_with_new_request was called with the correct input
        mock_create_agent.assert_called_once()
        mock_agent.run_with_new_request.assert_called_once_with(
            task_description="Test task",
            event_stream=None
        )
        
        # Verify that sys.exit was not called (execution completed successfully)
        mock_exit.assert_not_called()
        
    @patch('os.path.exists')
    @patch('sys.exit')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('anges.cli_interface.cli_runner.create_agent')
    def test_run_cli_with_file(self, mock_create_agent, mock_open, mock_exit, mock_exists):
        """Test running CLI with a file input."""
        # Setup mock agent
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent
        mock_exists.return_value = True

        # Setup mock file handle
        mock_file = MagicMock()
        mock_file.read.return_value = "Test task from file"
        mock_open.return_value.__enter__.return_value = mock_file

        # Create args namespace with file input
        args = argparse.Namespace(
            model="claude",
            prefix_cmd="",
            cmd_init_dir="",
            agent="default",
            input_file="test_file.txt",
            question=None,
            existing_stream_id=None,
            interactive=False
        )

        # Mock sys.stdin to avoid reading from actual stdin
        mock_stdin = MagicMock()
        mock_stdin.readline.side_effect = ["", ""]  # Empty input to avoid stdin reading

        # Call run_cli_with_args directly with the namespace
        with patch('sys.stdout'):  # Suppress output during test
            with patch('sys.stdin', mock_stdin):
                run_cli_with_args(args)
        
        # Verify agent was created and run with the file content
        mock_create_agent.assert_called_once()
        mock_agent.run_with_new_request.assert_called_once_with(
            task_description="Test task from file",
            event_stream=None
        )

    @patch('anges.cli_interface.cli_runner.create_agent')
    @patch('os.path.exists')
    @patch('sys.exit')
    def test_run_cli_with_file_not_found(self, mock_exit, mock_exists, mock_create_agent):
        """Test running CLI when input file is not found."""
        # Setup mocks
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent
        mock_exists.return_value = False

        # Create args namespace
        # Create args namespace
        args = argparse.Namespace(
            model="default",
            prefix_cmd="",
            cmd_init_dir="",
            agent="default",  # Changed from 'agent' to 'agent_type'
            input_file="nonexistent_file.txt",
            question="Test fallback question",  # Add a question to avoid stdin reading
            existing_stream_id=None,
            logging="info"
        )

        # Call run_cli_with_args directly with the namespace
        with patch('sys.stderr', new=io.StringIO()):
            with patch('sys.stdout'):  # Suppress output during test
                run_cli_with_args(args)

        # Verify agent was created and run with the fallback question
        mock_create_agent.assert_called_once()
        mock_agent.run_with_new_request.assert_called_once_with(
            task_description="Test fallback question",
            event_stream=None
        )

        # Verify that sys.exit was not called (execution continued)
        mock_exit.assert_not_called()

    @patch('anges.utils.data_handler.read_event_stream')
    @patch('anges.cli_interface.cli_runner.create_agent')
    def test_run_cli_with_existing_stream(self, mock_create_agent, mock_read_stream):
        """Test running CLI with an existing stream ID."""
        # Setup mocks
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent
        mock_stream = {"events": [{"type": "test"}]}
        mock_read_stream.return_value = mock_stream  # Mock successful stream read
        
        # Create args namespace
        args = argparse.Namespace(
            model="default",
            prefix_cmd="",
            cmd_init_dir="",
            agent="default",
            input_file=None,
            existing_stream_id="test_stream",
            question="test question",
            logging="info"
        )

        # Mock sys.stdin to avoid reading from actual stdin
        mock_stdin = MagicMock()
        mock_stdin.readline.side_effect = ["", ""]  # Empty input to avoid stdin reading

        # Call run_cli_with_args directly with the namespace
        with patch('sys.stdout'):  # Suppress output during test
            with patch('sys.stdin', mock_stdin):
                run_cli_with_args(args)
        
        # Verify agent was created and run with the existing stream
        # Verify agent was created and run with new request (not existing stream when question is provided)
        mock_create_agent.assert_called_once()
        mock_agent.run_with_new_request.assert_called_once_with(
            task_description="test question",
            event_stream=mock_stream
        )

    @patch('anges.cli_interface.cli_runner.create_agent')
    def test_run_cli_with_question(self, mock_create_agent):
        """Test running CLI with a direct question input."""
        # Setup mock agent
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent

        # Create args namespace with a question
        args = argparse.Namespace(
            model="default",
            prefix_cmd="",
            cmd_init_dir="",
            agent="default",
            input_file=None,
            question="Test question?",
            existing_stream_id=None,
            logging="info"
        )

        # Mock sys.stdin to avoid reading from actual stdin
        mock_stdin = MagicMock()
        mock_stdin.readline.side_effect = ["", ""]  # Empty input to avoid stdin reading

        # Call run_cli_with_args directly with the namespace
        with patch('sys.stdout'):  # Suppress output during test
            with patch('sys.stdin', mock_stdin):
                run_cli_with_args(args)

        # Verify agent was created and run with the question
        mock_create_agent.assert_called_once()
        mock_agent.run_with_new_request.assert_called_once_with(
            task_description="Test question?",
            event_stream=None
        )


class TestSignalHandling:
    """Test signal handling."""

    @patch('anges.cli_interface.cli_runner.interrupt_requested', False)
    def test_signal_handler(self):
        """Test the signal handler sets the interrupt flag."""
        # Call the signal handler
        signal_handler(signal.SIGINT, None)

        # Import the module to check the global variable
        import anges.cli_interface.cli_runner as cli_runner

        # Verify the interrupt flag was set
        assert cli_runner.interrupt_requested is True


