#!/bin/bash
# Development run script for WidgetBoard

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}WidgetBoard Development Runner${NC}"
echo "================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3.11 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/update dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Run tests
if [ "$1" == "test" ]; then
    echo -e "${GREEN}Running tests...${NC}"
    python -m unittest discover tests
    exit 0
fi

# Run application
echo -e "${GREEN}Starting WidgetBoard...${NC}"
python -m app.main

deactivate
