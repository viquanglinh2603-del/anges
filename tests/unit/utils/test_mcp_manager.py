import sys
import unittest
from unittest.mock import patch, MagicMock

import pytest

from anges.utils.mcp_manager import McpStdioClient, McpManager


class TestMcpStdioClient(unittest.TestCase):
    """Test cases for McpStdioClient functionality"""

    def setUp(self):
        """Set up test environment"""
        self.client = McpStdioClient(
            name="dummy_mcp_server",
            command=sys.executable,
            args=["tests/unit/utils/dummy_mcp_server.py"]
        )

    def test_client_initialization(self):
        """Test MCP client initialization"""
        self.assertEqual(self.client.name, "dummy_mcp_server")
        self.assertEqual(self.client.command, sys.executable)
        self.assertEqual(self.client.args, ["tests/unit/utils/dummy_mcp_server.py"])

    def test_to_dict(self):
        """Test client information serialization"""
        client_dict = self.client.to_dict()
        expected_keys = {"name", "command", "args"}
        self.assertEqual(set(client_dict.keys()), expected_keys)
        self.assertEqual(client_dict["name"], "dummy_mcp_server")
        self.assertEqual(client_dict["command"], sys.executable)
        self.assertEqual(client_dict["args"], ["tests/unit/utils/dummy_mcp_server.py"])

    @pytest.mark.asyncio
    @patch('anges.utils.mcp_manager.stdio_client')
    @patch('anges.utils.mcp_manager.ClientSession')
    async def test_list_tools_success(self, mock_session_class, mock_stdio_client):
        """Test successful tool listing"""
        # Mock stdio client
        mock_stdio = MagicMock()
        mock_writer = MagicMock()
        mock_stdio_client.return_value.__aenter__.return_value = (mock_stdio, mock_writer)
        
        # Mock client session
        mock_session = MagicMock()
        mock_session.initialize = MagicMock()
        mock_tools_response = MagicMock()
        mock_tools_response.tools = [
            MagicMock(name="echo"),
            MagicMock(name="add_numbers")
        ]
        mock_session.list_tools = MagicMock(return_value=mock_tools_response)
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        tools = await self.client.list_tools()
        
        self.assertEqual(len(tools), 2)
        mock_session.initialize.assert_called_once()
        mock_session.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_failure(self):
        """Test failed tool listing"""
        with patch('anges.utils.mcp_manager.stdio_client', side_effect=Exception("Connection failed")):
            with self.assertRaises(Exception):
                await self.client.list_tools()

    @pytest.mark.asyncio
    @patch('anges.utils.mcp_manager.stdio_client')
    @patch('anges.utils.mcp_manager.ClientSession')
    async def test_call_tool_success(self, mock_session_class, mock_stdio_client):
        """Test successful tool call"""
        # Mock stdio client
        mock_stdio = MagicMock()
        mock_writer = MagicMock()
        mock_stdio_client.return_value.__aenter__.return_value = (mock_stdio, mock_writer)
        
        # Mock client session
        mock_session = MagicMock()
        mock_session.initialize = MagicMock()
        mock_response = MagicMock()
        mock_response.isError = False
        mock_content = MagicMock()
        mock_content.text = "Echo: test"
        mock_response.content = [mock_content]
        mock_session.call_tool = MagicMock(return_value=mock_response)
        mock_session_class.return_value.__aenter__.return_value = mock_session
        
        result = await self.client.call_tool("echo", {"text": "test"})
        
        self.assertEqual(result, "Echo: test")
        mock_session.call_tool.assert_called_once_with("echo", {"text": "test"})

    @pytest.mark.asyncio
    async def test_call_tool_failure(self):
        """Test failed tool call"""
        with patch('anges.utils.mcp_manager.stdio_client', side_effect=Exception("Connection failed")):
            with self.assertRaises(Exception):
                await self.client.call_tool("echo", {"text": "test"})


