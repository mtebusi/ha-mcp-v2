#!/bin/bash

# HomeAssistant MCP Server Test Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="unit"
COVERAGE=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            TEST_TYPE="full"
            shift
            ;;
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --full         Run all tests (unit + integration)"
            echo "  --unit         Run unit tests only (default)"
            echo "  --integration  Run integration tests only"
            echo "  --coverage     Generate coverage report"
            echo "  --verbose, -v  Verbose output"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Function to check dependencies
check_dependencies() {
    echo -e "${BLUE}Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 is required but not installed${NC}"
        exit 1
    fi
    
    # Check Docker
    if [ "$TEST_TYPE" = "integration" ] || [ "$TEST_TYPE" = "full" ]; then
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}Docker is required for integration tests${NC}"
            exit 1
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            echo -e "${RED}Docker Compose is required for integration tests${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}Dependencies OK${NC}"
}

# Function to setup test environment
setup_environment() {
    echo -e "${BLUE}Setting up test environment...${NC}"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet -r src/requirements.txt
    pip install --quiet pytest pytest-asyncio pytest-cov pytest-timeout pytest-mock
    
    echo -e "${GREEN}Environment ready${NC}"
}

# Function to run unit tests
run_unit_tests() {
    echo -e "${BLUE}Running unit tests...${NC}"
    
    PYTEST_ARGS=""
    
    if [ "$VERBOSE" = true ]; then
        PYTEST_ARGS="${PYTEST_ARGS} -v"
    fi
    
    if [ "$COVERAGE" = true ]; then
        PYTEST_ARGS="${PYTEST_ARGS} --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml"
    fi
    
    # Run pytest
    pytest tests/test_*.py ${PYTEST_ARGS} --ignore=tests/test_integration.py
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Unit tests passed!${NC}"
    else
        echo -e "${RED}Unit tests failed!${NC}"
        exit 1
    fi
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${BLUE}Running integration tests...${NC}"
    
    # Start test environment
    echo "Starting test HomeAssistant instance..."
    docker-compose -f tests/docker-compose.yml up -d homeassistant
    
    # Wait for HomeAssistant to be ready
    echo "Waiting for HomeAssistant to start..."
    for i in {1..60}; do
        if curl -f http://localhost:8123/ &> /dev/null; then
            echo -e "${GREEN}HomeAssistant is ready${NC}"
            break
        fi
        
        if [ $i -eq 60 ]; then
            echo -e "${RED}HomeAssistant failed to start${NC}"
            docker-compose -f tests/docker-compose.yml logs homeassistant
            docker-compose -f tests/docker-compose.yml down
            exit 1
        fi
        
        sleep 2
    done
    
    # Start MCP server
    echo "Starting MCP server..."
    docker-compose -f tests/docker-compose.yml up -d mcp-server
    
    # Wait for MCP server
    sleep 5
    
    # Run integration tests
    PYTEST_ARGS=""
    
    if [ "$VERBOSE" = true ]; then
        PYTEST_ARGS="${PYTEST_ARGS} -v"
    fi
    
    if [ "$COVERAGE" = true ]; then
        PYTEST_ARGS="${PYTEST_ARGS} --cov=src --cov-report=term-missing"
    fi
    
    pytest tests/test_integration.py ${PYTEST_ARGS}
    TEST_RESULT=$?
    
    # Collect logs
    echo "Collecting logs..."
    docker-compose -f tests/docker-compose.yml logs > test-logs.txt
    
    # Stop test environment
    echo "Stopping test environment..."
    docker-compose -f tests/docker-compose.yml down
    
    if [ $TEST_RESULT -eq 0 ]; then
        echo -e "${GREEN}Integration tests passed!${NC}"
    else
        echo -e "${RED}Integration tests failed! Check test-logs.txt for details${NC}"
        exit 1
    fi
}

# Function to generate coverage report
generate_coverage_report() {
    if [ "$COVERAGE" = true ]; then
        echo -e "${BLUE}Coverage Report:${NC}"
        echo ""
        
        if [ -f "coverage.xml" ]; then
            python -m coverage report
            echo ""
            echo -e "${GREEN}HTML coverage report generated in htmlcov/${NC}"
            echo -e "${GREEN}XML coverage report generated as coverage.xml${NC}"
        fi
    fi
}

# Main execution
echo -e "${GREEN}HomeAssistant MCP Server Test Suite${NC}"
echo "======================================"
echo ""

# Check dependencies
check_dependencies

# Setup environment
setup_environment

# Run tests based on type
case $TEST_TYPE in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    full)
        run_unit_tests
        run_integration_tests
        ;;
esac

# Generate coverage report
generate_coverage_report

echo ""
echo -e "${GREEN}All tests completed successfully!${NC}"