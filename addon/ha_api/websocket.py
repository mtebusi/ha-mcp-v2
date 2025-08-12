"""HomeAssistant WebSocket API client."""

import asyncio
import json
from typing import Dict, Any, Optional, Callable, List
import websockets
import structlog

logger = structlog.get_logger()


class HAWebSocketClient:
    """Client for HomeAssistant WebSocket API."""
    
    def __init__(self, base_url: str, token: str):
        """Initialize WebSocket client."""
        # Convert HTTP URL to WebSocket URL
        ws_url = base_url.replace('http://', 'ws://').replace('https://', 'wss://')
        self.url = f"{ws_url}/api/websocket"
        self.token = token
        self.websocket = None
        self.message_id = 1
        self.pending_messages: Dict[int, asyncio.Future] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.running = False
    
    async def connect(self):
        """Connect to HomeAssistant WebSocket."""
        try:
            self.websocket = await websockets.connect(self.url)
            
            # Wait for auth_required message
            auth_msg = await self.websocket.recv()
            auth_data = json.loads(auth_msg)
            
            if auth_data.get('type') == 'auth_required':
                # Send authentication
                await self.send_message({
                    'type': 'auth',
                    'access_token': self.token
                })
                
                # Wait for auth result
                result_msg = await self.websocket.recv()
                result_data = json.loads(result_msg)
                
                if result_data.get('type') == 'auth_ok':
                    logger.info("WebSocket authenticated successfully")
                    self.running = True
                    # Start message handler
                    asyncio.create_task(self._handle_messages())
                    return True
                else:
                    logger.error("WebSocket authentication failed", result=result_data)
                    await self.disconnect()
                    return False
        except Exception as e:
            logger.error("Failed to connect to WebSocket", error=str(e))
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
    
    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message without waiting for response."""
        if not self.websocket:
            raise ConnectionError("WebSocket not connected")
        
        await self.websocket.send(json.dumps(message))
    
    async def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command and wait for response."""
        if not self.websocket:
            raise ConnectionError("WebSocket not connected")
        
        # Add message ID
        msg_id = self.message_id
        self.message_id += 1
        command['id'] = msg_id
        
        # Create future for response
        future = asyncio.Future()
        self.pending_messages[msg_id] = future
        
        # Send command
        await self.websocket.send(json.dumps(command))
        
        # Wait for response
        try:
            result = await asyncio.wait_for(future, timeout=30)
            return result
        except asyncio.TimeoutError:
            del self.pending_messages[msg_id]
            raise TimeoutError(f"Command {command.get('type')} timed out")
    
    async def _handle_messages(self):
        """Handle incoming messages."""
        while self.running and self.websocket:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                # Check if this is a response to a command
                msg_id = data.get('id')
                if msg_id in self.pending_messages:
                    future = self.pending_messages.pop(msg_id)
                    if not future.done():
                        future.set_result(data)
                
                # Handle events
                if data.get('type') == 'event':
                    await self._handle_event(data.get('event'))
                
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                self.running = False
                # Attempt reconnection
                asyncio.create_task(self._reconnect())
            except Exception as e:
                logger.error("Error handling WebSocket message", error=str(e))
    
    async def _handle_event(self, event: Dict[str, Any]):
        """Handle an event from HomeAssistant."""
        event_type = event.get('event_type')
        handlers = self.event_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error("Error in event handler", event_type=event_type, error=str(e))
    
    async def _reconnect(self):
        """Attempt to reconnect to WebSocket."""
        for attempt in range(5):
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            logger.info("Attempting WebSocket reconnection", attempt=attempt + 1)
            if await self.connect():
                logger.info("WebSocket reconnected successfully")
                # Re-subscribe to events
                await self._resubscribe_events()
                return
        
        logger.error("Failed to reconnect to WebSocket after 5 attempts")
    
    async def _resubscribe_events(self):
        """Re-subscribe to events after reconnection."""
        for event_type in self.event_handlers.keys():
            await self.subscribe_event(event_type)
    
    def on_event(self, event_type: str, handler: Callable):
        """Register an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def subscribe_event(self, event_type: Optional[str] = None) -> Dict[str, Any]:
        """Subscribe to events."""
        command = {'type': 'subscribe_events'}
        if event_type:
            command['event_type'] = event_type
        
        return await self.send_command(command)
    
    async def get_states(self) -> List[Dict[str, Any]]:
        """Get all states via WebSocket."""
        result = await self.send_command({'type': 'get_states'})
        return result.get('result', [])
    
    async def get_services(self) -> Dict[str, Any]:
        """Get all services via WebSocket."""
        result = await self.send_command({'type': 'get_services'})
        return result.get('result', {})
    
    async def get_config(self) -> Dict[str, Any]:
        """Get configuration via WebSocket."""
        result = await self.send_command({'type': 'get_config'})
        return result.get('result', {})
    
    async def call_service(
        self,
        domain: str,
        service: str,
        service_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call a service via WebSocket."""
        command = {
            'type': 'call_service',
            'domain': domain,
            'service': service,
            'service_data': service_data or {}
        }
        return await self.send_command(command)
    
    async def get_panels(self) -> Dict[str, Any]:
        """Get panels via WebSocket."""
        result = await self.send_command({'type': 'get_panels'})
        return result.get('result', {})
    
    async def get_lovelace_config(self) -> Dict[str, Any]:
        """Get Lovelace configuration."""
        result = await self.send_command({'type': 'lovelace/config'})
        return result.get('result', {})
    
    async def save_lovelace_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Save Lovelace configuration."""
        command = {
            'type': 'lovelace/config/save',
            'config': config
        }
        return await self.send_command(command)