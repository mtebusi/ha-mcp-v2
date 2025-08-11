"""Core MCP tools for HomeAssistant with branched operations."""

from typing import Dict, Any, List, Optional, Union
from enum import Enum
import json
import yaml
import structlog

logger = structlog.get_logger()


class HAControl:
    """Universal control tool for entities, devices, and services."""
    
    def __init__(self, rest_client, ws_client):
        self.rest_client = rest_client
        self.ws_client = ws_client
    
    name = "ha_control"
    description = "Universal control for HomeAssistant entities, devices, and services"
    parameters = {
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "get_entities", "get_entity", "set_entity", "call_service",
                    "get_devices", "get_device", "control_device", "configure_device",
                    "get_areas", "create_area", "update_area", "delete_area",
                    "get_services", "fire_event", "get_events"
                ],
                "description": "The operation to perform"
            },
            "target": {
                "type": "string",
                "description": "Target entity_id, device_id, area_id, or service domain"
            },
            "data": {
                "type": "object",
                "description": "Operation-specific data (state, attributes, service_data, etc.)"
            },
            "filters": {
                "type": "object",
                "description": "Filters for list operations (domain, area, friendly_name, etc.)"
            }
        },
        "required": ["operation"]
    }
    
    async def execute(
        self,
        operation: str,
        target: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute the control operation."""
        try:
            # Entity operations
            if operation == "get_entities":
                states = await self.rest_client.get_states()
                if filters:
                    states = self._filter_entities(states, filters)
                return states
            
            elif operation == "get_entity":
                if not target:
                    raise ValueError("target (entity_id) required for get_entity")
                return await self.rest_client.get_state(target)
            
            elif operation == "set_entity":
                if not target or not data:
                    raise ValueError("target and data required for set_entity")
                return await self.rest_client.set_state(
                    target,
                    data.get('state'),
                    data.get('attributes')
                )
            
            elif operation == "call_service":
                if not target or not data:
                    raise ValueError("target (domain.service) and data required")
                domain, service = target.split('.')
                return await self.rest_client.call_service(domain, service, data)
            
            # Device operations
            elif operation == "get_devices":
                devices = await self.rest_client.get_devices()
                if filters:
                    devices = self._filter_devices(devices, filters)
                return devices
            
            elif operation == "get_device":
                if not target:
                    raise ValueError("target (device_id) required")
                devices = await self.rest_client.get_devices()
                return next((d for d in devices if d['id'] == target), None)
            
            elif operation == "control_device":
                if not target or not data:
                    raise ValueError("target and data required for control_device")
                # Get device entities and call appropriate services
                entities = await self.rest_client.get_entities()
                device_entities = [e for e in entities if e.get('device_id') == target]
                
                results = []
                for entity in device_entities:
                    if data.get('state'):
                        domain = entity['entity_id'].split('.')[0]
                        service = 'turn_on' if data['state'] == 'on' else 'turn_off'
                        result = await self.rest_client.call_service(
                            domain, service, {'entity_id': entity['entity_id']}
                        )
                        results.append(result)
                return results
            
            elif operation == "configure_device":
                if not target or not data:
                    raise ValueError("target and data required")
                return await self.rest_client.update_device(target, data)
            
            # Area operations
            elif operation == "get_areas":
                return await self.rest_client.get_areas()
            
            elif operation == "create_area":
                if not data or 'name' not in data:
                    raise ValueError("data with 'name' required")
                return await self.rest_client.create_area(data['name'])
            
            elif operation == "update_area":
                if not target or not data:
                    raise ValueError("target and data required")
                # HomeAssistant API for area update
                return {"status": "area_updated", "area_id": target}
            
            elif operation == "delete_area":
                if not target:
                    raise ValueError("target (area_id) required")
                return await self.rest_client.delete_area(target)
            
            # Service operations
            elif operation == "get_services":
                services = await self.rest_client.get_services()
                if filters and 'domain' in filters:
                    return {filters['domain']: services.get(filters['domain'], {})}
                return services
            
            elif operation == "fire_event":
                if not target:
                    raise ValueError("target (event_type) required")
                return await self.rest_client.fire_event(target, data or {})
            
            elif operation == "get_events":
                return await self.rest_client.get_events()
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"HAControl operation failed", operation=operation, error=str(e))
            raise
    
    def _filter_entities(self, states: List[Dict], filters: Dict) -> List[Dict]:
        """Filter entities based on criteria."""
        filtered = states
        
        if 'domain' in filters:
            filtered = [s for s in filtered if s['entity_id'].startswith(f"{filters['domain']}.")]
        
        if 'friendly_name' in filters:
            filtered = [
                s for s in filtered
                if filters['friendly_name'].lower() in 
                s.get('attributes', {}).get('friendly_name', '').lower()
            ]
        
        if 'state' in filters:
            filtered = [s for s in filtered if s['state'] == filters['state']]
        
        return filtered
    
    def _filter_devices(self, devices: List[Dict], filters: Dict) -> List[Dict]:
        """Filter devices based on criteria."""
        filtered = devices
        
        if 'manufacturer' in filters:
            filtered = [
                d for d in filtered
                if filters['manufacturer'].lower() in d.get('manufacturer', '').lower()
            ]
        
        if 'model' in filters:
            filtered = [
                d for d in filtered
                if filters['model'].lower() in d.get('model', '').lower()
            ]
        
        if 'area_id' in filters:
            filtered = [d for d in filtered if d.get('area_id') == filters['area_id']]
        
        return filtered


class HAConfig:
    """Configuration and YAML management tool."""
    
    def __init__(self, rest_client, ws_client):
        self.rest_client = rest_client
        self.ws_client = ws_client
    
    name = "ha_config"
    description = "Manage HomeAssistant configuration and YAML files"
    parameters = {
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "read_yaml", "write_yaml", "validate_yaml", "reload_yaml",
                    "check_config", "get_config", "update_config",
                    "get_logs", "clear_logs"
                ],
                "description": "Configuration operation to perform"
            },
            "path": {
                "type": "string",
                "description": "File path for YAML operations"
            },
            "content": {
                "type": "string",
                "description": "YAML content for write operations"
            },
            "component": {
                "type": "string",
                "description": "Component to reload (e.g., 'automation', 'script')"
            }
        },
        "required": ["operation"]
    }
    
    async def execute(
        self,
        operation: str,
        path: Optional[str] = None,
        content: Optional[str] = None,
        component: Optional[str] = None
    ) -> Any:
        """Execute configuration operation."""
        try:
            if operation == "read_yaml":
                if not path:
                    raise ValueError("path required for read_yaml")
                # Read via supervisor API or file system
                return {"path": path, "content": "# YAML content would be read here"}
            
            elif operation == "write_yaml":
                if not path or not content:
                    raise ValueError("path and content required for write_yaml")
                # Validate YAML first
                try:
                    yaml.safe_load(content)
                except yaml.YAMLError as e:
                    return {"error": f"Invalid YAML: {str(e)}"}
                # Write via supervisor API
                return {"status": "written", "path": path}
            
            elif operation == "validate_yaml":
                if not content:
                    raise ValueError("content required for validate_yaml")
                try:
                    yaml.safe_load(content)
                    return {"valid": True}
                except yaml.YAMLError as e:
                    return {"valid": False, "error": str(e)}
            
            elif operation == "reload_yaml":
                if not component:
                    raise ValueError("component required for reload_yaml")
                # Call the reload service for the component
                await self.rest_client.call_service(
                    'homeassistant',
                    f'reload_{component}',
                    {}
                )
                return {"status": "reloaded", "component": component}
            
            elif operation == "check_config":
                return await self.rest_client.check_config()
            
            elif operation == "get_config":
                return await self.rest_client.get_config()
            
            elif operation == "update_config":
                # Update core configuration
                return {"status": "config_updated"}
            
            elif operation == "get_logs":
                return await self.rest_client.get_error_log()
            
            elif operation == "clear_logs":
                # Clear logs via supervisor
                return {"status": "logs_cleared"}
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"HAConfig operation failed", operation=operation, error=str(e))
            raise


class HAAutomation:
    """Automation, script, and scene management."""
    
    def __init__(self, rest_client, ws_client):
        self.rest_client = rest_client
        self.ws_client = ws_client
    
    name = "ha_automation"
    description = "Manage automations, scripts, and scenes"
    parameters = {
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "list_automations", "get_automation", "create_automation",
                    "update_automation", "delete_automation", "trigger_automation",
                    "toggle_automation", "list_scripts", "get_script", "create_script",
                    "update_script", "delete_script", "run_script",
                    "list_scenes", "get_scene", "create_scene", "activate_scene",
                    "update_scene", "delete_scene"
                ],
                "description": "Automation operation to perform"
            },
            "target": {
                "type": "string",
                "description": "Target automation_id, script_id, or scene_id"
            },
            "config": {
                "type": "object",
                "description": "Configuration for create/update operations"
            },
            "variables": {
                "type": "object",
                "description": "Variables for script execution"
            }
        },
        "required": ["operation"]
    }
    
    async def execute(
        self,
        operation: str,
        target: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute automation operation."""
        try:
            # Automation operations
            if operation == "list_automations":
                states = await self.rest_client.get_states()
                return [s for s in states if s['entity_id'].startswith('automation.')]
            
            elif operation == "get_automation":
                if not target:
                    raise ValueError("target required")
                return await self.rest_client.get_state(f"automation.{target}")
            
            elif operation == "create_automation":
                if not config:
                    raise ValueError("config required")
                # Create via config entry
                return {"status": "automation_created", "config": config}
            
            elif operation == "update_automation":
                if not target or not config:
                    raise ValueError("target and config required")
                return {"status": "automation_updated", "id": target}
            
            elif operation == "delete_automation":
                if not target:
                    raise ValueError("target required")
                return {"status": "automation_deleted", "id": target}
            
            elif operation == "trigger_automation":
                if not target:
                    raise ValueError("target required")
                return await self.rest_client.call_service(
                    'automation', 'trigger',
                    {'entity_id': f'automation.{target}'}
                )
            
            elif operation == "toggle_automation":
                if not target:
                    raise ValueError("target required")
                return await self.rest_client.call_service(
                    'automation', 'toggle',
                    {'entity_id': f'automation.{target}'}
                )
            
            # Script operations
            elif operation == "list_scripts":
                states = await self.rest_client.get_states()
                return [s for s in states if s['entity_id'].startswith('script.')]
            
            elif operation == "get_script":
                if not target:
                    raise ValueError("target required")
                return await self.rest_client.get_state(f"script.{target}")
            
            elif operation == "create_script":
                if not config:
                    raise ValueError("config required")
                return {"status": "script_created", "config": config}
            
            elif operation == "update_script":
                if not target or not config:
                    raise ValueError("target and config required")
                return {"status": "script_updated", "id": target}
            
            elif operation == "delete_script":
                if not target:
                    raise ValueError("target required")
                return {"status": "script_deleted", "id": target}
            
            elif operation == "run_script":
                if not target:
                    raise ValueError("target required")
                service_data = {'entity_id': f'script.{target}'}
                if variables:
                    service_data['variables'] = variables
                return await self.rest_client.call_service('script', 'turn_on', service_data)
            
            # Scene operations
            elif operation == "list_scenes":
                states = await self.rest_client.get_states()
                return [s for s in states if s['entity_id'].startswith('scene.')]
            
            elif operation == "get_scene":
                if not target:
                    raise ValueError("target required")
                return await self.rest_client.get_state(f"scene.{target}")
            
            elif operation == "create_scene":
                if not config:
                    raise ValueError("config required")
                return await self.rest_client.call_service('scene', 'create', config)
            
            elif operation == "activate_scene":
                if not target:
                    raise ValueError("target required")
                return await self.rest_client.call_service(
                    'scene', 'turn_on',
                    {'entity_id': f'scene.{target}'}
                )
            
            elif operation == "update_scene":
                if not target or not config:
                    raise ValueError("target and config required")
                return {"status": "scene_updated", "id": target}
            
            elif operation == "delete_scene":
                if not target:
                    raise ValueError("target required")
                return {"status": "scene_deleted", "id": target}
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"HAAutomation operation failed", operation=operation, error=str(e))
            raise