class TestMcpManager(unittest.TestCase):
    """Test cases for McpManager functionality"""

    def setUp(self):
        """Set up test environment"""
        # Create test configuration dictionary
        self.test_config = {}

    def test_manager_initialization_empty_config(self):
        """Test MCP manager initialization with empty config"""
        manager = McpManager({})
        self.assertEqual(manager.mcp_config, {})
        self.assertEqual(len(manager.mcp_clients), 0)

    def test_manager_initialization_with_config(self):
        """Test MCP manager initialization with configuration"""
        config = {
            "dummy_mcp_server": {
                "command": sys.executable,
                "args": ["tests/unit/utils/dummy_mcp_server.py"]
            }
        }
        
        manager = McpManager(config)
        
        self.assertEqual(len(manager.mcp_clients), 1)
        self.assertIn("dummy_mcp_server", manager.mcp_clients)
        
        client = manager.mcp_clients["dummy_mcp_server"]
        self.assertEqual(client.name, "dummy_mcp_server")
        self.assertEqual(client.command, sys.executable)

    def test_load_mcp_clients_with_config(self):
        """Test loading MCP clients from config"""
        config = {
            "dummy_mcp_server": {
                "command": sys.executable,
                "args": ["tests/unit/utils/dummy_mcp_server.py"]
            },
            "filesystem_server": {
                "command": "npx",
                "args": ["-g", "@modelcontextprotocol/server-filesystem", "/tmp"]
            }
        }
        
        manager = McpManager(config)
        
        self.assertEqual(len(manager.mcp_clients), 2)
        self.assertIn("dummy_mcp_server", manager.mcp_clients)
        self.assertIn("filesystem_server", manager.mcp_clients)
        
        # Check client properties
        dummy_client = manager.mcp_clients["dummy_mcp_server"]
        self.assertEqual(dummy_client.name, "dummy_mcp_server")
        self.assertEqual(dummy_client.command, sys.executable)

    def test_load_mcp_clients_invalid_config(self):
        """Test loading MCP clients with invalid configuration"""
        config = {
            "invalid_server": {
                "command": "python"
                # Missing 'args' field
            }
        }
        
        # Should not raise exception, but log warning
        manager = McpManager(config)
        self.assertEqual(len(manager.mcp_clients), 0)

    def test_add_mcp_client(self):
        """Test adding new MCP client"""
        manager = McpManager({})
        
        manager.add_mcp_client("new_server", sys.executable, ["tests/unit/utils/dummy_mcp_server.py"])
        
        self.assertIn("new_server", manager.mcp_clients)
        client = manager.mcp_clients["new_server"]
        self.assertEqual(client.name, "new_server")
        self.assertEqual(client.command, sys.executable)

    def test_remove_mcp_client(self):
        """Test removing MCP client"""
        config = {
            "dummy_mcp_server": {
                "command": sys.executable,
                "args": ["tests/unit/utils/dummy_mcp_server.py"]
            }
        }
        manager = McpManager(config)
        
        result = manager.remove_mcp_client("dummy_mcp_server")
        
        self.assertTrue(result)
        self.assertNotIn("dummy_mcp_server", manager.mcp_clients)

    def test_remove_nonexistent_client(self):
        """Test removing nonexistent MCP client"""
        manager = McpManager({})
        
        result = manager.remove_mcp_client("nonexistent")
        
        self.assertFalse(result)

    def test_update_mcp_client(self):
        """Test updating existing MCP client"""
        config = {
            "dummy_mcp_server": {
                "command": "old_command",
                "args": ["old_args"]
            }
        }
        manager = McpManager(config)
        
        result = manager.update_mcp_client("dummy_mcp_server", sys.executable, ["new_args"])
        
        self.assertTrue(result)
        client = manager.mcp_clients["dummy_mcp_server"]
        self.assertEqual(client.command, sys.executable)
        self.assertEqual(client.args, ["new_args"])

    def test_update_nonexistent_client(self):
        """Test updating nonexistent MCP client"""
        manager = McpManager({})
        
        result = manager.update_mcp_client("nonexistent", "command", ["args"])
        
        self.assertFalse(result)

    def test_get_mcp_client(self):
        """Test getting MCP client by name"""
        config = {
            "dummy_mcp_server": {
                "command": sys.executable,
                "args": ["tests/unit/utils/dummy_mcp_server.py"]
            }
        }
        manager = McpManager(config)
        
        client = manager.get_mcp_client("dummy_mcp_server")
        self.assertIsNotNone(client)
        self.assertEqual(client.name, "dummy_mcp_server")
        
        # Test nonexistent client
        nonexistent_client = manager.get_mcp_client("nonexistent")
        self.assertIsNone(nonexistent_client)

    @patch.object(McpManager, 'list_client_tools')
    def test_list_mcp_clients(self, mock_list_tools):
        """Test listing MCP clients with status"""
        config = {
            "connected_server": {
                "command": sys.executable,
                "args": ["tests/unit/utils/dummy_mcp_server.py"]
            },
            "disconnected_server": {
                "command": "invalid_command",
                "args": ["invalid_args"]
            }
        }
        manager = McpManager(config)
        
        # Mock list_client_tools behavior
        def mock_tools_side_effect(name):
            if name == "connected_server":
                return [MagicMock(name="echo")]
            else:
                raise Exception("Connection failed")
        
        mock_list_tools.side_effect = mock_tools_side_effect
        
        clients = manager.list_mcp_clients()
        
        self.assertEqual(len(clients), 2)
        
        # Find clients in results
        connected_info = next(c for c in clients if c["name"] == "connected_server")
        disconnected_info = next(c for c in clients if c["name"] == "disconnected_server")
        
        # Check connected client
        self.assertTrue(connected_info["status"])
        self.assertEqual(len(connected_info["tools"]), 1)
        
        # Check disconnected client
        self.assertFalse(disconnected_info["status"])
        self.assertEqual(len(disconnected_info["tools"]), 0)

    @patch('asyncio.run')
    def test_call_mcp_tool(self, mock_asyncio_run):
        """Test calling MCP tool"""
        config = {
            "dummy_mcp_server": {
                "command": sys.executable,
                "args": ["tests/unit/utils/dummy_mcp_server.py"]
            }
        }
        manager = McpManager(config)
        
        mock_asyncio_run.return_value = "Echo: test"
        
        result = manager.call_mcp_tool("dummy_mcp_server", "echo", {"text": "test"})
        
        self.assertEqual(result, "Echo: test")
        mock_asyncio_run.assert_called_once()

    def test_call_mcp_tool_nonexistent_client(self):
        """Test calling tool on nonexistent MCP client"""
        manager = McpManager({})
        
        with self.assertRaises(ValueError) as context:
            manager.call_mcp_tool("nonexistent", "echo", {"text": "test"})
        
        self.assertIn("MCP client 'nonexistent' not found", str(context.exception))

    @patch('asyncio.run')
    def test_list_client_tools(self, mock_asyncio_run):
        """Test listing tools for a specific client"""
        config = {
            "dummy_mcp_server": {
                "command": sys.executable,
                "args": ["tests/unit/utils/dummy_mcp_server.py"]
            }
        }
        manager = McpManager(config)
        
        mock_tools = [MagicMock(name="echo"), MagicMock(name="add_numbers")]
        mock_asyncio_run.return_value = mock_tools
        
        tools = manager.list_client_tools("dummy_mcp_server")
        
        self.assertEqual(len(tools), 2)
        mock_asyncio_run.assert_called_once()

    def test_list_client_tools_nonexistent_client(self):
        """Test listing tools for nonexistent client"""
        manager = McpManager({})
        
        with self.assertRaises(ValueError) as context:
            manager.list_client_tools("nonexistent")
        
        self.assertIn("MCP client 'nonexistent' not found", str(context.exception))


if __name__ == '__main__':
    pytest.main([__file__])