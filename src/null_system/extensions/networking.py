from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import ssl
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
import uuid

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """RPC message types."""
    EXECUTE_REQUEST = "execute_request"
    EXECUTE_RESPONSE = "execute_response"
    STATE_REQUEST = "state_request"
    STATE_RESPONSE = "state_response"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class ExecutionStatus(Enum):
    """Execution status codes."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    COMPILATION_ERROR = "compilation_error"
    RUNTIME_ERROR = "runtime_error"


@dataclass
class TLSConfig:
    """TLS configuration for secure communication."""
    enabled: bool = True
    cert_path: Optional[Path] = None
    key_path: Optional[Path] = None
    ca_cert_path: Optional[Path] = None
    verify_mode: str = "CERT_REQUIRED"
    check_hostname: bool = True
    
    def create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context from configuration."""
        if not self.enabled:
            return None
        
        context = ssl.create_default_context()
        
        if self.ca_cert_path:
            context.load_verify_locations(str(self.ca_cert_path))
        
        if self.cert_path and self.key_path:
            context.load_cert_chain(str(self.cert_path), str(self.key_path))
        
        if self.verify_mode == "CERT_NONE":
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        elif self.verify_mode == "CERT_OPTIONAL":
            context.verify_mode = ssl.CERT_OPTIONAL
        else:  # CERT_REQUIRED
            context.verify_mode = ssl.CERT_REQUIRED
        
        return context


@dataclass
class RPCMessage:
    """RPC message structure."""
    message_type: MessageType
    message_id: str
    source_id: str
    target_id: Optional[str] = None
    payload: Dict[str, Any] = None
    timestamp: float = None
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            # Use current time for timestamp to avoid asyncio issues
            import time
            self.timestamp = time.time()
        if self.payload is None:
            self.payload = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RPCMessage':
        """Create from dictionary."""
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RPCMessage':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class ExecutionRequest:
    """Remote execution request."""
    program_source: str
    program_id: str
    input_data: Optional[Dict[str, Any]] = None
    timeout: float = 30.0
    optimization_level: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ExecutionResponse:
    """Remote execution response."""
    program_id: str
    status: ExecutionStatus
    output: List[str] = None
    final_state: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.output is None:
            self.output = []
        if self.final_state is None:
            self.final_state = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionResponse':
        """Create from dictionary."""
        data['status'] = ExecutionStatus(data['status'])
        return cls(**data)


