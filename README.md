# HomeAssistant MCP Server Add-on

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![Build Status][build-shield]][build]
[![Test Coverage][coverage-shield]][coverage]

[![Supports amd64 Architecture][amd64-shield]][amd64]
[![Supports aarch64 Architecture][aarch64-shield]][aarch64]
[![Supports armhf Architecture][armhf-shield]][armhf]
[![Supports armv7 Architecture][armv7-shield]][armv7]
[![Supports i386 Architecture][i386-shield]][i386]

[![Add to my Home Assistant][my-ha-shield]][my-ha]

MCP (Model Context Protocol) server add-on for HomeAssistant that enables Claude Desktop to interact with your HomeAssistant instance through its native Connections capability.

## Features

- 🔐 **Secure OAuth2 Authentication** - Uses HomeAssistant's native authentication system
- 🏠 **Locally Hosted** - Runs directly on your HomeAssistant device
- 🚀 **Zero Configuration** - Simple installation with minimal setup required
- 🔧 **Comprehensive Control** - Full access to HomeAssistant functionality through MCP tools
- 🌍 **Multi-Architecture Support** - Works on all common HomeAssistant hardware
- ☁️ **Cloud Compatible** - Works with Nabu Casa/HomeAssistant Cloud
- 🛡️ **AppArmor Protected** - Enhanced security with AppArmor profile

## Installation

### Method 1: Add Repository to HomeAssistant

1. Open your HomeAssistant instance
2. Navigate to **Settings** → **Add-ons** → **Add-on Store**
3. Click the three dots menu (⋮) → **Repositories**
4. Add this repository URL: `https://github.com/mtebusi/ha-mcp-v2`
5. Click **Add**
6. Find "HomeAssistant MCP Server" in the add-on store and click **Install**

### Method 2: One-Click Install

[![Add to my Home Assistant][my-ha-shield]][my-ha]

Click the button above to automatically add this repository to your HomeAssistant instance.

## Configuration

### HomeAssistant Add-on Configuration

The add-on requires minimal configuration:

```yaml
log_level: info  # Options: debug, info, warning, error
ssl: true        # Enable SSL/TLS
certfile: fullchain.pem  # SSL certificate file (optional)
keyfile: privkey.pem     # SSL key file (optional)
```

### Claude Desktop Setup

1. Start the HomeAssistant MCP Server add-on
2. Open Claude Desktop
3. Go to **Settings** → **Connections** → **Add Custom Connection**
4. Enter your HomeAssistant URL with `/sse` appended:
   - Local: `https://homeassistant.local:8089/sse`
   - Cloud: `https://YOUR-NABU-CASA-URL/sse`
5. Complete the OAuth2 authentication flow
6. The MCP tools will be automatically loaded

## Available MCP Tools

The add-on provides 7 powerful core tools with branched operations:

### 🎮 `ha_control`
Universal control for entities, devices, and services
- Get/set entity states
- Call services
- Control devices
- Manage areas
- Fire events

### ⚙️ `ha_config`
Configuration and YAML management
- Read/write YAML files
- Validate configuration
- Reload components
- View logs

### 🤖 `ha_automation`
Automation, script, and scene management
- Create/edit automations
- Manage scripts
- Control scenes
- Trigger automations

### 🔌 `ha_integration`
Integration and add-on management
- Install/remove integrations
- Manage add-ons
- Configure components

### 📊 `ha_dashboard`
Dashboard and UI management
- Create/edit dashboards
- Manage cards
- Control themes
- Configure panels

### 🖥️ `ha_system`
System operations and diagnostics
- Restart HomeAssistant
- Create/restore backups
- View diagnostics
- Database maintenance

### 📝 `ha_template`
Template and helper management
- Render templates
- Create input helpers
- Manage counters/timers

## Development

### Prerequisites

- Python 3.12+
- Docker (for testing)
- HomeAssistant instance (for testing)

### Local Development

