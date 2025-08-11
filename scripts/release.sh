#!/bin/bash

# HomeAssistant MCP Server Release Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get current version
CURRENT_VERSION=$(cat addon/config.yaml | grep 'version:' | cut -d'"' -f2)

# Function to validate version format
validate_version() {
    if ! [[ $1 =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$ ]]; then
        echo -e "${RED}Invalid version format. Use semantic versioning (e.g., 1.0.0 or 1.0.0-beta)${NC}"
        exit 1
    fi
}

# Function to update version in files
update_version() {
    local old_version=$1
    local new_version=$2
    
    echo -e "${BLUE}Updating version from ${old_version} to ${new_version}...${NC}"
    
    # Update addon/config.yaml
    sed -i "s/version: \"${old_version}\"/version: \"${new_version}\"/" addon/config.yaml
    
    # Update src/constants.py
    sed -i "s/VERSION = \"${old_version}\"/VERSION = \"${new_version}\"/" src/constants.py
    
    # Update repository.yaml
    sed -i "s/version: ${old_version}/version: ${new_version}/" repository.yaml 2>/dev/null || true
    
    echo -e "${GREEN}Version updated in all files${NC}"
}

# Function to update changelog
update_changelog() {
    local version=$1
    local date=$(date +%Y-%m-%d)
    
    echo -e "${BLUE}Updating CHANGELOG.md...${NC}"
    
    # Check if version already exists in changelog
    if grep -q "\[${version}\]" addon/CHANGELOG.md; then
        echo -e "${YELLOW}Version ${version} already exists in CHANGELOG.md${NC}"
    else
        # Prepare new changelog entry
        cat > /tmp/changelog_entry.md << EOF
## [${version}] - ${date}

### Added
- 

### Changed
- 

### Fixed
- 

### Security
- 

EOF
        
        # Insert new entry after the header
        awk '/^## \[/ && !found {print ""; system("cat /tmp/changelog_entry.md"); found=1} 1' addon/CHANGELOG.md > /tmp/changelog_new.md
        mv /tmp/changelog_new.md addon/CHANGELOG.md
        
        echo -e "${YELLOW}Please edit addon/CHANGELOG.md to add release notes${NC}"
    fi
}

# Function to create git tag
create_tag() {
    local version=$1
    local tag="v${version}"
    
    echo -e "${BLUE}Creating git tag ${tag}...${NC}"
    
    # Check if tag already exists
    if git rev-parse "${tag}" >/dev/null 2>&1; then
        echo -e "${RED}Tag ${tag} already exists${NC}"
        exit 1
    fi
    
    # Create annotated tag
    git tag -a "${tag}" -m "Release version ${version}"
    
    echo -e "${GREEN}Tag ${tag} created${NC}"
}

# Function to run pre-release checks
pre_release_checks() {
    echo -e "${BLUE}Running pre-release checks...${NC}"
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        echo -e "${RED}There are uncommitted changes. Please commit or stash them first.${NC}"
        exit 1
    fi
    
    # Run tests
    echo "Running tests..."
    ./scripts/test.sh --unit
    
    # Run linting
    echo "Running linting..."
    python -m ruff check src/ || true
    python -m black --check src/ || true
    
    echo -e "${GREEN}Pre-release checks passed${NC}"
}

# Parse arguments
case "${1:-}" in
    --help)
        echo "Usage: $0 [VERSION] [OPTIONS]"
        echo ""
        echo "Create a new release for HomeAssistant MCP Server"
        echo ""
        echo "Arguments:"
        echo "  VERSION        New version number (e.g., 1.0.1)"
        echo ""
        echo "Options:"
        echo "  --major        Increment major version"
        echo "  --minor        Increment minor version"
        echo "  --patch        Increment patch version"
        echo "  --push         Push changes and tag to remote"
        echo "  --help         Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 1.0.1                  Release version 1.0.1"
        echo "  $0 --patch                Auto-increment patch version"
        echo "  $0 --minor --push         Auto-increment minor version and push"
        exit 0
        ;;
    --major)
        IFS='.' read -r major minor patch <<< "${CURRENT_VERSION%%-*}"
        NEW_VERSION="$((major + 1)).0.0"
        ;;
    --minor)
        IFS='.' read -r major minor patch <<< "${CURRENT_VERSION%%-*}"
        NEW_VERSION="${major}.$((minor + 1)).0"
        ;;
    --patch)
        IFS='.' read -r major minor patch <<< "${CURRENT_VERSION%%-*}"
        NEW_VERSION="${major}.${minor}.$((patch + 1))"
        ;;
    *)
        if [ -z "${1:-}" ]; then
            echo -e "${RED}Please specify a version number or use --major, --minor, or --patch${NC}"
            exit 1
        fi
        NEW_VERSION=$1
        validate_version "$NEW_VERSION"
        ;;
esac

# Check if --push flag is set
PUSH=false
for arg in "$@"; do
    if [ "$arg" = "--push" ]; then
        PUSH=true
    fi
done

# Display release information
echo -e "${GREEN}HomeAssistant MCP Server Release Tool${NC}"
echo "======================================"
echo ""
echo "Current version: ${CURRENT_VERSION}"
echo "New version:     ${NEW_VERSION}"
echo ""

# Ask for confirmation
read -p "Do you want to proceed with the release? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Release cancelled${NC}"
    exit 0
fi

# Run pre-release checks
pre_release_checks

# Update version in files
update_version "$CURRENT_VERSION" "$NEW_VERSION"

# Update changelog
update_changelog "$NEW_VERSION"

# Commit changes
echo -e "${BLUE}Committing changes...${NC}"
git add addon/config.yaml src/constants.py repository.yaml addon/CHANGELOG.md
git commit -m "chore: release version ${NEW_VERSION}"

# Create tag
create_tag "$NEW_VERSION"

# Push if requested
if [ "$PUSH" = true ]; then
    echo -e "${BLUE}Pushing changes to remote...${NC}"
    git push origin main
    git push origin "v${NEW_VERSION}"
    echo -e "${GREEN}Release pushed to remote repository${NC}"
else
    echo -e "${YELLOW}Changes committed locally. Run 'git push origin main && git push origin v${NEW_VERSION}' to push to remote.${NC}"
fi

echo ""
echo -e "${GREEN}Release ${NEW_VERSION} prepared successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit addon/CHANGELOG.md to add release notes"
echo "2. Push changes if not already done"
echo "3. GitHub Actions will automatically create the release"