"""Tool registry for MCP server."""

from typing import Dict, Any, List, Callable
import asyncio
import structlog

logger = structlog.get_logger()


class Tool:
    """Represents an MCP tool."""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable
    ):
        """Initialize tool."""
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
    
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
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool."""
        try:
            # Validate parameters
            required = self.parameters.get('required', [])
            for param in required:
                if param not in params:
                    return {
                        'error': f'Missing required parameter: {param}'
                    }
            
            # Execute handler
            if asyncio.iscoroutinefunction(self.handler):
                result = await self.handler(**params)
            else:
                result = self.handler(**params)
            
            return {'result': result}
        except Exception as e:
            logger.error("Tool execution failed", tool=self.name, error=str(e))
            return {'error': str(e)}


class ToolRegistry:
    """Registry for MCP tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, Tool] = {}
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable
    ):
        """Register a new tool."""
        tool = Tool(name, description, parameters, handler)
        self.tools[name] = tool
        logger.debug("Tool registered", name=name)
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all registered tools."""
        return [tool.get_schema() for tool in self.tools.values()]
    
    async def execute_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name."""
        tool = self.tools.get(name)
        if not tool:
            return {'error': f'Unknown tool: {name}'}
        
        return await tool.execute(params)