```bash
# Clone the repository
git clone https://github.com/mtebusi/ha-mcp-v2.git
cd ha-mcp-v2

# Install dependencies
pip install -r src/requirements.txt

# Run locally (requires HomeAssistant instance)
python -m src.server --debug --ha-url http://localhost:8123 --ha-token YOUR_TOKEN

# Run tests
./scripts/test.sh
```

### Building the Add-on

```bash
# Build for local architecture
./scripts/build.sh --arch amd64

# Build all architectures
./scripts/build.sh --all
```

### Testing

```bash
# Start test environment
docker-compose -f tests/docker-compose.yml up -d

# Run tests
pytest tests/ -v

# Stop test environment
docker-compose -f tests/docker-compose.yml down
```

## Architecture

The add-on uses a Server-Sent Events (SSE) based MCP server that:
1. Runs as a HomeAssistant add-on with supervisor integration
2. Exposes an SSE endpoint at `/sse` for Claude Desktop connections
3. Handles OAuth2 authentication flow with HomeAssistant
4. Provides MCP tools that interact with HomeAssistant's REST and WebSocket APIs
5. Maintains secure, persistent connections with automatic reconnection

## Security

- **AppArmor Profile**: Restricts file system access and capabilities
- **OAuth2 Authentication**: Uses HomeAssistant's native auth system
- **TLS/SSL Support**: Encrypted connections when configured
- **Token Management**: Secure token storage and refresh
- **Rate Limiting**: Prevents API abuse
- **Input Validation**: All inputs are validated and sanitized

## Troubleshooting

### Connection Issues

If Claude Desktop cannot connect:
1. Verify the add-on is running: Check add-on logs
2. Check the URL format: Must end with `/sse`
3. Ensure SSL certificates are valid if using HTTPS
4. Verify firewall allows port 8089

### Authentication Issues

If authentication fails:
1. Check HomeAssistant user permissions
2. Verify OAuth2 redirect URL is accessible
3. Clear browser cookies and retry
4. Check add-on logs for auth errors

### Tool Execution Issues

If tools fail to execute:
1. Verify HomeAssistant API is accessible
2. Check user has required permissions
3. Review add-on logs for errors
4. Ensure HomeAssistant version compatibility

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

- **Issues**: [GitHub Issues](https://github.com/mtebusi/ha-mcp-v2/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mtebusi/ha-mcp-v2/discussions)
- **Documentation**: [Wiki](https://github.com/mtebusi/ha-mcp-v2/wiki)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- HomeAssistant community for the amazing platform
- Anthropic for Claude and the MCP protocol
- Contributors and testers

---

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[aarch64]: https://github.com/mtebusi/ha-mcp-v2/blob/main/addon/config.yaml
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[amd64]: https://github.com/mtebusi/ha-mcp-v2/blob/main/addon/config.yaml
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armhf]: https://github.com/mtebusi/ha-mcp-v2/blob/main/addon/config.yaml
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[armv7]: https://github.com/mtebusi/ha-mcp-v2/blob/main/addon/config.yaml
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
[i386]: https://github.com/mtebusi/ha-mcp-v2/blob/main/addon/config.yaml
[build-shield]: https://github.com/mtebusi/ha-mcp-v2/workflows/Build%20Multi-Architecture/badge.svg
[build]: https://github.com/mtebusi/ha-mcp-v2/actions/workflows/build.yml
[coverage-shield]: https://codecov.io/gh/mtebusi/ha-mcp-v2/branch/main/graph/badge.svg
[coverage]: https://codecov.io/gh/mtebusi/ha-mcp-v2
[commits-shield]: https://img.shields.io/github/commit-activity/y/mtebusi/ha-mcp-v2.svg
[commits]: https://github.com/mtebusi/ha-mcp-v2/commits/main
[license-shield]: https://img.shields.io/github/license/mtebusi/ha-mcp-v2.svg
[releases-shield]: https://img.shields.io/github/release/mtebusi/ha-mcp-v2.svg
[releases]: https://github.com/mtebusi/ha-mcp-v2/releases
[my-ha-shield]: https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg
[my-ha]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmtebusi%2Fha-mcp-v2