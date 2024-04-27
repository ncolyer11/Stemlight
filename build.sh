#!/bin/bash

while read requirement; do
    pip install "$requirement" || true
done < requirements.txt

# version=$(python3 -c "from src.Assets.version import version; print(version)")

pyinstaller --onefile \
--add-data "src/Images/*:src/Images" \
--add-data "src/Assets/*:src/Assets" \
--icon="src/Assets/icon.ico" \
# --name "Stemlight$version" \
--name "Stemlight" \
Main_Menu.py