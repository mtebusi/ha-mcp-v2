"""MCP Protocol handler."""

import json
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()


class MCPProtocolHandler:
    """Handle MCP protocol messages."""
    
    def __init__(self):
        """Initialize protocol handler."""
        self.message_handlers = {
            'tool_call': self.handle_tool_call,
            'list_tools': self.handle_list_tools,
            'ping': self.handle_ping,
        }
    
    async def handle_message(
        self,
        message: Dict[str, Any],
        tool_registry,
        connection_info: Dict
    ) -> Dict[str, Any]:
        """Handle incoming MCP message."""
        msg_type = message.get('type')
        
        if not msg_type:
            return {
                'type': 'error',
                'error': 'Missing message type'
            }
        
        handler = self.message_handlers.get(msg_type)
        if not handler:
            return {
                'type': 'error',
                'error': f'Unknown message type: {msg_type}'
            }
        
        try:
            return await handler(message, tool_registry, connection_info)
        except Exception as e:
            logger.error("Error handling message", type=msg_type, error=str(e))
            return {
                'type': 'error',
                'error': str(e)
            }
    
    async def handle_tool_call(
        self,
        message: Dict[str, Any],
        tool_registry,
        connection_info: Dict
    ) -> Dict[str, Any]:
        """Handle tool call request."""
        if not connection_info.get('authenticated'):
            return {
                'type': 'error',
                'error': 'Not authenticated'
            }
        
        tool_name = message.get('tool')
        params = message.get('params', {})
        
        if not tool_name:
            return {
                'type': 'error',
                'error': 'Missing tool name'
            }
        
        # Execute tool
        result = await tool_registry.execute_tool(tool_name, params)
        
        if result.get('error'):
            return {
                'type': 'tool_result',
                'tool': tool_name,
                'error': result['error']
            }
        
        return {
            'type': 'tool_result',
            'tool': tool_name,
            'result': result.get('result')
        }
    
    async def handle_list_tools(
        self,
        message: Dict[str, Any],
        tool_registry,
        connection_info: Dict
    ) -> Dict[str, Any]:
        """Handle list tools request."""
        if not connection_info.get('authenticated'):
            return {
                'type': 'error',
                'error': 'Not authenticated'
            }
        
        return {
            'type': 'tools',
            'tools': tool_registry.get_tool_schemas()
        }
    
    async def handle_ping(
        self,
        message: Dict[str, Any],
        tool_registry,
        connection_info: Dict
    ) -> Dict[str, Any]:
        """Handle ping message."""
        return {'type': 'pong'}