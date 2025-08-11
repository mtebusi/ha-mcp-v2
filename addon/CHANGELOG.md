# Changelog

All notable changes to the HomeAssistant MCP Server add-on will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2025-01-11

### Added
- Initial release of HomeAssistant MCP Server add-on
- SSE-based MCP server implementation
- OAuth2 authentication with HomeAssistant
- Seven core MCP tools with branched operations:
  - `ha_control` - Universal entity and device control
  - `ha_config` - Configuration and YAML management
  - `ha_automation` - Automation, script, and scene management
  - `ha_integration` - Integration and add-on management
  - `ha_dashboard` - Dashboard and UI management
  - `ha_system` - System operations and diagnostics
  - `ha_template` - Template and helper management
- Multi-architecture support (amd64, aarch64, armhf, armv7, i386)
- AppArmor security profile
- SSL/TLS support for secure connections
- Automatic token refresh
- Connection state management
- Comprehensive error handling
- Structured logging with multiple log levels
- Rate limiting for API requests
- Response caching for improved performance
- Docker multi-stage builds
- GitHub Actions CI/CD pipelines
- Automated testing suite
- Dependency management with Dependabot

### Security
- Implemented OAuth2 authentication flow
- Added AppArmor security profile
- Enabled SSL/TLS encryption
- Input validation and sanitization
- Secure token storage
- Rate limiting protection

### Documentation
- Comprehensive README with installation guide
- Detailed DOCS.md for users
- CLAUDE.md for development guidance
- Inline code documentation
- API usage examples

[0.0.1]: https://github.com/mtebusi/ha-mcp-v2/releases/tag/v0.0.1