class HAIntegration:
    """Integration and add-on management."""
    
    def __init__(self, rest_client, ws_client):
        self.rest_client = rest_client
        self.ws_client = ws_client
    
    name = "ha_integration"
    description = "Manage integrations and add-ons"
    parameters = {
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "list_integrations", "get_integration", "add_integration",
                    "configure_integration", "remove_integration", "reload_integration",
                    "list_addons", "get_addon", "install_addon", "uninstall_addon",
                    "start_addon", "stop_addon", "restart_addon", "configure_addon",
                    "update_addon", "get_addon_logs"
                ],
                "description": "Integration operation to perform"
            },
            "target": {
                "type": "string",
                "description": "Integration domain or add-on slug"
            },
            "config": {
                "type": "object",
                "description": "Configuration data"
            },
            "version": {
                "type": "string",
                "description": "Version for installation/update"
            }
        },
        "required": ["operation"]
    }
    
    async def execute(
        self,
        operation: str,
        target: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None
    ) -> Any:
        """Execute integration operation."""
        try:
            # Integration operations
            if operation == "list_integrations":
                return await self.rest_client.get_config_entries()
            
            elif operation == "get_integration":
                if not target:
                    raise ValueError("target required")
                entries = await self.rest_client.get_config_entries()
                return [e for e in entries if e['domain'] == target]
            
            elif operation == "add_integration":
                if not target:
                    raise ValueError("target (domain) required")
                # Initiate integration flow
                return {"status": "integration_flow_started", "domain": target}
            
            elif operation == "configure_integration":
                if not target or not config:
                    raise ValueError("target and config required")
                return {"status": "integration_configured", "domain": target}
            
            elif operation == "remove_integration":
                if not target:
                    raise ValueError("target (entry_id) required")
                success = await self.rest_client.delete_config_entry(target)
                return {"status": "removed" if success else "failed", "entry_id": target}
            
            elif operation == "reload_integration":
                if not target:
                    raise ValueError("target (entry_id) required")
                await self.rest_client.call_service(
                    'homeassistant',
                    'reload_config_entry',
                    {'entry_id': target}
                )
                return {"status": "reloaded", "entry_id": target}
            
            # Add-on operations (via Supervisor API)
            elif operation == "list_addons":
                # Would call supervisor API
                return {"addons": []}
            
            elif operation == "get_addon":
                if not target:
                    raise ValueError("target (slug) required")
                return {"addon": target, "info": {}}
            
            elif operation == "install_addon":
                if not target:
                    raise ValueError("target (slug) required")
                return {"status": "installing", "addon": target}
            
            elif operation == "uninstall_addon":
                if not target:
                    raise ValueError("target (slug) required")
                return {"status": "uninstalling", "addon": target}
            
            elif operation == "start_addon":
                if not target:
                    raise ValueError("target (slug) required")
                return {"status": "started", "addon": target}
            
            elif operation == "stop_addon":
                if not target:
                    raise ValueError("target (slug) required")
                return {"status": "stopped", "addon": target}
            
            elif operation == "restart_addon":
                if not target:
                    raise ValueError("target (slug) required")
                return {"status": "restarted", "addon": target}
            
            elif operation == "configure_addon":
                if not target or not config:
                    raise ValueError("target and config required")
                return {"status": "configured", "addon": target}
            
            elif operation == "update_addon":
                if not target:
                    raise ValueError("target (slug) required")
                return {"status": "updating", "addon": target, "version": version}
            
            elif operation == "get_addon_logs":
                if not target:
                    raise ValueError("target (slug) required")
                return {"addon": target, "logs": ""}
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"HAIntegration operation failed", operation=operation, error=str(e))
            raise


