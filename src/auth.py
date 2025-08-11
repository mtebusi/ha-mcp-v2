"""OAuth2 authentication handler for HomeAssistant."""

import secrets
import time
from typing import Dict, Optional
from urllib.parse import urlencode

import jwt
import structlog

logger = structlog.get_logger()


class AuthHandler:
    """Handle OAuth2 authentication with HomeAssistant."""
    
    def __init__(self, config):
        """Initialize auth handler."""
        self.config = config
        self.pending_auths: Dict[str, Dict] = {}
        self.token_cache: Dict[str, Dict] = {}
        
        # OAuth2 configuration
        self.client_id = "mcp_server"
        self.redirect_uri = f"http://{config.host}:{config.port}/auth/callback"
        
        # Get HomeAssistant base URL
        if config.supervisor_token:
            # Running as add-on
            self.ha_base_url = "http://homeassistant.local:8123"  # External URL
        else:
            # Running standalone
            self.ha_base_url = config.ha_url or "http://localhost:8123"
    
    def get_auth_url(self, connection_id: str) -> str:
        """Generate OAuth2 authorization URL."""
        state = secrets.token_urlsafe(32)
        
        # Store state for validation
        self.pending_auths[state] = {
            'connection_id': connection_id,
            'created_at': time.time()
        }
        
        # Clean up old pending auths (older than 10 minutes)
        current_time = time.time()
        self.pending_auths = {
            k: v for k, v in self.pending_auths.items()
            if current_time - v['created_at'] < 600
        }
        
        # Build auth URL
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'state': state,
            'response_type': 'code'
        }
        
        auth_url = f"{self.ha_base_url}/auth/authorize?{urlencode(params)}"
        logger.info("Generated auth URL", connection_id=connection_id)
        
        return auth_url
    
    async def exchange_code(self, code: str, state: str) -> Optional[str]:
        """Exchange authorization code for access token."""
        # Validate state
        if state not in self.pending_auths:
            logger.warning("Invalid state in auth callback", state=state)
            return None
        
        auth_info = self.pending_auths.pop(state)
        connection_id = auth_info['connection_id']
        
        # In a real implementation, we would exchange the code for a token
        # via HomeAssistant's token endpoint. For now, we'll simulate this.
        # The actual implementation would make a POST request to /auth/token
        
        # Generate a mock token for development
        token_payload = {
            'connection_id': connection_id,
            'iat': time.time(),
            'exp': time.time() + 3600,  # 1 hour expiry
            'scope': 'full_access'
        }
        
        # In production, this would be the actual access token from HA
        token = jwt.encode(token_payload, 'secret', algorithm='HS256')
        
        # Cache token
        self.token_cache[token] = {
            'connection_id': connection_id,
            'created_at': time.time(),
            'expires_at': time.time() + 3600
        }
        
        logger.info("Token exchange successful", connection_id=connection_id)
        return token
    
    async def validate_token(self, token: str) -> bool:
        """Validate an access token."""
        # Check token cache
        if token in self.token_cache:
            token_info = self.token_cache[token]
            if time.time() < token_info['expires_at']:
                return True
            else:
                # Token expired
                del self.token_cache[token]
                return False
        
        # In production, validate with HomeAssistant
        # For development, try to decode the JWT
        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
            if time.time() < payload.get('exp', 0):
                # Cache valid token
                self.token_cache[token] = {
                    'connection_id': payload.get('connection_id'),
                    'created_at': payload.get('iat'),
                    'expires_at': payload.get('exp')
                }
                return True
        except jwt.InvalidTokenError:
            pass
        
        return False
    
    async def refresh_token(self, refresh_token: str) -> Optional[str]:
        """Refresh an access token."""
        # In production, this would call HomeAssistant's token refresh endpoint
        # For now, return None to indicate refresh not implemented
        return None