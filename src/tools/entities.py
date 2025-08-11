"""Entity management tools for HomeAssistant."""

from typing import Dict, Any, List, Optional
from .base import BaseTool


class GetEntities(BaseTool):
    """Get entities from HomeAssistant."""
    
    name = "get_entities"
    description = "Query entities by domain, area, or attributes"
    parameters = {
        "properties": {
            "domain": {
                "type": "string",
                "description": "Filter by domain (e.g., 'light', 'switch', 'sensor')"
            },
            "area": {
                "type": "string",
                "description": "Filter by area name"
            },
            "device": {
                "type": "string",
                "description": "Filter by device ID"
            },
            "friendly_name": {
                "type": "string",
                "description": "Filter by friendly name (partial match)"
            }
        },
        "required": []
    }
    
    async def execute(self, **kwargs) -> List[Dict[str, Any]]:
        """Execute the tool."""
        states = await self.rest_client.get_states()
        
        # Apply filters
        filtered = states
        
        if domain := kwargs.get('domain'):
            filtered = [s for s in filtered if s['entity_id'].startswith(f"{domain}.")]
        
        if area := kwargs.get('area'):
            # Get entity registry to check areas
            entities = await self.rest_client.get_entities()
            area_entities = {e['entity_id'] for e in entities if e.get('area_id') == area}
            filtered = [s for s in filtered if s['entity_id'] in area_entities]
        
        if device := kwargs.get('device'):
            entities = await self.rest_client.get_entities()
            device_entities = {e['entity_id'] for e in entities if e.get('device_id') == device}
            filtered = [s for s in filtered if s['entity_id'] in device_entities]
        
        if friendly_name := kwargs.get('friendly_name'):
            filtered = [
                s for s in filtered
                if friendly_name.lower() in s.get('attributes', {}).get('friendly_name', '').lower()
            ]
        
        return filtered


class GetEntityState(BaseTool):
    """Get current state of an entity."""
    
    name = "get_entity_state"
    description = "Get current state and attributes of a specific entity"
    parameters = {
        "properties": {
            "entity_id": {
                "type": "string",
                "description": "Entity ID (e.g., 'light.living_room')"
            }
        },
        "required": ["entity_id"]
    }
    
    async def execute(self, entity_id: str) -> Dict[str, Any]:
        """Execute the tool."""
        return await self.rest_client.get_state(entity_id)


class SetEntityState(BaseTool):
    """Set state of an entity."""
    
    name = "set_entity_state"
    description = "Update the state of an entity"
    parameters = {
        "properties": {
            "entity_id": {
                "type": "string",
                "description": "Entity ID to update"
            },
            "state": {
                "type": "string",
                "description": "New state value"
            },
            "attributes": {
                "type": "object",
                "description": "Additional attributes to set"
            }
        },
        "required": ["entity_id", "state"]
    }
    
    async def execute(
        self,
        entity_id: str,
        state: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute the tool."""
        return await self.rest_client.set_state(entity_id, state, attributes)


class CallService(BaseTool):
    """Call a HomeAssistant service."""
    
    name = "call_service"
    description = "Call any HomeAssistant service"
    parameters = {
        "properties": {
            "domain": {
                "type": "string",
                "description": "Service domain (e.g., 'light', 'switch')"
            },
            "service": {
                "type": "string",
                "description": "Service name (e.g., 'turn_on', 'toggle')"
            },
            "entity_id": {
                "type": "string",
                "description": "Target entity ID or list of entity IDs"
            },
            "service_data": {
                "type": "object",
                "description": "Additional service data"
            }
        },
        "required": ["domain", "service"]
    }
    
    async def execute(
        self,
        domain: str,
        service: str,
        entity_id: Optional[str] = None,
        service_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute the tool."""
        data = service_data or {}
        if entity_id:
            data['entity_id'] = entity_id
        
        return await self.rest_client.call_service(domain, service, data)


class GetServices(BaseTool):
    """Get available services."""
    
    name = "get_services"
    description = "Get all available HomeAssistant services"
    parameters = {
        "properties": {
            "domain": {
                "type": "string",
                "description": "Filter by domain (optional)"
            }
        },
        "required": []
    }
    
    async def execute(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Execute the tool."""
        services = await self.rest_client.get_services()
        
        if domain:
            return {domain: services.get(domain, {})}
        
        return services


def register_entity_tools(registry, rest_client, ws_client):
    """Register entity management tools."""
    tools = [
        GetEntities(rest_client, ws_client),
        GetEntityState(rest_client, ws_client),
        SetEntityState(rest_client, ws_client),
        CallService(rest_client, ws_client),
        GetServices(rest_client, ws_client)
    ]
    
    for tool in tools:
        registry.register_tool(
            tool.name,
            tool.description,
            tool.parameters,
            tool.execute
        )