class RPCServer:
    """Simple RPC server for handling remote execution requests."""
    
    def __init__(self, host: str = "localhost", port: int = 8080, tls_config: "TLSConfig | None" = None):
        """Initialize RPC server."""
        self.host = host
        self.port = port
        self.tls_config = tls_config or TLSConfig()
        self.clients: "Dict[str, asyncio.transports.Transport]" = {}
        self.message_handlers: "Dict[MessageType, Callable]" = {}
        self.running = False
        self.server = None
        
        # Register default handlers
        self.message_handlers[MessageType.EXECUTE_REQUEST] = self._handle_execute_request
        self.message_handlers[MessageType.STATE_REQUEST] = self._handle_state_request
        self.message_handlers[MessageType.HEARTBEAT] = self._handle_heartbeat
    
    async def start(self):
        """Start the RPC server."""
        try:
            if self.tls_config.enabled and self.tls_config.create_ssl_context():
                # TLS server
                self.server = await asyncio.start_server(
                    self.handle_client,
                    self.host,
                    self.port,
                    ssl=self.tls_config.create_ssl_context()
                )
            else:
                # Non-TLS server
                self.server = await asyncio.start_server(
                    self.handle_client,
                    self.host,
                    self.port
                )
            
            self.running = True
            logger.info(f"RPC server started on {self.host}:{self.port}")
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise
    
    async def stop(self):
        """Stop the RPC server."""
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        logger.info("RPC server stopped")
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle client connection."""
        client_id = str(uuid.uuid4())
        self.clients[client_id] = writer
        
        try:
            while self.running:
                data = await reader.read(8192)
                if not data:
                    break
                
                try:
                    message = RPCMessage.from_json(data.decode())
                    await self._process_message(client_id, message)
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {e}")
                    error_response = RPCMessage(
                        message_type=MessageType.ERROR,
                        message_id=str(uuid.uuid4()),
                        source_id="server",
                        target_id=client_id,
                        payload={"error": str(e)}
                    )
                    writer.write(error_response.to_json().encode())
                    await writer.drain()
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Client {client_id} error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            self.clients.pop(client_id, None)
    
    async def _process_message(self, client_id: str, message: RPCMessage):
        """Process incoming RPC message."""
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(client_id, message)
            except Exception as e:
                logger.error(f"Handler error: {e}")
                await self._send_error(client_id, str(e))
        else:
            await self._send_error(client_id, f"No handler for message type: {message.message_type}")
    
    async def _handle_execute_request(self, client_id: str, message: RPCMessage):
        """Handle execution request."""
        try:
            request = ExecutionRequest(**message.payload)
            logger.info(f"Executing program {request.program_id} for client {client_id}")
            
            # Simulate program execution
            response = ExecutionResponse(
                program_id=request.program_id,
                status=ExecutionStatus.SUCCESS,
                output=["Program executed successfully"],
                final_state={"result": 42},
                execution_time=0.1
            )
            
            response_message = RPCMessage(
                message_type=MessageType.EXECUTE_RESPONSE,
                message_id=str(uuid.uuid4()),
                source_id="server",
                target_id=client_id,
                payload=response.to_dict()
            )
            
            await self._send_to_client(client_id, response_message)
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            error_response = ExecutionResponse(
                program_id=message.payload.get("program_id", "unknown"),
                status=ExecutionStatus.ERROR,
                error_message=str(e)
            )
            
            response_message = RPCMessage(
                message_type=MessageType.EXECUTE_RESPONSE,
                message_id=str(uuid.uuid4()),
                source_id="server",
                target_id=client_id,
                payload=error_response.to_dict()
            )
            
            await self._send_to_client(client_id, response_message)
    
    async def _handle_state_request(self, client_id: str, message: RPCMessage):
        """Handle state request."""
        # Simulate returning server state
        state_data = {
            "available": True,
            "load": 0.3,
            "supported_languages": ["null-lang"],
            "version": "1.0.0"
        }
        
        response_message = RPCMessage(
            message_type=MessageType.STATE_RESPONSE,
            message_id=str(uuid.uuid4()),
            source_id="server",
            target_id=client_id,
            payload=state_data
        )
        
        await self._send_to_client(client_id, response_message)
    
    async def _handle_heartbeat(self, client_id: str, message: RPCMessage):
        """Handle heartbeat."""
        # Respond with heartbeat
        import time
        response_message = RPCMessage(
            message_type=MessageType.HEARTBEAT,
            message_id=str(uuid.uuid4()),
            source_id="server",
            target_id=client_id,
            payload={"timestamp": time.time()}
        )
        
        await self._send_to_client(client_id, response_message)
    
    async def _send_to_client(self, client_id: str, message: RPCMessage):
        """Send message to specific client."""
        if client_id in self.clients:
            try:
                writer = self.clients[client_id]
                writer.write(message.to_json().encode())
                await writer.drain()
            except Exception as e:
                logger.error(f"Failed to send to client {client_id}: {e}")
                # Remove failed client
                self.clients.pop(client_id, None)
    
    async def _send_error(self, client_id: str, error_message: str):
        """Send error message to client."""
        error_payload = {"error": error_message}
        error_message_obj = RPCMessage(
            message_type=MessageType.ERROR,
            message_id=str(uuid.uuid4()),
            source_id="server",
            target_id=client_id,
            payload=error_payload
        )
        await self._send_to_client(client_id, error_message_obj)


class RPCClient:
    """RPC client for making remote execution requests."""
    
    def __init__(self, tls_config: Optional[TLSConfig] = None):
        """Initialize RPC client."""
        self.tls_config = tls_config or TLSConfig()
        self.reader = None
        self.writer = None
        self.connected = False
        self.client_id = str(uuid.uuid4())
    
    async def connect(self, host: str, port: int) -> bool:
        """Connect to RPC server."""
        try:
            if self.tls_config.enabled and self.tls_config.create_ssl_context():
                reader, writer = await asyncio.open_connection(
                    host, port, ssl=self.tls_config.create_ssl_context()
                )
            else:
                reader, writer = await asyncio.open_connection(host, port)
            
            self.reader = reader
            self.writer = writer
            self.connected = True
            logger.info(f"Connected to {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {host}:{port}: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from server."""
        self.connected = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        logger.info("Disconnected from server")
    
    async def execute_program(self, program_source: str, timeout: float = 30.0) -> Optional[ExecutionResponse]:
        """Execute program on remote server."""
        if not self.connected:
            raise RuntimeError("Not connected to server")
        
        try:
            request = ExecutionRequest(
                program_source=program_source,
                program_id=str(uuid.uuid4()),
                timeout=timeout
            )
            
            message = RPCMessage(
                message_type=MessageType.EXECUTE_REQUEST,
                message_id=str(uuid.uuid4()),
                source_id=self.client_id,
                target_id="server",
                payload=request.to_dict()
            )
            
            # Send request
            self.writer.write(message.to_json().encode())
            await self.writer.drain()
            
            # Wait for response
            data = await asyncio.wait_for(self.reader.read(8192), timeout=timeout)
            response_message = RPCMessage.from_json(data.decode())
            
            if response_message.message_type == MessageType.EXECUTE_RESPONSE:
                return ExecutionResponse.from_dict(response_message.payload)
            else:
                logger.error(f"Unexpected response type: {response_message.message_type}")
                return None
                
        except asyncio.TimeoutError:
            logger.error(f"Execution timeout after {timeout}s")
            return None
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return None
    
    async def get_server_state(self) -> Optional[Dict[str, Any]]:
        """Get server state."""
        if not self.connected:
            raise RuntimeError("Not connected to server")
        
        try:
            message = RPCMessage(
                message_type=MessageType.STATE_REQUEST,
                message_id=str(uuid.uuid4()),
                source_id=self.client_id,
                target_id="server"
            )
            
            self.writer.write(message.to_json().encode())
            await self.writer.drain()
            
            data = await self.reader.read(8192)
            response_message = RPCMessage.from_json(data.decode())
            
            if response_message.message_type == MessageType.STATE_RESPONSE:
                return response_message.payload
            else:
                logger.error(f"Unexpected response type: {response_message.message_type}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get server state: {e}")
            return None


