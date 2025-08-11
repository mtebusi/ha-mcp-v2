# HomeAssistant MCP Server Documentation

## Overview

The HomeAssistant MCP Server add-on enables Claude Desktop to interact with your HomeAssistant instance using the Model Context Protocol (MCP). This provides a secure, locally-hosted connection that gives Claude access to comprehensive HomeAssistant control capabilities.

## Installation

### Prerequisites

- HomeAssistant OS, Supervised, or Container installation
- HomeAssistant version 2024.1.0 or later
- Claude Desktop application
- SSL certificates (optional, but recommended for remote access)

### Installation Steps

1. **Add the repository**:
   - Navigate to Settings → Add-ons → Add-on Store
   - Click ⋮ → Repositories
   - Add: `https://github.com/mtebusi/ha-mcp-v2`

2. **Install the add-on**:
   - Find "HomeAssistant MCP Server" in the store
   - Click Install
   - Wait for installation to complete

3. **Configure the add-on** (optional):
   - Adjust settings as needed
   - Default configuration works for most users

4. **Start the add-on**:
   - Click Start
   - Check logs to verify successful startup

## Configuration

### Add-on Options

```yaml
log_level: info        # Logging verbosity: debug, info, warning, error
ssl: true             # Enable HTTPS/WSS connections
certfile: fullchain.pem  # Path to SSL certificate (relative to /ssl/)
keyfile: privkey.pem    # Path to SSL private key (relative to /ssl/)
```

### SSL Configuration

For secure remote access:

1. **Using Let's Encrypt** (recommended):
   ```yaml
   ssl: true
   certfile: fullchain.pem
   keyfile: privkey.pem
   ```

2. **Using self-signed certificates**:
   - Generate certificates
   - Place in `/ssl/` directory
   - Update configuration with filenames

3. **Without SSL** (local only):
   ```yaml
   ssl: false
   ```

## Claude Desktop Connection

### Setup Process

1. **Start the add-on** in HomeAssistant

2. **Open Claude Desktop**

3. **Add MCP Connection**:
   - Go to Settings → Connections
   - Click "Add Custom Connection"
   - Enter your HomeAssistant URL with `/sse`:
     - Local: `http://homeassistant.local:8089/sse`
     - HTTPS: `https://your-domain.com:8089/sse`
     - Nabu Casa: `https://your-id.ui.nabu.casa/sse`

4. **Authenticate**:
   - Browser opens for OAuth2 flow
   - Log in to HomeAssistant
   - Authorize the connection
   - Return to Claude Desktop

5. **Verify Connection**:
   - Tools should appear in Claude's interface
   - Test with a simple command

### Connection URLs

| Setup Type | URL Format |
|------------|------------|
| Local HTTP | `http://homeassistant.local:8089/sse` |
| Local HTTPS | `https://homeassistant.local:8089/sse` |
| Remote HTTPS | `https://your-domain.com:8089/sse` |
| Nabu Casa | `https://your-id.ui.nabu.casa/sse` |
| IP Address | `http://192.168.1.100:8089/sse` |

## Available Tools

### ha_control

Universal control for entities, devices, and services.

**Operations:**
- `get_entities` - List all entities with optional filters
- `get_entity` - Get specific entity state
- `set_entity` - Update entity state
- `call_service` - Call any HomeAssistant service
- `get_devices` - List all devices
- `control_device` - Control device state
- `get_areas` - List all areas
- `create_area` - Create new area

**Example Usage:**
```
Turn on living room lights:
- Operation: call_service
- Target: light.turn_on
- Data: {"entity_id": "light.living_room"}
```

### ha_config

Configuration and YAML file management.

**Operations:**
- `read_yaml` - Read configuration files
- `write_yaml` - Modify configuration files
- `validate_yaml` - Check YAML syntax
- `reload_yaml` - Reload specific components
- `check_config` - Validate HomeAssistant configuration
- `get_logs` - View system logs

### ha_automation

Manage automations, scripts, and scenes.

**Operations:**
- `list_automations` - Show all automations
- `create_automation` - Create new automation
- `trigger_automation` - Manually trigger
- `list_scripts` - Show all scripts
- `run_script` - Execute script
- `list_scenes` - Show all scenes
- `activate_scene` - Activate scene

### ha_integration

Manage integrations and add-ons.

**Operations:**
- `list_integrations` - Show installed integrations
- `add_integration` - Install new integration
- `list_addons` - Show installed add-ons
- `install_addon` - Install new add-on
- `start_addon` - Start add-on
- `stop_addon` - Stop add-on

