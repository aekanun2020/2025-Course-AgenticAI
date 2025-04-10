#!/bin/bash
# Build script for RAGDocs
# This script builds Python packages for distribution

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== RAGDocs Build Script =====${NC}"

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf build/ dist/ *.egg-info/

# Build the package
echo -e "${YELLOW}Building package...${NC}"
python -m pip install --upgrade build
python -m build

# Check results
if [ -d "dist" ]; then
    echo -e "${GREEN}Build successful! Files created:${NC}"
    ls -l dist/
else
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}Done!${NC}"
echo -e "To install the package: pip install dist/ragdocs-*.whl"
echo -e "To upload to PyPI: python -m twine upload dist/*"

exit 0
