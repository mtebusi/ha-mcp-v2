"""Base class for MCP tools."""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseTool(ABC):
    """Base class for all MCP tools."""
    
    def __init__(self, rest_client, ws_client):
        """Initialize tool with API clients."""
        self.rest_client = rest_client
        self.ws_client = ws_client
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """Tool parameters schema."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool."""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for MCP."""
        return {
            'name': self.name,
            'description': self.description,
            'inputSchema': {
                'type': 'object',
                'properties': self.parameters.get('properties', {}),
                'required': self.parameters.get('required', [])
            }
        }