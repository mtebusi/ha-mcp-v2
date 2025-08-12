"""Configuration management for MCP Server."""

import os
from dataclasses import dataclass
from typing import Optional

try:
    import ssl
except ImportError:
    ssl = None


@dataclass
class Config:
    """Server configuration."""
    
    host: str = "0.0.0.0"
    port: int = 8089
    ssl: bool = False
    certfile: Optional[str] = None
    keyfile: Optional[str] = None
    supervisor_token: Optional[str] = None
    ha_url: Optional[str] = None
    ha_token: Optional[str] = None
    log_level: str = "INFO"
    
    def get_ssl_context(self) -> Optional[object]:
        """Get SSL context if SSL is enabled."""
        if not self.ssl or ssl is None:
            return None
        
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        
        if self.certfile and self.keyfile:
            # Check if files exist
            certfile_path = self.certfile
            keyfile_path = self.keyfile
            
            # Handle add-on SSL path
            if not os.path.exists(certfile_path) and os.path.exists(f"/ssl/{certfile_path}"):
                certfile_path = f"/ssl/{certfile_path}"
            if not os.path.exists(keyfile_path) and os.path.exists(f"/ssl/{keyfile_path}"):
                keyfile_path = f"/ssl/{keyfile_path}"
            
            context.load_cert_chain(certfile_path, keyfile_path)
        
        return context
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create config from environment variables."""
        return cls(
            host=os.getenv('MCP_HOST', '0.0.0.0'),
            port=int(os.getenv('MCP_PORT', '8089')),
            ssl=os.getenv('MCP_SSL', 'false').lower() == 'true',
            certfile=os.getenv('MCP_CERTFILE'),
            keyfile=os.getenv('MCP_KEYFILE'),
            supervisor_token=os.getenv('SUPERVISOR_TOKEN'),
            ha_url=os.getenv('HA_URL'),
            ha_token=os.getenv('HA_TOKEN'),
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )
    
    @classmethod
    def from_addon_options(cls, options_path: str = '/data/options.json') -> 'Config':
        """Create config from add-on options."""
        import json
        
        if not os.path.exists(options_path):
            return cls.from_env()
        
        with open(options_path) as f:
            options = json.load(f)
        
        return cls(
            ssl=options.get('ssl', False),
            certfile=options.get('certfile'),
            keyfile=options.get('keyfile'),
            log_level=options.get('log_level', 'info').upper(),
            supervisor_token=os.getenv('SUPERVISOR_TOKEN')
        )