ARG BUILD_FROM
FROM $BUILD_FROM

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Setup base system
RUN \
    apk add --no-cache \
        nginx \
        openssl

# Copy Python requirements
COPY requirements.txt /tmp/

# Install Python dependencies
RUN \
    pip3 install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

# Copy root filesystem
COPY rootfs /

# Copy application
COPY src /app

# Set working directory
WORKDIR /app

# Build arguments
ARG BUILD_ARCH
ARG BUILD_DATE
ARG BUILD_DESCRIPTION
ARG BUILD_NAME
ARG BUILD_REF
ARG BUILD_REPOSITORY
ARG BUILD_VERSION

# Labels
LABEL \
    io.hass.name="${BUILD_NAME}" \
    io.hass.description="${BUILD_DESCRIPTION}" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version=${BUILD_VERSION} \
    maintainer="mtebusi <mtebusi@example.com>" \
    org.opencontainers.image.title="${BUILD_NAME}" \
    org.opencontainers.image.description="${BUILD_DESCRIPTION}" \
    org.opencontainers.image.vendor="HomeAssistant MCP Server" \
    org.opencontainers.image.authors="mtebusi <mtebusi@example.com>" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.url="https://github.com/mtebusi/ha-mcp-v2" \
    org.opencontainers.image.source="https://github.com/mtebusi/ha-mcp-v2" \
    org.opencontainers.image.documentation="https://github.com/mtebusi/ha-mcp-v2/blob/main/README.md" \
    org.opencontainers.image.created=${BUILD_DATE} \
    org.opencontainers.image.revision=${BUILD_REF} \
    org.opencontainers.image.version=${BUILD_VERSION}