### ha_dashboard

Dashboard and UI management.

**Operations:**
- `list_dashboards` - Show all dashboards
- `create_dashboard` - Create new dashboard
- `add_card` - Add card to dashboard
- `list_themes` - Show available themes
- `set_theme` - Apply theme

### ha_system

System operations and maintenance.

**Operations:**
- `restart_ha` - Restart HomeAssistant
- `check_config` - Validate configuration
- `create_backup` - Create system backup
- `get_system_info` - Get system information
- `get_diagnostics` - Collect diagnostics
- `purge_database` - Clean up database

### ha_template

Template and helper entity management.

**Operations:**
- `render_template` - Execute Jinja2 template
- `list_helpers` - Show all helper entities
- `create_input_boolean` - Create toggle helper
- `create_input_number` - Create number helper
- `update_helper_value` - Update helper value

## Security

### Authentication

The add-on uses OAuth2 for authentication:
1. Initial connection requires browser-based auth
2. Tokens are securely stored
3. Automatic token refresh
4. Session management

### Permissions

The add-on respects HomeAssistant user permissions:
- Users can only access what they're authorized for
- Admin users have full access
- Limited users have restricted access

### Network Security

- **SSL/TLS**: Encrypted connections when enabled
- **AppArmor**: Sandboxed execution environment
- **Rate Limiting**: Prevents API abuse
- **Input Validation**: All inputs sanitized

## Troubleshooting

### Common Issues

#### Connection Refused
- Verify add-on is running
- Check port 8089 is accessible
- Ensure correct URL format

#### Authentication Failed
- Clear browser cookies
- Check user permissions
- Verify OAuth2 redirect

#### Tools Not Loading
- Restart add-on
- Check logs for errors
- Verify API access

#### SSL Certificate Errors
- Verify certificate paths
- Check certificate validity
- Ensure proper permissions

### Debugging

1. **Enable debug logging**:
   ```yaml
   log_level: debug
   ```

2. **Check logs**:
   - Add-on logs in Supervisor
   - HomeAssistant core logs
   - Browser console logs

3. **Test connectivity**:
   ```bash
   curl https://your-ha-instance:8089/health
   ```

### Getting Help

- **GitHub Issues**: Report bugs and request features
- **Community Forum**: Ask questions and share experiences
- **Documentation**: Check the wiki for detailed guides

## Advanced Configuration

### Custom SSL Certificates

1. Generate certificates:
   ```bash
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   ```

2. Place in `/ssl/` directory

3. Update configuration:
   ```yaml
   ssl: true
   certfile: cert.pem
   keyfile: key.pem
   ```

### Proxy Configuration

For reverse proxy setups:

1. **NGINX Example**:
   ```nginx
   location /sse {
       proxy_pass http://localhost:8089;
       proxy_http_version 1.1;
       proxy_set_header Connection '';
       proxy_buffering off;
       proxy_cache off;
   }
   ```

2. **Traefik Example**:
   ```yaml
   http:
     routers:
       mcp:
         rule: "PathPrefix(`/sse`)"
         service: mcp-server
     services:
       mcp-server:
         loadBalancer:
           servers:
             - url: "http://localhost:8089"
   ```

### Performance Tuning

Optimize for your setup:

```yaml
# For high-traffic environments
log_level: warning  # Reduce logging overhead

# For development
log_level: debug    # Maximum verbosity
```

## FAQ

**Q: Can I use this without SSL?**
A: Yes, but only for local connections. SSL is required for remote access.

**Q: How many concurrent connections are supported?**
A: The add-on supports up to 10 concurrent connections.

**Q: Does this work with Nabu Casa?**
A: Yes, it's fully compatible with HomeAssistant Cloud/Nabu Casa.

**Q: Can multiple users connect simultaneously?**
A: Yes, each user gets their own authenticated session.

**Q: Is this compatible with all HomeAssistant installations?**
A: It works with HomeAssistant OS, Supervised, and Container installations.

## Updates

The add-on updates automatically when new versions are released. To manually update:

1. Navigate to the add-on page
2. Click "Check for updates"
3. If available, click "Update"
4. Restart the add-on after updating

## Support

For issues or questions:
- **GitHub Issues**: https://github.com/mtebusi/ha-mcp-v2/issues
- **Documentation**: https://github.com/mtebusi/ha-mcp-v2/wiki
- **Community**: HomeAssistant Community Forum