#!/usr/bin/env python3
"""Null-Lang Language Server Protocol (LSP) implementation."""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, List, Optional

from .document_state import DocumentState
from .diagnostics import DiagnosticsCollector
from .completion import CompletionProvider

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

document_states: Dict[str, DocumentState] = {}
request_id_counter = 0


class SimpleJSONRPCServer:
    """Simple JSON-RPC 2.0 server for LSP."""
    
    def __init__(self):
        self.handlers: Dict[str, Any] = {}
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup request handlers."""
        self.handlers = {
            'initialize': self._handle_initialize,
            'initialized': self._handle_initialized,
            'textDocument/didOpen': self._handle_did_open,
            'textDocument/didChange': self._handle_did_change,
            'textDocument/didClose': self._handle_did_close,
            'textDocument/completion': self._handle_completion,
            'textDocument/hover': self._handle_hover,
            'shutdown': self._handle_shutdown,
            'exit': self._handle_exit,
        }
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        logger.info("LSP client initialized")
        return {
            'capabilities': {
                'textDocumentSync': 1,  # Full document sync
                'completionProvider': {
                    'triggerCharacters': ['.']
                },
                'hoverProvider': True,
            },
            'serverInfo': {
                'name': 'null-lsp',
                'version': '0.1.0',
            }
        }
    
    async def _handle_initialized(self, params: Dict[str, Any]) -> None:
        """Handle initialized notification."""
        logger.info("LSP initialization complete")
    
    async def _handle_did_open(self, params: Dict[str, Any]) -> None:
        """Handle textDocument/didOpen."""
        uri = params['textDocument']['uri']
        text = params['textDocument']['text']
        
        logger.debug(f"Opening document: {uri}")
        
        doc_state = DocumentState(uri=uri, text=text)
        doc_state.update(text)
        document_states[uri] = doc_state
        
        await self._publish_diagnostics(uri, doc_state.diagnostics)
    
    async def _handle_did_change(self, params: Dict[str, Any]) -> None:
        """Handle textDocument/didChange."""
        uri = params['textDocument']['uri']
        
        logger.debug(f"Changing document: {uri}")
        
        if uri not in document_states:
            document_states[uri] = DocumentState(uri=uri, text="")
        
        doc_state = document_states[uri]
        
        for change in params['contentChanges']:
            if 'text' in change:
                doc_state.update(change['text'])
        
        await self._publish_diagnostics(uri, doc_state.diagnostics)
    
    async def _handle_did_close(self, params: Dict[str, Any]) -> None:
        """Handle textDocument/didClose."""
        uri = params['textDocument']['uri']
        
        logger.debug(f"Closing document: {uri}")
        
        if uri in document_states:
            del document_states[uri]
    
    async def _handle_completion(self, params: Dict[str, Any]) -> List[Dict]:
        """Handle textDocument/completion."""
        uri = params['textDocument']['uri']
        position = params['position']
        
        logger.debug(f"Completion request for {uri}")
        
        if uri not in document_states:
            return []
        
        doc_state = document_states[uri]
        completions = CompletionProvider.get_completions(
            doc_state,
            position['line'],
            position['character']
        )
        
        return completions
    
    async def _handle_hover(self, params: Dict[str, Any]) -> Optional[Dict]:
        """Handle textDocument/hover."""
        uri = params['textDocument']['uri']
        position = params['position']
        
        logger.debug(f"Hover request for {uri}")
        
        if uri not in document_states:
            return None
        
        doc_state = document_states[uri]
        hover_info = doc_state.get_hover_info(position['line'], position['character'])
        
        if hover_info:
            return {'contents': hover_info}
        
        return None
    
    async def _handle_shutdown(self, params: Dict[str, Any]) -> None:
        """Handle shutdown request."""
        logger.info("Shutting down LSP server")
        return None
    
    async def _handle_exit(self, params: Dict[str, Any]) -> None:
        """Handle exit notification."""
        logger.info("LSP server exiting")
        sys.exit(0)
    
    async def _publish_diagnostics(self, uri: str, diagnostics: List[Dict]) -> None:
        """Publish diagnostics to client."""
        notification = {
            'jsonrpc': '2.0',
            'method': 'textDocument/publishDiagnostics',
            'params': {
                'uri': uri,
                'diagnostics': diagnostics,
            }
        }
        self._send_notification(notification)
    
    def _send_notification(self, notification: Dict[str, Any]) -> None:
        """Send notification to client."""
        json_str = json.dumps(notification)
        content_length = len(json_str.encode('utf-8'))
        
        output = f"Content-Length: {content_length}\r\n\r\n{json_str}"
        sys.stdout.write(output)
        sys.stdout.flush()
        logger.debug(f"Sent notification: {notification.get('method')}")
    
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming JSON-RPC message."""
        method = message.get('method')
        params = message.get('params', {})
        msg_id = message.get('id')
        
        logger.debug(f"Received message: {method}")
        
        if method in self.handlers:
            handler = self.handlers[method]
            try:
                result = await handler(params)
                
                if msg_id is not None:
                    response = {
                        'jsonrpc': '2.0',
                        'id': msg_id,
                        'result': result,
                    }
                    self._send_response(response)
            except Exception as e:
                logger.exception(f"Error handling {method}: {e}")
                if msg_id is not None:
                    error_response = {
                        'jsonrpc': '2.0',
                        'id': msg_id,
                        'error': {
                            'code': -32603,
                            'message': str(e),
                        }
                    }
                    self._send_response(error_response)
        else:
            logger.warning(f"Unknown method: {method}")
    
    def _send_response(self, response: Dict[str, Any]) -> None:
        """Send response to client."""
        json_str = json.dumps(response)
        content_length = len(json_str.encode('utf-8'))
        
        output = f"Content-Length: {content_length}\r\n\r\n{json_str}"
        sys.stdout.write(output)
        sys.stdout.flush()
        logger.debug(f"Sent response for id {response.get('id')}")


async def read_messages(server: SimpleJSONRPCServer):
    """Read messages from stdin using LSP protocol."""
    loop = asyncio.get_event_loop()
    
    while True:
        try:
            header = await loop.run_in_executor(None, sys.stdin.readline)
            if not header:
                logger.info("EOF reached")
                break
            
            if not header.startswith('Content-Length:'):
                logger.warning(f"Invalid header: {header}")
                continue
            
            content_length = int(header.split(':')[1].strip())
            
            sys.stdin.readline()
            
            message_bytes = await loop.run_in_executor(
                None,
                lambda: sys.stdin.read(content_length)
            )
            
            message = json.loads(message_bytes)
            await server.handle_message(message)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
        except Exception as e:
            logger.exception(f"Error reading message: {e}")


async def main():
    """Start the language server."""
    logger.info("Starting Null-Lang LSP server...")
    
    server = SimpleJSONRPCServer()
    
    try:
        await read_messages(server)
    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")


if __name__ == '__main__':
    asyncio.run(main())
