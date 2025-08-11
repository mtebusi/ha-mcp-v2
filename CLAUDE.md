# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**HomeAssistant MCP Server Add-on** - A secure, locally-hosted MCP (Model Context Protocol) server that runs as a HomeAssistant add-on, enabling Claude Desktop to interact with HomeAssistant instances through its native Connections capability.

### Core Features
- SSE-based MCP server accessible at `<homeassistant_url>/sse`
- OAuth2 authentication using HomeAssistant's native auth system
- Full HomeAssistant control through REST and WebSocket APIs
- Multi-architecture support (amd64, aarch64, armhf, armv7, i386)
- AppArmor security profile with Security Rating 8
- Zero-configuration setup for end users

## Version Management

All version references use these variables:
```yaml
VERSION: "1.0.0"
BUILD_DATE: "2025-01-11"
MCP_PROTOCOL_VERSION: "1.0"
MIN_HA_VERSION: "2024.1.0"
```

## Project Architecture

### Directory Structure
```
/
├── addon/                          # HomeAssistant add-on package
│   ├── config.yaml                # Add-on configuration manifest
│   ├── Dockerfile                 # Multi-stage, multi-arch Dockerfile
│   ├── build.yaml                 # Build configuration for architectures
│   ├── apparmor.txt              # AppArmor security profile
│   ├── icon.png                  # 256x256 add-on icon
│   ├── logo.png                  # 512x512 add-on logo
│   ├── CHANGELOG.md              # Version changelog
│   ├── DOCS.md                   # User documentation
│   └── README.md                 # Add-on description
├── src/                           # MCP server implementation
│   ├── __init__.py               # Package initialization
│   ├── server.py                 # Main SSE MCP server
│   ├── auth.py                   # OAuth2 authentication handler
│   ├── config.py                 # Configuration management
│   ├── constants.py              # Version and constant definitions
│   ├── tools/                    # MCP tools implementation
│   │   ├── __init__.py          
│   │   ├── base.py              # Base tool class
│   │   ├── entities.py          # Entity management tools
│   │   ├── devices.py           # Device control tools
│   │   ├── integrations.py      # Integration management
│   │   ├── addons.py            # Add-on management
│   │   ├── scenes.py            # Scene management
│   │   ├── automations.py       # Automation tools
│   │   ├── scripts.py           # Script management
│   │   ├── helpers.py           # Helper entities
│   │   ├── dashboards.py        # Dashboard management
│   │   ├── themes.py            # Theme management
│   │   └── yaml_editor.py       # YAML configuration editor
│   ├── ha_api/                   # HomeAssistant API clients
│   │   ├── __init__.py
│   │   ├── rest.py              # REST API client
│   │   ├── websocket.py         # WebSocket API client
│   │   └── auth.py              # Auth API wrapper
│   ├── mcp/                      # MCP protocol implementation
│   │   ├── __init__.py
│   │   ├── protocol.py          # MCP protocol handler
│   │   ├── sse.py               # SSE transport layer
│   │   └── registry.py          # Tool registry
│   └── requirements.txt          # Python dependencies
├── .github/                       # GitHub configuration
│   ├── workflows/
│   │   ├── build.yml            # Multi-arch build and publish
│   │   ├── lint.yml             # Code quality checks
│   │   ├── test.yml             # Automated testing
│   │   └── release.yml          # Release automation
│   └── dependabot.yml           # Dependency updates
├── tests/                         # Test suite (gitignored)
│   ├── docker-compose.yml        # Test HomeAssistant instance
│   ├── conftest.py              # pytest configuration
│   ├── test_auth.py             # Authentication tests
│   ├── test_tools.py            # Tool functionality tests
│   ├── test_integration.py      # Integration tests
│   └── fixtures/                # Test data and mocks
├── scripts/                       # Development scripts
│   ├── build.sh                 # Local build script
│   ├── test.sh                  # Test runner
│   └── release.sh               # Release helper
├── repository.yaml               # Add-on repository manifest
├── README.md                     # Repository documentation
├── LICENSE                       # MIT License
├── .gitignore                   # Git ignore configuration
└── .editorconfig                # Editor configuration

```

## Development Commands

### Build Commands
```bash
# Build add-on locally for testing
./scripts/build.sh --arch amd64

# Build all architectures
./scripts/build.sh --all

# Build with debug output
DEBUG=1 ./scripts/build.sh
```

### Test Commands
```bash
# Run full test suite with HomeAssistant instance
./scripts/test.sh --full

# Run unit tests only
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Lint Commands
```bash
# Python linting
ruff check src/
black --check src/
mypy src/

# YAML validation
yamllint addon/
yamllint .github/

# Dockerfile linting
hadolint addon/Dockerfile

# Add-on validation (HomeAssistant compliance)
python -m homeassistant.components.hassio validate addon/
```

### Development Server
```bash
# Run MCP server locally (requires HA instance)
python -m src.server --debug --ha-url http://localhost:8123 --token <long_lived_token>

