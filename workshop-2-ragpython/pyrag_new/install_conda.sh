#!/bin/bash
# Script for installing RAGDocs with Conda

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== RAGDocs Conda Installer =====${NC}"
echo -e "This will install RAGDocs using Conda for use with Claude Desktop\n"

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo -e "${RED}Conda could not be found. Please install Conda first.${NC}"
    echo -e "Visit: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Get conda info
conda_info=$(conda info)
echo -e "${GREEN}Conda is installed:${NC}"
echo "$conda_info" | grep -E "conda version|conda-build version|python version" | sed 's/^/  /'

# Check if environment should be created
read -p "Enter name for Conda environment (default: ragdocs): " env_name
env_name=${env_name:-ragdocs}

# Check if environment exists
if conda env list | grep -q "^$env_name "; then
    read -p "Environment '$env_name' already exists. Do you want to use it? [Y/n]: " use_existing
    use_existing=${use_existing:-Y}
    
    if [[ "$use_existing" =~ ^[Yy]$ ]]; then
        echo -e "\n${YELLOW}Using existing Conda environment '$env_name'...${NC}"
    else
        read -p "Do you want to remove it and create a new one? [y/N]: " recreate
        recreate=${recreate:-N}
        
        if [[ "$recreate" =~ ^[Yy]$ ]]; then
            echo -e "\n${YELLOW}Removing existing Conda environment '$env_name'...${NC}"
            conda env remove -n $env_name
            echo -e "\n${YELLOW}Creating new Conda environment '$env_name'...${NC}"
            conda create -y -n $env_name python=3.10
        else
            echo -e "\n${RED}Installation cancelled.${NC}"
            exit 0
        fi
    fi
else
    echo -e "\n${YELLOW}Creating Conda environment '$env_name'...${NC}"
    conda create -y -n $env_name python=3.10
fi

# Activate environment
echo -e "\n${YELLOW}Activating Conda environment '$env_name'...${NC}"
# Use eval to handle conda activate in script
eval "$(conda shell.bash hook)"
conda activate $env_name

# Check if activation was successful
if [[ "$CONDA_DEFAULT_ENV" != "$env_name" ]]; then
    echo -e "${RED}Failed to activate Conda environment '$env_name'.${NC}"
    exit 1
fi

echo -e "${GREEN}Conda environment '$env_name' activated.${NC}"

# Current directory
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Install dependencies with conda or pip as needed
echo -e "\n${YELLOW}Installing dependencies...${NC}"
# Try to install with conda first, fallback to pip for packages not in conda
conda install -y -c conda-forge python-dotenv aiohttp beautifulsoup4 pymupdf || true
pip install -r $CURRENT_DIR/requirements.txt

# Install RAGDocs package
echo -e "\n${YELLOW}Installing RAGDocs package...${NC}"
pip install -e $CURRENT_DIR

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

# Get full path to conda python
CONDA_PYTHON=$(which python)
echo -e "\n${GREEN}Using Conda Python: ${CONDA_PYTHON}${NC}"

echo -e "\n${YELLOW}You need to update your Claude Desktop configuration.${NC}"
echo -e "Add the following to your claude_desktop_config.json file:"
echo -e "${GREEN}"
cat << EOT
{
  "mcpServers": {
    "ragdocs": {
      "command": "${CONDA_PYTHON}",
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

# Create a conda activation script
echo -e "\n${YELLOW}Creating run script with Conda activation...${NC}"
cat > $CURRENT_DIR/run_conda.sh << EOT
#!/bin/bash
# Run RAGDocs with Conda environment

# Source conda.sh to get conda command
source "\$(conda info --base)/etc/profile.d/conda.sh"

# Activate the environment
conda activate ${env_name}

# Run the server
python -m ragdocs.server "\$@"
EOT

chmod +x $CURRENT_DIR/run_conda.sh
echo -e "${GREEN}Created run_conda.sh script to run RAGDocs with Conda environment${NC}"

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
echo -e "   NOTE: Make sure to use the full path to the Conda Python interpreter"
echo -e "3. Restart Claude Desktop"
echo -e "\nAlternatively, you can run RAGDocs with the run_conda.sh script"
echo -e "For more details, see the INSTALL.md and README_CONDA.md files"

exit 0
