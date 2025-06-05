#!/bin/bash

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Conda is not installed or not in the PATH. Please install Conda and try again."
    exit 1
fi

# Activate the conda environment
eval "$(conda shell.bash hook)"
conda activate stemlight

# Check if the environment activation was successful
if [ $? -ne 0 ]; then
    echo "Failed to activate the Conda environment 'stemlight'. Please ensure it exists and try again."
    exit 1
fi

# Optional: extract version if needed
# version=$(python3 -c "from src.Assets.version import version; print(version)")

# Run PyInstaller
pyinstaller \
--add-data "src/Images/*:src/Images" \
--add-data "src/Assets/*:src/Assets" \
--icon="src/Assets/icon.ico" \
--name "Stemlight for Linux" \
--windowed \
Main_Menu.py

# Check if PyInstaller was successful
if [ $? -ne 0 ]; then
    echo "PyInstaller build failed. Exiting."
    exit 1
fi

# Compress the output directory
cd dist || exit 1
zip -r "Stemlight_for_Linux.zip" "Stemlight for Linux"

# Check if compression was successful
if [ $? -ne 0 ]; then
    echo "Compression failed. Exiting."
    exit 1
fi

echo "Build and compression completed successfully."
