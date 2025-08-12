"""HomeAssistant MCP Server Package."""

from .constants import VERSION, MCP_PROTOCOL_VERSION, MIN_HA_VERSION

__version__ = VERSION
__all__ = ['VERSION', 'MCP_PROTOCOL_VERSION', 'MIN_HA_VERSION']