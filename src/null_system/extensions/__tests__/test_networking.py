"""Tests for networking extension."""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from networking import (
    RPCMessage,
    RPCServer,
    RPCClient,
    NetworkingManager,
    DistributedNullVM,
    MessageType,
    ExecutionStatus,
    ExecutionRequest,
    ExecutionResponse,
    TLSConfig
)


class TestRPCMessage:
    """Test RPC message structure."""
    
    def test_message_creation(self):
        """Test creating RPC messages."""
        message = RPCMessage(
            message_type=MessageType.EXECUTE_REQUEST,
            message_id="test-123",
            source_id="client-1",
            payload={"test": "data"}
        )
        
        assert message.message_type == MessageType.EXECUTE_REQUEST
        assert message.message_id == "test-123"
        assert message.source_id == "client-1"
        assert message.payload["test"] == "data"
    
    def test_serialization(self):
        """Test JSON serialization."""
        message = RPCMessage(
            message_type=MessageType.EXECUTE_RESPONSE,
            message_id="test-456",
            source_id="server",
            target_id="client",
            payload={"result": "success"}
        )
        
        json_str = message.to_json()
        assert isinstance(json_str, str)
        
        restored = RPCMessage.from_json(json_str)
        assert restored.message_type == message.message_type
        assert restored.message_id == message.message_id
        assert restored.payload == message.payload
    
    def test_timestamp_default(self):
        """Test timestamp initialization."""
        message = RPCMessage(
            message_type=MessageType.HEARTBEAT,
            message_id="test",
            source_id="test"
        )
        
        assert message.timestamp is not None
        assert isinstance(message.timestamp, float)


class TestExecutionRequest:
    """Test execution request structure."""
    
    def test_request_creation(self):
        """Test creating execution requests."""
        request = ExecutionRequest(
            program_source="print hello",
            program_id="prog-123",
            input_data={"x": 1},
            timeout=10.0
        )
        
        assert request.program_source == "print hello"
        assert request.program_id == "prog-123"
        assert request.input_data["x"] == 1
        assert request.timeout == 10.0
    
    def test_default_values(self):
        """Test default request values."""
        request = ExecutionRequest(
            program_source="print hello",
            program_id="prog-123"
        )
        
        assert request.timeout == 30.0
        assert request.optimization_level == 1


class TestExecutionResponse:
    """Test execution response structure."""
    
    def test_response_creation(self):
        """Test creating execution responses."""
        response = ExecutionResponse(
            program_id="prog-123",
            status=ExecutionStatus.SUCCESS,
            output=["Hello, World!"],
            final_state={"result": 42},
            execution_time=0.5
        )
        
        assert response.program_id == "prog-123"
        assert response.status == ExecutionStatus.SUCCESS
        assert response.output == ["Hello, World!"]
        assert response.final_state["result"] == 42
        assert response.execution_time == 0.5
    
    def test_default_values(self):
        """Test default response values."""
        response = ExecutionResponse(
            program_id="prog-123",
            status=ExecutionStatus.SUCCESS
        )
        
        assert response.output == []
        assert response.final_state == {}
        assert response.execution_time == 0.0


class TestTLSConfig:
    """Test TLS configuration."""
    
    def test_tls_creation(self):
        """Test TLS config creation."""
        config = TLSConfig(
            enabled=True,
            cert_path=Path("cert.pem"),
            key_path=Path("key.pem")
        )
        
        assert config.enabled == True
        assert config.cert_path == Path("cert.pem")
        assert config.key_path == Path("key.pem")
    
    def test_ssl_context_creation(self):
        """Test SSL context creation."""
        config = TLSConfig(enabled=True)
        
        # This should not raise an exception
        ssl_context = config.create_ssl_context()
        assert ssl_context is not None
        assert isinstance(ssl_context, type(ssl.create_default_context()))
    
    def test_ssl_context_disabled(self):
        """Test SSL context when disabled."""
        config = TLSConfig(enabled=False)
        ssl_context = config.create_ssl_context()
        assert ssl_context is None


