"""SSE transport layer for MCP."""

import json
from typing import Dict, Any, AsyncIterator
from aiohttp import web
from aiohttp_sse import EventSourceResponse
import structlog

logger = structlog.get_logger()


class SSETransport:
    """Handle SSE transport for MCP messages."""
    
    def __init__(self):
        """Initialize SSE transport."""
        self.connections: Dict[str, EventSourceResponse] = {}
    
    async def send_message(
        self,
        response: EventSourceResponse,
        message: Dict[str, Any]
    ):
        """Send a message via SSE."""
        try:
            data = json.dumps(message)
            await response.send(data)
            logger.debug("Sent SSE message", type=message.get('type'))
        except Exception as e:
            logger.error("Failed to send SSE message", error=str(e))
            raise
    
    async def receive_messages(
        self,
        request: web.Request
    ) -> AsyncIterator[Dict[str, Any]]:
        """Receive messages from SSE connection."""
        # SSE is typically one-way (server to client)
        # For bidirectional communication, we might need to:
        # 1. Use a separate POST endpoint for client messages
        # 2. Or use WebSocket instead of SSE
        # 3. Or use long-polling with message queue
        
        # For now, this is a placeholder
        # Real implementation would depend on MCP specification
        yield {}