class NetworkingManager:
    """Manages networking operations for distributed execution."""
    
    def __init__(self, tls_config: "TLSConfig | None" = None):
        """Initialize networking manager."""
        self.tls_config = tls_config or TLSConfig()
        self.servers: "Dict[str, RPCServer]" = {}
        self.clients: "Dict[str, RPCClient]" = {}
        self.node_id = str(uuid.uuid4())
    
    async def start_server(self, name: str, host: str = "localhost", port: int = 8080) -> bool:
        """Start a named RPC server."""
        try:
            server = RPCServer(host, port, self.tls_config)
            self.servers[name] = server
            
            # Start server in background
            asyncio.create_task(server.start())
            
            # Wait a bit for server to start
            await asyncio.sleep(0.1)
            
            logger.info(f"Started server '{name}' on {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start server '{name}': {e}")
            return False
    
    async def stop_server(self, name: str) -> bool:
        """Stop a named RPC server."""
        if name in self.servers:
            try:
                await self.servers[name].stop()
                del self.servers[name]
                logger.info(f"Stopped server '{name}'")
                return True
            except Exception as e:
                logger.error(f"Failed to stop server '{name}': {e}")
                return False
        return False
    
    async def connect_to_server(self, name: str, host: str, port: int) -> bool:
        """Connect to remote server."""
        try:
            client = RPCClient(self.tls_config)
            if await client.connect(host, port):
                self.clients[name] = client
                logger.info(f"Connected to server '{name}' at {host}:{port}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to connect to '{name}': {e}")
            return False
    
    async def disconnect_from_server(self, name: str) -> bool:
        """Disconnect from server."""
        if name in self.clients:
            try:
                await self.clients[name].disconnect()
                del self.clients[name]
                logger.info(f"Disconnected from server '{name}'")
                return True
            except Exception as e:
                logger.error(f"Failed to disconnect from '{name}': {e}")
                return False
        return False
    
    async def execute_remote(self, server_name: str, program_source: str, timeout: float = 30.0) -> Optional[ExecutionResponse]:
        """Execute program on remote server."""
        if server_name not in self.clients:
            raise ValueError(f"Server '{server_name}' not connected")
        
        client = self.clients[server_name]
        return await client.execute_program(program_source, timeout)
    
    async def get_server_info(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get information about remote server."""
        if server_name not in self.clients:
            raise ValueError(f"Server '{server_name}' not connected")
        
        client = self.clients[server_name]
        return await client.get_server_state()
    
    def get_connected_servers(self) -> List[str]:
        """Get list of connected server names."""
        return list(self.clients.keys())


class DistributedNullVM:
    """Distributed Null VM capable of delegating workloads to remote nodes."""
    
    def __init__(self, networking_manager: Optional[NetworkingManager] = None):
        """Initialize distributed VM."""
        self.networking_manager = networking_manager or NetworkingManager()
        self.local_vm_id = str(uuid.uuid4())
        self.remote_nodes: Dict[str, Dict[str, Any]] = {}
        self.workload_history: List[Dict[str, Any]] = []
        self.load_balancing_strategy = "round_robin"  # or "least_loaded", "random"
        self.round_robin_index = 0
    
    def register_remote_node(self, node_id: str, capabilities: Dict[str, Any]) -> None:
        """Register a remote node with its capabilities."""
        # Use current time instead of asyncio.get_event_loop() to avoid issues
        import time
        self.remote_nodes[node_id] = {
            "id": node_id,
            "capabilities": capabilities,
            "last_heartbeat": time.time(),
            "load": 0.0,
            "task_count": 0
        }
        logger.info(f"Registered remote node: {node_id}")
    
    async def execute_distributed(self, 
                                program_source: str, 
                                target_nodes: Optional[List[str]] = None) -> Optional[ExecutionResponse]:
        """Execute program in distributed manner."""
        if not target_nodes:
            target_nodes = self._select_nodes()
        
        if not target_nodes:
            logger.warning("No suitable target nodes available")
            return None
        
        # Try each target node until one succeeds
        for node_id in target_nodes:
            if node_id in self.networking_manager.clients:
                try:
                    logger.info(f"Executing on remote node: {node_id}")
                    response = await self.networking_manager.execute_remote(node_id, program_source)
                    if response and response.status == ExecutionStatus.SUCCESS:
                        self._record_workload(node_id, response)
                        return response
                except Exception as e:
                    logger.error(f"Execution failed on node {node_id}: {e}")
        
        return None
    
    def _select_nodes(self, count: int = 1) -> List[str]:
        """Select target nodes using configured strategy."""
        if self.load_balancing_strategy == "round_robin":
            return self._round_robin_selection(count)
        elif self.load_balancing_strategy == "least_loaded":
            return self._least_loaded_selection(count)
        elif self.load_balancing_strategy == "random":
            return self._random_selection(count)
        else:
            return []
    
    def _round_robin_selection(self, count: int) -> List[str]:
        """Round-robin node selection."""
        nodes = list(self.remote_nodes.keys())
        if not nodes:
            return []
        
        selected = []
        for i in range(count):
            selected_node = nodes[self.round_robin_index % len(nodes)]
            selected.append(selected_node)
            self.round_robin_index += 1
        
        return selected
    
    def _least_loaded_selection(self, count: int) -> List[str]:
        """Select least loaded nodes."""
        nodes_by_load = sorted(
            self.remote_nodes.items(),
            key=lambda x: x[1]["load"]
        )
        
        return [node_id for node_id, _ in nodes_by_load[:count]]
    
    def _random_selection(self, count: int) -> List[str]:
        """Random node selection."""
        import random
        nodes = list(self.remote_nodes.keys())
        return random.sample(nodes, min(count, len(nodes)))
    
    def _record_workload(self, node_id: str, response: ExecutionResponse) -> None:
        """Record workload execution."""
        import time
        workload_record = {
            "node_id": node_id,
            "program_id": response.program_id,
            "execution_time": response.execution_time,
            "timestamp": time.time()
        }
        self.workload_history.append(workload_record)
    
    def get_node_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered nodes."""
        return {node_id: {**info, "reachable": node_id in self.networking_manager.clients} 
                for node_id, info in self.remote_nodes.items()}
    
    def set_load_balancing_strategy(self, strategy: str) -> bool:
        """Set load balancing strategy."""
        valid_strategies = ["round_robin", "least_loaded", "random"]
        if strategy in valid_strategies:
            self.load_balancing_strategy = strategy
            logger.info(f"Load balancing strategy set to: {strategy}")
            return True
        return False