# Run with test HomeAssistant
docker-compose -f tests/docker-compose.yml up -d
python -m src.server --test-mode
```

## Implementation Details

### MCP Server Core (`src/server.py`)
```python
# Main server implementation pattern
class MCPServer:
    - Initialize SSE endpoint at /sse
    - Handle OAuth2 authentication flow
    - Register all available tools
    - Process incoming MCP requests
    - Stream responses via SSE
    - Maintain connection state
    - Handle graceful shutdown
```

### Authentication Flow (`src/auth.py`)
```python
# OAuth2 implementation
1. Client connects to /sse with initial handshake
2. Server responds with auth_required and auth_url
3. User authenticates via HomeAssistant OAuth2
4. Token passed back to Claude Desktop
5. Subsequent requests include bearer token
6. Token refresh handled automatically
```

### Tool Registration (`src/tools/`)
Each tool module must:
- Inherit from `BaseTool` class
- Define `name`, `description`, and `parameters` schema
- Implement `execute()` method
- Handle errors gracefully
- Return structured responses

### HomeAssistant API Integration (`src/ha_api/`)
```python
# REST API client pattern
class HARestClient:
    - Token-based authentication
    - Automatic retry with exponential backoff
    - Rate limiting compliance
    - Response caching where appropriate
    
# WebSocket client pattern  
class HAWebSocketClient:
    - Persistent connection management
    - Event subscription handling
    - Real-time state updates
    - Automatic reconnection
```

## Security Implementation

### AppArmor Profile (`addon/apparmor.txt`)
```
#include <tunables/global>

