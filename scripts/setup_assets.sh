#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "Setting up Isaac Sim assets..."

# ----------------
MESHES_FILE_ID="1e1PoO8-AqFTrluMp00KKuDM571hzYc5Y"
TEXTURES_FILE_ID="1O-vC3MNV52-uPZXQF_7bQVNI4keG62T7"

MESHES_ZIP="meshes.zip"
TEXTURES_ZIP="textures.zip"

# -----------------------

if ! command -v gdown &> /dev/null
then
    echo " Installing gdown..."
    pip install gdown
fi

mkdir -p sim_assets/meshes
mkdir -p sim_assets/textures

if [ -z "$(ls -A sim_assets/meshes 2>/dev/null)" ]; then
    echo "Downloading meshes..."
    gdown https://drive.google.com/uc?id=$MESHES_FILE_ID -O $MESHES_ZIP

    echo "Extracting meshes..."
    unzip -o $MESHES_ZIP -d sim_assets/meshes

    rm $MESHES_ZIP
else
    echo "Meshes already exist, skipping..."
fi

if [ -z "$(ls -A sim_assets/textures 2>/dev/null)" ]; then
    echo "Downloading textures..."
    gdown https://drive.google.com/uc?id=$TEXTURES_FILE_ID -O $TEXTURES_ZIP

    echo "Extracting textures..."
    unzip -o $TEXTURES_ZIP -d sim_assets/textures

    rm $TEXTURES_ZIP
else
    echo "Textures already exist, skipping..."
fi

echo "All assets ready! you can open hubble.usd in Isaac sim !!!"