class TestNetworkingManager:
    """Test NetworkingManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = NetworkingManager()
    
    def test_initialization(self):
        """Test manager initialization."""
        assert len(self.manager.servers) == 0
        assert len(self.manager.clients) == 0
        assert self.manager.node_id is not None
    
    @pytest.mark.asyncio
    async def test_start_server(self):
        """Test starting a server."""
        with patch('asyncio.start_server') as mock_start:
            mock_server = AsyncMock()
            mock_start.return_value = mock_server
            
            success = await self.manager.start_server("test-server", "localhost", 8080)
            
            assert success == True
            assert "test-server" in self.manager.servers
            mock_start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_server(self):
        """Test stopping a server."""
        # Mock a running server
        server = AsyncMock()
        server.running = False
        self.manager.servers["test-server"] = server
        
        success = await self.manager.stop_server("test-server")
        
        assert success == True
        server.stop.assert_called_once()
        assert "test-server" not in self.manager.servers
    
    @pytest.mark.asyncio
    async def test_connect_to_server(self):
        """Test connecting to remote server."""
        with patch('asyncio.open_connection') as mock_connect:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_connect.return_value = (mock_reader, mock_writer)
            
            success = await self.manager.connect_to_server("remote", "localhost", 8080)
            
            assert success == True
            assert "remote" in self.manager.clients
    
    @pytest.mark.asyncio
    async def test_disconnect_from_server(self):
        """Test disconnecting from server."""
        # Mock a connected client
        client = AsyncMock()
        client.connected = True
        self.manager.clients["remote"] = client
        
        success = await self.manager.disconnect_from_server("remote")
        
        assert success == True
        client.disconnect.assert_called_once()
        assert "remote" not in self.manager.clients
    
    def test_get_connected_servers(self):
        """Test getting connected servers list."""
        # Add some mock clients
        self.manager.clients["server1"] = AsyncMock()
        self.manager.clients["server2"] = AsyncMock()
        
        servers = self.manager.get_connected_servers()
        assert "server1" in servers
        assert "server2" in servers
        assert len(servers) == 2


class TestDistributedNullVM:
    """Test DistributedNullVM class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.vm = DistributedNullVM()
    
    def test_initialization(self):
        """Test VM initialization."""
        assert len(self.vm.remote_nodes) == 0
        assert len(self.vm.workload_history) == 0
        assert self.vm.local_vm_id is not None
        assert self.vm.load_balancing_strategy == "round_robin"
    
    def test_register_remote_node(self):
        """Test registering remote nodes."""
        capabilities = {"languages": ["null-lang"], "version": "1.0"}
        
        self.vm.register_remote_node("node-1", capabilities)
        
        assert "node-1" in self.vm.remote_nodes
        assert self.vm.remote_nodes["node-1"]["capabilities"] == capabilities
        assert "last_heartbeat" in self.vm.remote_nodes["node-1"]
    
    def test_set_load_balancing_strategy(self):
        """Test setting load balancing strategies."""
        # Valid strategies
        assert self.vm.set_load_balancing_strategy("least_loaded") == True
        assert self.vm.load_balancing_strategy == "least_loaded"
        
        assert self.vm.set_load_balancing_strategy("random") == True
        assert self.vm.load_balancing_strategy == "random"
        
        # Invalid strategy
        assert self.vm.set_load_balancing_strategy("invalid") == False
    
    def test_round_robin_selection(self):
        """Test round-robin node selection."""
        # Add some nodes
        self.vm.register_remote_node("node1", {})
        self.vm.register_remote_node("node2", {})
        self.vm.register_remote_node("node3", {})
        
        # Test round-robin selection
        selected1 = self.vm._select_nodes(1)
        selected2 = self.vm._select_nodes(1)
        selected3 = self.vm._select_nodes(1)
        selected4 = self.vm._select_nodes(1)  # Should cycle back
        
        assert len(selected1) == 1
        assert selected1[0] in ["node1", "node2", "node3"]
        assert selected2[0] in ["node1", "node2", "node3"]
        assert selected3[0] in ["node1", "node2", "node3"]
        assert selected4[0] in ["node1", "node2", "node3"]
    
    def test_least_loaded_selection(self):
        """Test least-loaded node selection."""
        self.vm.load_balancing_strategy = "least_loaded"
        
        # Add nodes with different loads
        self.vm.remote_nodes["node1"] = {"load": 0.8, "task_count": 5}
        self.vm.remote_nodes["node2"] = {"load": 0.2, "task_count": 1}
        self.vm.remote_nodes["node3"] = {"load": 0.5, "task_count": 3}
        
        selected = self.vm._select_nodes(2)
        
        assert len(selected) == 2
        assert "node2" in selected  # Lowest load
        assert selected[0] == "node2"  # Should be first
    
    def test_get_node_status(self):
        """Test getting node status."""
        capabilities = {"version": "1.0"}
        self.vm.register_remote_node("node1", capabilities)
        
        # Mock a connection to this node
        self.vm.networking_manager.clients["node1"] = AsyncMock()
        
        status = self.vm.get_node_status()
        
        assert "node1" in status
        assert status["node1"]["capabilities"] == capabilities
        assert status["node1"]["reachable"] == True
    
    def test_record_workload(self):
        """Test recording workload execution."""
        response = ExecutionResponse(
            program_id="prog-123",
            status=ExecutionStatus.SUCCESS,
            execution_time=0.5
        )
        
        self.vm._record_workload("node1", response)
        
        assert len(self.vm.workload_history) == 1
        history_item = self.vm.workload_history[0]
        assert history_item["node_id"] == "node1"
        assert history_item["program_id"] == "prog-123"
        assert history_item["execution_time"] == 0.5


