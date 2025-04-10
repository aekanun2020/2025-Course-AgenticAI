#!/bin/bash
# Script for installing RAGDocs

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== RAGDocs Installer =====${NC}"
echo -e "This will install RAGDocs for use with Claude Desktop\n"

# Check Python version
python_version=$(python --version 2>&1)
if [[ "$python_version" == *"Python 3"* ]]; then
    echo -e "${GREEN}Found Python: ${python_version}${NC}"
else
    echo -e "${RED}Python 3.10 or higher is required but '${python_version}' was found.${NC}"
    echo -e "Please install Python 3.10+ and try again."
    exit 1
fi

# Check if virtualenv should be used
read -p "Do you want to create a virtual environment? (recommended) [Y/n]: " create_venv
create_venv=${create_venv:-Y}

if [[ "$create_venv" =~ ^[Yy]$ ]]; then
    echo -e "\n${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
    
    # Activate virtual environment
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    echo -e "${GREEN}Virtual environment activated.${NC}"
fi

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Install RAGDocs package
echo -e "\n${YELLOW}Installing RAGDocs package...${NC}"
pip install -e .

# Detect OS and configure Claude Desktop
echo -e "\n${YELLOW}Configuring Claude Desktop...${NC}"

if [[ "$OSTYPE" == "darwin"* ]]; then
    config_file="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    logs_dir="$HOME/Library/Logs/Claude"
    echo -e "OS detected: macOS"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    config_file="$APPDATA\\Claude\\claude_desktop_config.json"
    logs_dir="$APPDATA\\Claude\\logs"
    echo -e "OS detected: Windows"
else
    config_file="$HOME/.config/Claude/claude_desktop_config.json"
    logs_dir="$HOME/.local/share/Claude/logs"
    echo -e "OS detected: Linux"
fi

echo -e "Claude config file: ${config_file}"
echo -e "\n${YELLOW}You need to update your Claude Desktop configuration.${NC}"
echo -e "Add the following to your claude_desktop_config.json file:"
echo -e "${GREEN}"
cat << 'EOT'
{
  "mcpServers": {
    "ragdocs": {
      "command": "python",
      "args": [
        "-m",
        "ragdocs.server"
      ],
      "env": {
        "QDRANT_URL": "http://localhost:6333",
        "EMBEDDING_PROVIDER": "ollama",
        "OLLAMA_URL": "http://localhost:11434"
      }
    }
  }
}
EOT
echo -e "${NC}"

# Check for Qdrant and Ollama
echo -e "\n${YELLOW}Checking for required services...${NC}"

qdrant_running=false
ollama_running=false

if curl -s http://localhost:6333/health > /dev/null; then
    echo -e "${GREEN}✓ Qdrant server appears to be running on http://localhost:6333${NC}"
    qdrant_running=true
else
    echo -e "${RED}✗ Qdrant server does not appear to be running on http://localhost:6333${NC}"
    echo -e "   You'll need to install and start Qdrant before using RAGDocs"
    echo -e "   Visit: https://qdrant.tech/documentation/guides/installation/"
fi

if curl -s http://localhost:11434/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama server appears to be running on http://localhost:11434${NC}"
    ollama_running=true
else
    echo -e "${RED}✗ Ollama server does not appear to be running on http://localhost:11434${NC}"
    echo -e "   You'll need to install and start Ollama before using RAGDocs"
    echo -e "   Visit: https://ollama.ai/download"
fi

echo -e "\n${GREEN}Installation complete!${NC}"
echo -e "\nTo use RAGDocs:"
echo -e "1. Make sure Qdrant and Ollama are running"
echo -e "2. Update your Claude Desktop configuration as shown above"
echo -e "3. Restart Claude Desktop"
echo -e "\nFor more details, see the INSTALL.md file."

exit 0
