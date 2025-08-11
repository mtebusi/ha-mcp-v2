"""Constants and version management for HomeAssistant MCP Server."""

VERSION = "0.0.1"
BUILD_DATE = "2025-01-11"
MCP_PROTOCOL_VERSION = "1.0"
MIN_HA_VERSION = "2024.1.0"

# Server configuration
DEFAULT_PORT = 8089
DEFAULT_HOST = "0.0.0.0"
SSE_ENDPOINT = "/sse"
MAX_CONNECTIONS = 10
CONNECTION_TIMEOUT = 300  # seconds
KEEPALIVE_INTERVAL = 30  # seconds

# HomeAssistant API
HA_API_TIMEOUT = 30  # seconds
HA_API_RETRY_COUNT = 3
HA_API_RETRY_DELAY = 1  # seconds

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Rate limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds

# Cache settings
CACHE_TTL = 60  # seconds
CACHE_MAX_SIZE = 1000  # entries