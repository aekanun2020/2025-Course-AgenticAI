#!/bin/bash
# Run RAGDocs with Conda environment

# Source conda.sh to get conda command
source "$(conda info --base)/etc/profile.d/conda.sh"

# Activate the environment
conda activate ragdocs

# Run the server
python -m ragdocs.server "$@"