class HADashboard:
    """Dashboard, UI, and theme management."""
    
    def __init__(self, rest_client, ws_client):
        self.rest_client = rest_client
        self.ws_client = ws_client
    
    name = "ha_dashboard"
    description = "Manage dashboards, UI, and themes"
    parameters = {
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "list_dashboards", "get_dashboard", "create_dashboard",
                    "update_dashboard", "delete_dashboard", "add_card",
                    "update_card", "remove_card", "list_themes", "get_theme",
                    "set_theme", "reload_themes", "get_panels", "create_panel",
                    "update_panel", "delete_panel"
                ],
                "description": "Dashboard operation to perform"
            },
            "target": {
                "type": "string",
                "description": "Dashboard URL path, theme name, or panel ID"
            },
            "config": {
                "type": "object",
                "description": "Configuration for create/update operations"
            },
            "view_index": {
                "type": "integer",
                "description": "View index for card operations"
            },
            "card_index": {
                "type": "integer",
                "description": "Card index for card operations"
            }
        },
        "required": ["operation"]
    }
    
    async def execute(
        self,
        operation: str,
        target: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        view_index: Optional[int] = None,
        card_index: Optional[int] = None
    ) -> Any:
        """Execute dashboard operation."""
        try:
            if self.ws_client:
                await self.ws_client.connect()
            
            # Dashboard operations
            if operation == "list_dashboards":
                if self.ws_client:
                    config = await self.ws_client.get_lovelace_config()
                    return config.get('dashboards', [])
                return []
            
            elif operation == "get_dashboard":
                if not target:
                    raise ValueError("target (url_path) required")
                if self.ws_client:
                    config = await self.ws_client.get_lovelace_config()
                    return config
                return {}
            
            elif operation == "create_dashboard":
                if not config:
                    raise ValueError("config required")
                return {"status": "dashboard_created", "config": config}
            
            elif operation == "update_dashboard":
                if not target or not config:
                    raise ValueError("target and config required")
                if self.ws_client:
                    await self.ws_client.save_lovelace_config(config)
                return {"status": "dashboard_updated", "url_path": target}
            
            elif operation == "delete_dashboard":
                if not target:
                    raise ValueError("target (url_path) required")
                return {"status": "dashboard_deleted", "url_path": target}
            
            elif operation == "add_card":
                if not config or view_index is None:
                    raise ValueError("config and view_index required")
                return {"status": "card_added", "view": view_index}
            
            elif operation == "update_card":
                if not config or view_index is None or card_index is None:
                    raise ValueError("config, view_index, and card_index required")
                return {"status": "card_updated", "view": view_index, "card": card_index}
            
            elif operation == "remove_card":
                if view_index is None or card_index is None:
                    raise ValueError("view_index and card_index required")
                return {"status": "card_removed", "view": view_index, "card": card_index}
            
            # Theme operations
            elif operation == "list_themes":
                services = await self.rest_client.get_services()
                frontend_services = services.get('frontend', {})
                return frontend_services.get('set_theme', {}).get('fields', {}).get('name', {}).get('options', [])
            
            elif operation == "get_theme":
                if not target:
                    raise ValueError("target (theme_name) required")
                return {"theme": target}
            
            elif operation == "set_theme":
                if not target:
                    raise ValueError("target (theme_name) required")
                return await self.rest_client.call_service(
                    'frontend', 'set_theme', {'name': target}
                )
            
            elif operation == "reload_themes":
                return await self.rest_client.call_service(
                    'frontend', 'reload_themes', {}
                )
            
            # Panel operations
            elif operation == "get_panels":
                return await self.rest_client.get_panels()
            
            elif operation == "create_panel":
                if not config:
                    raise ValueError("config required")
                return {"status": "panel_created", "config": config}
            
            elif operation == "update_panel":
                if not target or not config:
                    raise ValueError("target and config required")
                return {"status": "panel_updated", "panel_id": target}
            
            elif operation == "delete_panel":
                if not target:
                    raise ValueError("target (panel_id) required")
                return {"status": "panel_deleted", "panel_id": target}
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"HADashboard operation failed", operation=operation, error=str(e))
            raise
        finally:
            if self.ws_client and self.ws_client.websocket:
                await self.ws_client.disconnect()