profile homeassistant-mcp-server flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/python>
  
  # Network access
  network tcp,
  network inet stream,
  
  # File access (restricted)
  /data/** r,
  /config/** r,
  /ssl/** r,
  
  # Deny access to sensitive areas
  deny /root/** rwx,
  deny /etc/passwd r,
  deny /etc/shadow r,
}
```

### Security Best Practices
1. Never store tokens in plaintext
2. Use HTTPS exclusively for production
3. Implement rate limiting
4. Log security events
5. Validate all input
6. Sanitize YAML modifications
7. Use principle of least privilege

## Docker Configuration

### Multi-Architecture Dockerfile
```dockerfile
# Build stage for each architecture
ARG BUILD_FROM
FROM $BUILD_FROM AS builder

# Runtime stage
FROM $BUILD_FROM
ENV PYTHONUNBUFFERED=1
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt
COPY src/ /app/
WORKDIR /app
CMD ["python", "-m", "server"]
```

### Build Configuration (`addon/build.yaml`)
```yaml
build_from:
  amd64: "ghcr.io/home-assistant/amd64-base-python:3.12"
  aarch64: "ghcr.io/home-assistant/aarch64-base-python:3.12"
  armhf: "ghcr.io/home-assistant/armhf-base-python:3.12"
  armv7: "ghcr.io/home-assistant/armv7-base-python:3.12"
  i386: "ghcr.io/home-assistant/i386-base-python:3.12"
```

## GitHub Workflows

### Build Workflow (`.github/workflows/build.yml`)
- Triggers on push to main and PRs
- Builds all architectures in parallel
- Pushes to GitHub Container Registry
- Updates version tags

### Lint Workflow (`.github/workflows/lint.yml`)
- Python linting (ruff, black, mypy)
- YAML validation
- Dockerfile linting
- Add-on compliance check

### Test Workflow (`.github/workflows/test.yml`)
- Spins up HomeAssistant test instance
- Runs full test suite
- Generates coverage reports
- Posts results to PR

### Release Workflow (`.github/workflows/release.yml`)
- Triggers on version tags
- Creates GitHub release
- Updates changelog
- Publishes to add-on repository

## Testing Strategy

### Test HomeAssistant Instance (`tests/docker-compose.yml`)
```yaml
version: '3'
services:
  homeassistant:
    image: ghcr.io/home-assistant/home-assistant:stable
    volumes:
      - ./test_config:/config
    environment:
      - TZ=UTC
    ports:
      - "8123:8123"
```

### Test Coverage Requirements
- Unit tests: >80% coverage
- Integration tests: All API endpoints
- Authentication flow: Full coverage
- Tool execution: All tools tested
- Error handling: All error paths

## MCP Tools Implementation

### Available Tools

#### Entity Management
- `get_entities` - Query entities by domain, area, or attributes
- `get_entity_state` - Get current state and attributes
- `set_entity_state` - Update entity state
- `call_service` - Call any HomeAssistant service

#### Device Control
- `list_devices` - List all devices
- `get_device_info` - Get device details
- `control_device` - Send commands to devices
- `configure_device` - Update device configuration

#### Configuration Management
- `list_integrations` - Show installed integrations
- `add_integration` - Install new integration
- `configure_integration` - Modify integration settings
- `remove_integration` - Uninstall integration

#### Add-on Management
- `list_addons` - List installed add-ons
- `install_addon` - Install new add-on
- `start_addon` - Start add-on
- `stop_addon` - Stop add-on
- `configure_addon` - Update add-on config

#### Automation & Scenes
- `list_automations` - Show all automations
- `create_automation` - Create new automation
- `edit_automation` - Modify automation
- `trigger_automation` - Manually trigger
- `list_scenes` - Show all scenes
- `create_scene` - Create new scene
- `activate_scene` - Activate scene

#### YAML Configuration
- `read_yaml` - Read configuration file
- `edit_yaml` - Modify configuration
- `validate_yaml` - Check YAML syntax
- `reload_yaml` - Reload configuration

#### Dashboard Management
- `list_dashboards` - Show all dashboards
- `create_dashboard` - Create new dashboard
- `edit_dashboard` - Modify dashboard
- `add_card` - Add card to dashboard

## Configuration Schema

### Add-on Configuration (`addon/config.yaml`)
```yaml
name: "HomeAssistant MCP Server"
version: "1.0.0"
slug: "ha_mcp_server"
description: "MCP server for Claude Desktop integration with HomeAssistant"
arch:
  - amd64
  - aarch64
  - armhf
  - armv7
  - i386
startup: services
boot: auto
init: false
hassio_api: true
homeassistant_api: true
auth_api: true
ingress: true
ingress_port: 8089
ingress_entry: /sse
panel_icon: mdi:robot
panel_title: MCP Server
ports:
  8089/tcp: 8089
ports_description:
  8089/tcp: MCP SSE Server
options:
  log_level: info
  ssl: true
  certfile: fullchain.pem
  keyfile: privkey.pem
schema:
  log_level: list(debug|info|warning|error)
  ssl: bool
  certfile: str?
  keyfile: str?
apparmor: true
```

## Performance Optimization

### Resource Limits
- Memory: Max 128MB
- CPU: Max 10% single core
- Disk: Max 50MB storage
- Connections: Max 10 concurrent

### Optimization Strategies
1. Connection pooling for API requests
2. Response caching with TTL
3. Lazy loading of tools
4. Efficient SSE streaming
5. Minimal Docker image size

## Error Handling

### Error Categories
1. **Authentication Errors**: Return auth_required
2. **API Errors**: Retry with backoff
3. **Tool Errors**: Return error response
4. **Connection Errors**: Attempt reconnection
5. **Configuration Errors**: Log and fallback

### Logging Strategy
```python
# Structured logging
import structlog
logger = structlog.get_logger()

# Log levels by environment
DEBUG: All operations
INFO: Key operations and state changes
WARNING: Recoverable errors
ERROR: Failures requiring attention
```

## Release Process

### Version Bumping
1. Update VERSION in `src/constants.py`
2. Update version in `addon/config.yaml`
3. Update version in `repository.yaml`
4. Update CHANGELOG.md
5. Create git tag: `v1.0.0`
6. Push tag to trigger release

### Changelog Format
```markdown
## [1.0.0] - 2025-01-11
### Added
- Initial release
- SSE MCP server implementation
- OAuth2 authentication
- Full HomeAssistant API integration

### Changed
### Fixed
### Security
```

## Development Guidelines

### Code Style
- Python: Black formatting, ruff linting
- Type hints required for all functions
- Docstrings for all public methods
- Maximum line length: 100
- Import sorting: isort

### Commit Convention
```
type(scope): description

- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Test additions
- chore: Maintenance
```

### Pull Request Process
1. Create feature branch
2. Implement with tests
3. Run full test suite
4. Update documentation
5. Submit PR with description
6. Pass all CI checks
7. Obtain review approval

## Troubleshooting

### Common Issues
1. **Connection refused**: Check HomeAssistant URL and port
2. **Authentication failed**: Verify token permissions
3. **Tools not loading**: Check tool registry initialization
4. **SSL errors**: Verify certificate configuration
5. **Performance issues**: Check resource limits

### Debug Mode
```bash
# Enable debug logging
addon:
  options:
    log_level: debug

# View logs
docker logs addon_ha_mcp_server
```

## Maintenance Tasks

### Regular Updates
- [ ] Update base Docker images monthly
- [ ] Review and update dependencies
- [ ] Security vulnerability scanning
- [ ] Performance profiling
- [ ] Documentation updates

### Monitoring
- Connection count metrics
- Request/response times
- Error rates
- Memory usage
- API rate limit status

## Important Notes

1. **Never commit sensitive data** (tokens, passwords, keys)
2. **Always test locally** before pushing
3. **Maintain backwards compatibility** with HA versions
4. **Follow HomeAssistant add-on guidelines** strictly
5. **Respect rate limits** of HomeAssistant APIs
6. **Implement graceful degradation** for missing features
7. **Use structured logging** for debugging
8. **Document all API changes** in changelog
9. **Test on all architectures** before release
10. **Keep dependencies minimal** for security

## Quick Reference

### Key Files to Edit
- `src/server.py` - Main server logic
- `src/tools/*.py` - Add new tools here
- `addon/config.yaml` - Add-on configuration
- `src/constants.py` - Version management
- `.github/workflows/*.yml` - CI/CD pipelines

### Testing Checklist
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing on local HA
- [ ] Multi-architecture builds succeed
- [ ] Lint checks pass
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version bumped appropriately