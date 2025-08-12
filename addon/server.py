"""Main MCP SSE Server for HomeAssistant integration."""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, Optional
import argparse

from aiohttp import web
from aiohttp_sse import sse_response
import structlog

from constants import (
    VERSION, DEFAULT_PORT, DEFAULT_HOST, SSE_ENDPOINT,
    MAX_CONNECTIONS, CONNECTION_TIMEOUT, KEEPALIVE_INTERVAL
)
from auth import AuthHandler
from config import Config
from mcp.protocol import MCPProtocolHandler
from mcp.registry import ToolRegistry
from ha_api.rest import HARestClient
from ha_api.websocket import HAWebSocketClient

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class MCPServer:
    """HomeAssistant MCP Server implementation."""
    
    def __init__(self, config: Config):
        """Initialize the MCP server."""
        self.config = config
        self.app = web.Application()
        self.connections: Dict[str, Any] = {}
        self.auth_handler = AuthHandler(config)
        self.protocol_handler = MCPProtocolHandler()
        self.tool_registry = ToolRegistry()
        self.ha_rest_client: Optional[HARestClient] = None
        self.ha_ws_client: Optional[HAWebSocketClient] = None
        
        # Setup routes
        self.setup_routes()
        
        # Initialize HomeAssistant clients
        self.setup_ha_clients()
        
        # Register tools
        self.register_tools()
        
        logger.info("MCP Server initialized", version=VERSION)
    
    def setup_routes(self):
        """Setup server routes."""
        self.app.router.add_get(SSE_ENDPOINT, self.handle_sse)
        self.app.router.add_get('/health', self.handle_health)
        self.app.router.add_get('/auth/callback', self.handle_auth_callback)
    
    def setup_ha_clients(self):
        """Initialize HomeAssistant API clients."""
        if self.config.supervisor_token:
            # Running as add-on with supervisor token
            ha_url = "http://supervisor/core"
            token = self.config.supervisor_token
        else:
            # Running standalone
            ha_url = self.config.ha_url
            token = self.config.ha_token
        
        if ha_url and token:
            self.ha_rest_client = HARestClient(ha_url, token)
            self.ha_ws_client = HAWebSocketClient(ha_url, token)
            logger.info("HomeAssistant clients initialized", ha_url=ha_url)
    
    def register_tools(self):
        """Register all available MCP tools."""
        from tools.core import register_core_tools
        
        # Register core tools with branched operations
        register_core_tools(self.tool_registry, self.ha_rest_client, self.ha_ws_client)
        
        logger.info("Tools registered", count=len(self.tool_registry.tools))
    
    async def handle_sse(self, request: web.Request) -> web.Response:
        """Handle SSE connection from Claude Desktop."""
        connection_id = request.headers.get('X-Connection-Id', str(id(request)))
        
        # Check connection limit
        if len(self.connections) >= MAX_CONNECTIONS:
            logger.warning("Connection limit reached", current=len(self.connections))
            return web.Response(status=503, text="Connection limit reached")
        
        async with sse_response(request) as response:
            self.connections[connection_id] = {
                'request': request,
                'response': response,
                'authenticated': False
            }
            
            try:
                # Send initial handshake
                await response.send(json.dumps({
                    'type': 'handshake',
                    'version': VERSION,
                    'protocol': 'mcp/1.0',
                    'capabilities': {
                        'tools': True,
                        'resources': False,
                        'prompts': False
                    }
                }))
                
                # Check authentication
                auth_header = request.headers.get('Authorization')
                if not auth_header or not auth_header.startswith('Bearer '):
                    # Send auth required
                    await response.send(json.dumps({
                        'type': 'auth_required',
                        'auth_url': self.auth_handler.get_auth_url(connection_id)
                    }))
                else:
                    # Validate token
                    token = auth_header.split(' ')[1]
                    if await self.auth_handler.validate_token(token):
                        self.connections[connection_id]['authenticated'] = True
                        
                        # Send tool list
                        await response.send(json.dumps({
                            'type': 'tools',
                            'tools': self.tool_registry.get_tool_schemas()
                        }))
                    else:
                        await response.send(json.dumps({
                            'type': 'error',
                            'error': 'Invalid token'
                        }))
                        return response
                
                # Keep connection alive and handle messages
                while not response.task.done():
                    try:
                        # Wait for messages with timeout for keepalive
                        message = await asyncio.wait_for(
                            self._receive_message(request),
                            timeout=KEEPALIVE_INTERVAL
                        )
                        
                        if message:
                            # Process message
                            result = await self.protocol_handler.handle_message(
                                message,
                                self.tool_registry,
                                self.connections[connection_id]
                            )
                            
                            # Send response
                            await response.send(json.dumps(result))
                    except asyncio.TimeoutError:
                        # Send keepalive ping
                        await response.send(json.dumps({'type': 'ping'}))
                    except Exception as e:
                        logger.error("Error processing message", error=str(e))
                        await response.send(json.dumps({
                            'type': 'error',
                            'error': str(e)
                        }))
                
            except Exception as e:
                logger.error("SSE connection error", error=str(e), connection_id=connection_id)
            finally:
                # Clean up connection
                if connection_id in self.connections:
                    del self.connections[connection_id]
                logger.info("Connection closed", connection_id=connection_id)
            
            return response
    
    async def _receive_message(self, request: web.Request) -> Optional[Dict]:
        """Receive message from SSE connection."""
        # This would normally read from the request stream
        # For SSE, messages come through POST to the same endpoint or via EventSource
        # Implementation depends on the exact MCP protocol specification
        return None
    
    async def handle_health(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({
            'status': 'healthy',
            'version': VERSION,
            'connections': len(self.connections)
        })
    
    async def handle_auth_callback(self, request: web.Request) -> web.Response:
        """Handle OAuth2 callback."""
        code = request.query.get('code')
        state = request.query.get('state')
        
        if not code or not state:
            return web.Response(status=400, text="Missing code or state")
        
        # Exchange code for token
        token = await self.auth_handler.exchange_code(code, state)
        
        if token:
            # Return success page with instructions
            return web.Response(
                text=f"Authentication successful! Return to Claude Desktop and your connection will be established.",
                content_type='text/html'
            )
        else:
            return web.Response(status=401, text="Authentication failed")
    
    async def start(self):
        """Start the server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(
            runner,
            self.config.host,
            self.config.port,
            ssl_context=self.config.get_ssl_context()
        )
        
        await site.start()
        logger.info(
            "MCP Server started",
            host=self.config.host,
            port=self.config.port,
            ssl=self.config.ssl
        )
        
        # Keep server running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            await runner.cleanup()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='HomeAssistant MCP Server')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--host', default=DEFAULT_HOST, help='Host to bind to')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Port to bind to')
    parser.add_argument('--ssl', action='store_true', help='Enable SSL')
    parser.add_argument('--certfile', help='SSL certificate file')
    parser.add_argument('--keyfile', help='SSL key file')
    parser.add_argument('--supervisor-token', help='Supervisor token (for add-on mode)')
    parser.add_argument('--ha-url', help='HomeAssistant URL (for standalone mode)')
    parser.add_argument('--ha-token', help='HomeAssistant token (for standalone mode)')
    parser.add_argument('--log-level', default='INFO', help='Log level')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else getattr(logging, args.log_level.upper())
    logging.basicConfig(level=log_level)
    
    # Create config
    config = Config(
        host=args.host,
        port=args.port,
        ssl=args.ssl,
        certfile=args.certfile,
        keyfile=args.keyfile,
        supervisor_token=args.supervisor_token or os.environ.get('SUPERVISOR_TOKEN'),
        ha_url=args.ha_url,
        ha_token=args.ha_token
    )
    
    # Create and start server
    server = MCPServer(config)
    await server.start()


if __name__ == '__main__':
    asyncio.run(main())