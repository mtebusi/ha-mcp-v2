"""HomeAssistant REST API client."""

import asyncio
from typing import Dict, Any, Optional, List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

from constants import HA_API_TIMEOUT, HA_API_RETRY_COUNT, HA_API_RETRY_DELAY

logger = structlog.get_logger()


class HARestClient:
    """Client for HomeAssistant REST API."""
    
    def __init__(self, base_url: str, token: str):
        """Initialize REST client."""
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        self.client = httpx.AsyncClient(
            timeout=HA_API_TIMEOUT,
            headers=self.headers
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the client."""
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(HA_API_RETRY_COUNT),
        wait=wait_exponential(multiplier=HA_API_RETRY_DELAY)
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """Make an API request with retry logic."""
        url = f"{self.base_url}/api{endpoint}"
        response = await self.client.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    
    async def get_config(self) -> Dict[str, Any]:
        """Get HomeAssistant configuration."""
        response = await self._request('GET', '/config')
        return response.json()
    
    async def get_states(self) -> List[Dict[str, Any]]:
        """Get all entity states."""
        response = await self._request('GET', '/states')
        return response.json()
    
    async def get_state(self, entity_id: str) -> Dict[str, Any]:
        """Get state of a specific entity."""
        response = await self._request('GET', f'/states/{entity_id}')
        return response.json()
    
    async def set_state(
        self,
        entity_id: str,
        state: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Set state of an entity."""
        data = {
            'state': state,
            'attributes': attributes or {}
        }
        response = await self._request('POST', f'/states/{entity_id}', json=data)
        return response.json()
    
    async def call_service(
        self,
        domain: str,
        service: str,
        service_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Call a HomeAssistant service."""
        response = await self._request(
            'POST',
            f'/services/{domain}/{service}',
            json=service_data or {}
        )
        return response.json()
    
    async def get_services(self) -> Dict[str, Any]:
        """Get all available services."""
        response = await self._request('GET', '/services')
        return response.json()
    
    async def get_events(self) -> List[Dict[str, Any]]:
        """Get list of events."""
        response = await self._request('GET', '/events')
        return response.json()
    
    async def fire_event(
        self,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fire an event."""
        response = await self._request(
            'POST',
            f'/events/{event_type}',
            json=event_data or {}
        )
        return response.json()
    
    async def get_panels(self) -> Dict[str, Any]:
        """Get registered panels."""
        response = await self._request('GET', '/panels')
        return response.json()
    
    async def get_error_log(self) -> str:
        """Get error log."""
        response = await self._request('GET', '/error_log')
        return response.text
    
    async def check_config(self) -> Dict[str, Any]:
        """Check configuration."""
        response = await self._request('POST', '/config/core/check_config')
        return response.json()
    
    # Integration management
    async def get_config_entries(self) -> List[Dict[str, Any]]:
        """Get all config entries (integrations)."""
        response = await self._request('GET', '/config/config_entries/entry')
        return response.json()
    
    async def delete_config_entry(self, entry_id: str) -> bool:
        """Delete a config entry."""
        response = await self._request('DELETE', f'/config/config_entries/entry/{entry_id}')
        return response.status_code == 200
    
    # Device registry
    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get all devices."""
        response = await self._request('GET', '/config/device_registry/list')
        return response.json()
    
    async def update_device(
        self,
        device_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update device information."""
        response = await self._request(
            'POST',
            f'/config/device_registry/{device_id}',
            json=update_data
        )
        return response.json()
    
    # Entity registry
    async def get_entities(self) -> List[Dict[str, Any]]:
        """Get all entities from registry."""
        response = await self._request('GET', '/config/entity_registry/list')
        return response.json()
    
    async def update_entity(
        self,
        entity_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update entity in registry."""
        response = await self._request(
            'POST',
            f'/config/entity_registry/{entity_id}',
            json=update_data
        )
        return response.json()
    
    # Area registry
    async def get_areas(self) -> List[Dict[str, Any]]:
        """Get all areas."""
        response = await self._request('GET', '/config/area_registry/list')
        return response.json()
    
    async def create_area(self, name: str) -> Dict[str, Any]:
        """Create a new area."""
        response = await self._request(
            'POST',
            '/config/area_registry/create',
            json={'name': name}
        )
        return response.json()
    
    async def delete_area(self, area_id: str) -> bool:
        """Delete an area."""
        response = await self._request('DELETE', f'/config/area_registry/{area_id}')
        return response.status_code == 200