@pytest.mark.asyncio
class TestRPCServer:
    """Test RPC server functionality."""
    
    async def test_server_initialization(self):
        """Test server initialization."""
        server = RPCServer("localhost", 8080)
        
        assert server.host == "localhost"
        assert server.port == 8080
        assert len(server.message_handlers) > 0
    
    async def test_handle_execute_request(self):
        """Test handling execution requests."""
        server = RPCServer("localhost", 8080)
        
        # Create a test message
        request_data = {
            "program_source": "print hello",
            "program_id": "test-prog",
            "timeout": 30.0
        }
        
        message = RPCMessage(
            message_type=MessageType.EXECUTE_REQUEST,
            message_id="test-123",
            source_id="client-1",
            payload=request_data
        )
        
        # Mock writer
        writer = AsyncMock()
        server.clients["client-1"] = writer
        
        await server._handle_execute_request("client-1", message)
        
        # Should send a response
        writer.write.assert_called()
        written_data = writer.write.call_args[0][0]
        response_message = RPCMessage.from_json(written_data.decode())
        
        assert response_message.message_type == MessageType.EXECUTE_RESPONSE
        assert "program_id" in response_message.payload
    
    async def test_handle_state_request(self):
        """Test handling state requests."""
        server = RPCServer("localhost", 8080)
        
        message = RPCMessage(
            message_type=MessageType.STATE_REQUEST,
            message_id="test-123",
            source_id="client-1"
        )
        
        writer = AsyncMock()
        server.clients["client-1"] = writer
        
        await server._handle_state_request("client-1", message)
        
        # Should send server state
        written_data = writer.write.call_args[0][0]
        response_message = RPCMessage.from_json(written_data.decode())
        
        assert response_message.message_type == MessageType.STATE_RESPONSE
        assert "available" in response_message.payload


@pytest.mark.asyncio
class TestRPCClient:
    """Test RPC client functionality."""
    
    async def test_client_initialization(self):
        """Test client initialization."""
        client = RPCClient()
        
        assert client.connected == False
        assert client.client_id is not None
    
    async def test_connect(self):
        """Test connecting to server."""
        client = RPCClient()
        
        with patch('asyncio.open_connection') as mock_connect:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_connect.return_value = (mock_reader, mock_writer)
            
            success = await client.connect("localhost", 8080)
            
            assert success == True
            assert client.connected == True
            assert client.reader == mock_reader
            assert client.writer == mock_writer
    
    async def test_execute_program(self):
        """Test executing program remotely."""
        client = RPCClient()
        
        # Mock connection
        client.reader = AsyncMock()
        client.writer = AsyncMock()
        client.connected = True
        
        # Mock response
        response_data = {
            "program_id": "test-prog",
            "status": "success",
            "output": ["Hello!"],
            "execution_time": 0.1
        }
        
        response_message = RPCMessage(
            message_type=MessageType.EXECUTE_RESPONSE,
            message_id="response-123",
            source_id="server",
            payload=response_data
        )
        
        client.reader.read.return_value = response_message.to_json().encode()
        
        result = await client.execute_program("print hello")
        
        assert result is not None
        assert result.status == ExecutionStatus.SUCCESS
        assert result.output == ["Hello!"]
        assert result.execution_time == 0.1


class TestIntegration:
    """Integration tests for networking system."""
    
    @pytest.mark.asyncio
    async def test_client_server_workflow(self):
        """Test complete client-server workflow."""
        # This would test a full client-server interaction
        # In a real implementation, this would involve actual network I/O
        
        client = RPCClient()
        server = RPCServer("localhost", 8080)
        
        # Test message creation and serialization
        message = RPCMessage(
            message_type=MessageType.HEARTBEAT,
            message_id="test-123",
            source_id="client",
            target_id="server"
        )
        
        json_str = message.to_json()
        restored = RPCMessage.from_json(json_str)
        
        assert restored.message_type == MessageType.HEARTBEAT
        assert restored.message_id == "test-123"
        assert restored.source_id == "client"
    
    @pytest.mark.asyncio
    async def test_distributed_execution_flow(self):
        """Test distributed execution workflow."""
        vm = DistributedNullVM()
        
        # Register some nodes
        vm.register_remote_node("node1", {"load": 0.5})
        vm.register_remote_node("node2", {"load": 0.8})
        vm.register_remote_node("node3", {"load": 0.2})
        
        # Set load balancing to least loaded
        vm.set_load_balancing_strategy("least_loaded")
        
        # Test node selection
        selected_nodes = vm._select_nodes(2)
        assert len(selected_nodes) == 2
        assert "node3" in selected_nodes  # Least loaded node
        
        # Test workload recording
        response = ExecutionResponse(
            program_id="test-prog",
            status=ExecutionStatus.SUCCESS,
            execution_time=0.3
        )
        
        vm._record_workload("node3", response)
        assert len(vm.workload_history) == 1
        assert vm.workload_history[0]["node_id"] == "node3"