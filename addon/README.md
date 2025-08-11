# HomeAssistant MCP Server Add-on

MCP (Model Context Protocol) server that enables Claude Desktop to interact with your HomeAssistant instance.

## About

This add-on provides a secure, locally-hosted MCP server that allows Claude Desktop to connect to your HomeAssistant instance. It uses OAuth2 authentication and provides comprehensive control through seven powerful tools.

## Features

- 🔐 Secure OAuth2 authentication
- 🏠 Runs locally on your HomeAssistant device  
- 🚀 Zero-configuration setup
- 🔧 Full HomeAssistant control
- 🌍 Multi-architecture support
- ☁️ Compatible with Nabu Casa
- 🛡️ AppArmor security

## Quick Start

1. Install the add-on
2. Start the add-on
3. Open Claude Desktop
4. Add connection: `https://your-ha-instance:8089/sse`
5. Complete authentication
6. Start using MCP tools!

## Configuration

```yaml
log_level: info
ssl: true
certfile: fullchain.pem
keyfile: privkey.pem
```

## Available Tools

- **ha_control** - Control entities, devices, and services
- **ha_config** - Manage configuration and YAML files
- **ha_automation** - Create and manage automations
- **ha_integration** - Manage integrations and add-ons
- **ha_dashboard** - Customize dashboards and UI
- **ha_system** - System operations and maintenance
- **ha_template** - Template rendering and helpers

## Support

For detailed documentation, see the [DOCS](./DOCS.md) tab.

For issues or questions, visit our [GitHub repository](https://github.com/mtebusi/ha-mcp-v2).