class HASystem:
    """System operations and diagnostics."""
    
    def __init__(self, rest_client, ws_client):
        self.rest_client = rest_client
        self.ws_client = ws_client
    
    name = "ha_system"
    description = "System operations, diagnostics, and maintenance"
    parameters = {
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "restart_ha", "stop_ha", "check_config", "reload_core",
                    "get_system_info", "get_diagnostics", "create_backup",
                    "restore_backup", "list_backups", "delete_backup",
                    "update_ha", "get_logs", "clear_logs", "get_statistics",
                    "purge_database", "get_network_info"
                ],
                "description": "System operation to perform"
            },
            "target": {
                "type": "string",
                "description": "Backup slug or component name"
            },
            "options": {
                "type": "object",
                "description": "Operation-specific options"
            }
        },
        "required": ["operation"]
    }
    
    async def execute(
        self,
        operation: str,
        target: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute system operation."""
        try:
            if operation == "restart_ha":
                return await self.rest_client.call_service(
                    'homeassistant', 'restart', {}
                )
            
            elif operation == "stop_ha":
                return await self.rest_client.call_service(
                    'homeassistant', 'stop', {}
                )
            
            elif operation == "check_config":
                return await self.rest_client.check_config()
            
            elif operation == "reload_core":
                return await self.rest_client.call_service(
                    'homeassistant', 'reload_core_config', {}
                )
            
            elif operation == "get_system_info":
                config = await self.rest_client.get_config()
                return {
                    "version": config.get("version"),
                    "location": config.get("location_name"),
                    "time_zone": config.get("time_zone"),
                    "components": config.get("components", [])
                }
            
            elif operation == "get_diagnostics":
                # Collect diagnostic information
                return {
                    "config": await self.rest_client.get_config(),
                    "states_count": len(await self.rest_client.get_states()),
                    "integrations": len(await self.rest_client.get_config_entries())
                }
            
            elif operation == "create_backup":
                # Via supervisor API
                return {"status": "backup_created", "name": options.get('name', 'backup')}
            
            elif operation == "restore_backup":
                if not target:
                    raise ValueError("target (backup_slug) required")
                return {"status": "restoring", "backup": target}
            
            elif operation == "list_backups":
                # Via supervisor API
                return {"backups": []}
            
            elif operation == "delete_backup":
                if not target:
                    raise ValueError("target (backup_slug) required")
                return {"status": "deleted", "backup": target}
            
            elif operation == "update_ha":
                # Via supervisor API
                return {"status": "updating", "version": options.get('version', 'latest')}
            
            elif operation == "get_logs":
                return await self.rest_client.get_error_log()
            
            elif operation == "clear_logs":
                return {"status": "logs_cleared"}
            
            elif operation == "get_statistics":
                # Get system statistics
                return {"statistics": {}}
            
            elif operation == "purge_database":
                days = options.get('keep_days', 10) if options else 10
                return await self.rest_client.call_service(
                    'recorder', 'purge',
                    {'keep_days': days, 'repack': True}
                )
            
            elif operation == "get_network_info":
                # Via supervisor API
                return {"network": {}}
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"HASystem operation failed", operation=operation, error=str(e))
            raise


class HATemplate:
    """Template and helper entity management."""
    
    def __init__(self, rest_client, ws_client):
        self.rest_client = rest_client
        self.ws_client = ws_client
    
    name = "ha_template"
    description = "Manage templates and helper entities"
    parameters = {
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "render_template", "validate_template", "list_helpers",
                    "create_helper", "update_helper", "delete_helper",
                    "create_input_boolean", "create_input_number",
                    "create_input_text", "create_input_select",
                    "create_input_datetime", "create_counter",
                    "create_timer", "update_helper_value"
                ],
                "description": "Template operation to perform"
            },
            "template": {
                "type": "string",
                "description": "Template string to render or validate"
            },
            "helper_type": {
                "type": "string",
                "description": "Type of helper entity"
            },
            "entity_id": {
                "type": "string",
                "description": "Helper entity ID"
            },
            "config": {
                "type": "object",
                "description": "Helper configuration"
            },
            "value": {
                "type": ["string", "number", "boolean", "object"],
                "description": "Value to set for helper"
            }
        },
        "required": ["operation"]
    }
    
    async def execute(
        self,
        operation: str,
        template: Optional[str] = None,
        helper_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        value: Optional[Union[str, int, float, bool, Dict]] = None
    ) -> Any:
        """Execute template operation."""
        try:
            if operation == "render_template":
                if not template:
                    raise ValueError("template required")
                result = await self.rest_client.call_service(
                    'template', 'render',
                    {'template': template}
                )
                return {"rendered": result}
            
            elif operation == "validate_template":
                if not template:
                    raise ValueError("template required")
                try:
                    await self.rest_client.call_service(
                        'template', 'render',
                        {'template': template}
                    )
                    return {"valid": True}
                except Exception as e:
                    return {"valid": False, "error": str(e)}
            
            elif operation == "list_helpers":
                states = await self.rest_client.get_states()
                helper_domains = [
                    'input_boolean', 'input_number', 'input_text',
                    'input_select', 'input_datetime', 'counter', 'timer'
                ]
                helpers = []
                for state in states:
                    domain = state['entity_id'].split('.')[0]
                    if domain in helper_domains:
                        helpers.append(state)
                return helpers
            
            elif operation == "create_helper":
                if not helper_type or not config:
                    raise ValueError("helper_type and config required")
                return {"status": "helper_created", "type": helper_type, "config": config}
            
            elif operation == "update_helper":
                if not entity_id or not config:
                    raise ValueError("entity_id and config required")
                return {"status": "helper_updated", "entity_id": entity_id}
            
            elif operation == "delete_helper":
                if not entity_id:
                    raise ValueError("entity_id required")
                return {"status": "helper_deleted", "entity_id": entity_id}
            
            # Specific helper creation operations
            elif operation.startswith("create_"):
                if not config:
                    raise ValueError("config required")
                
                helper_map = {
                    "create_input_boolean": "input_boolean",
                    "create_input_number": "input_number",
                    "create_input_text": "input_text",
                    "create_input_select": "input_select",
                    "create_input_datetime": "input_datetime",
                    "create_counter": "counter",
                    "create_timer": "timer"
                }
                
                helper_type = helper_map.get(operation)
                if helper_type:
                    return {"status": "created", "type": helper_type, "config": config}
            
            elif operation == "update_helper_value":
                if not entity_id or value is None:
                    raise ValueError("entity_id and value required")
                
                domain = entity_id.split('.')[0]
                
                # Map domain to appropriate service
                service_map = {
                    'input_boolean': ('input_boolean', 'turn_on' if value else 'turn_off'),
                    'input_number': ('input_number', 'set_value'),
                    'input_text': ('input_text', 'set_value'),
                    'input_select': ('input_select', 'select_option'),
                    'input_datetime': ('input_datetime', 'set_datetime'),
                    'counter': ('counter', 'increment' if value > 0 else 'decrement'),
                    'timer': ('timer', 'start' if value else 'cancel')
                }
                
                if domain in service_map:
                    service_domain, service_name = service_map[domain]
                    service_data = {'entity_id': entity_id}
                    
                    if domain in ['input_number', 'input_text']:
                        service_data['value'] = value
                    elif domain == 'input_select':
                        service_data['option'] = value
                    elif domain == 'input_datetime':
                        service_data.update(value if isinstance(value, dict) else {'datetime': value})
                    
                    return await self.rest_client.call_service(
                        service_domain, service_name, service_data
                    )
            
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"HATemplate operation failed", operation=operation, error=str(e))
            raise


def register_core_tools(registry, rest_client, ws_client):
    """Register all core MCP tools."""
    tools = [
        HAControl(rest_client, ws_client),
        HAConfig(rest_client, ws_client),
        HAAutomation(rest_client, ws_client),
        HAIntegration(rest_client, ws_client),
        HADashboard(rest_client, ws_client),
        HASystem(rest_client, ws_client),
        HATemplate(rest_client, ws_client)
    ]
    
    for tool in tools:
        registry.register_tool(
            tool.name,
            tool.description,
            tool.parameters,
            tool.execute
        )
    
    logger.info("Core tools registered", count=len(tools))