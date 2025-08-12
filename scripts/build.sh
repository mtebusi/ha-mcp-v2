#!/bin/bash

# HomeAssistant MCP Server Add-on Build Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ARCH=""
ALL_ARCHS="amd64 aarch64 armhf armv7 i386"
PUSH=false
TAG="latest"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --arch)
            ARCH="$2"
            shift 2
            ;;
        --all)
            ARCH="all"
            shift
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --arch ARCH    Build for specific architecture (amd64, aarch64, armhf, armv7, i386)"
            echo "  --all          Build for all architectures"
            echo "  --push         Push images to registry"
            echo "  --tag TAG      Docker image tag (default: latest)"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Validate architecture
if [ -z "$ARCH" ]; then
    echo -e "${YELLOW}No architecture specified, building for amd64${NC}"
    ARCH="amd64"
fi

# Function to build for a specific architecture
build_arch() {
    local arch=$1
    echo -e "${GREEN}Building for architecture: $arch${NC}"
    
    # Determine base image
    BASE_IMAGE="ghcr.io/home-assistant/${arch}-base-python:3.12-alpine"
    
    # Build arguments
    local BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    local BUILD_REF=$(git rev-parse --short HEAD)
    local BUILD_VERSION=$(cat addon/config.yaml | grep 'version:' | cut -d'"' -f2)
    
    # Image name
    IMAGE_NAME="ha-mcp-v2-${arch}:${TAG}"
    
    # Build command
    echo "Building ${IMAGE_NAME}..."
    docker build \
        --build-arg BUILD_FROM="${BASE_IMAGE}" \
        --build-arg BUILD_ARCH="${arch}" \
        --build-arg BUILD_DATE="${BUILD_DATE}" \
        --build-arg BUILD_REF="${BUILD_REF}" \
        --build-arg BUILD_VERSION="${BUILD_VERSION}" \
        --build-arg BUILD_NAME="HomeAssistant MCP Server" \
        --build-arg BUILD_DESCRIPTION="MCP server for Claude Desktop integration" \
        --build-arg BUILD_REPOSITORY="https://github.com/mtebusi/ha-mcp-v2" \
        -t "${IMAGE_NAME}" \
        -f addon/Dockerfile \
        addon/
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Successfully built ${IMAGE_NAME}${NC}"
        
        if [ "$PUSH" = true ]; then
            echo "Pushing ${IMAGE_NAME} to registry..."
            docker tag ${IMAGE_NAME} ghcr.io/mtebusi/${IMAGE_NAME}
            docker push ghcr.io/mtebusi/${IMAGE_NAME}
        fi
    else
        echo -e "${RED}Failed to build ${IMAGE_NAME}${NC}"
        exit 1
    fi
}

# Copy source files to addon directory for build
echo "Preparing build context..."
cp -r src/* addon/
cp src/requirements.txt addon/

# Build based on architecture selection
if [ "$ARCH" = "all" ]; then
    echo -e "${GREEN}Building for all architectures: ${ALL_ARCHS}${NC}"
    for arch in $ALL_ARCHS; do
        build_arch $arch
    done
else
    build_arch $ARCH
fi

# Clean up
echo "Cleaning up build context..."
rm -rf addon/*.py addon/tools addon/ha_api addon/mcp addon/requirements.txt

echo -e "${GREEN}Build complete!${NC}"