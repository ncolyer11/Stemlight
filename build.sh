#!/bin/bash

while read requirement; do
    if [[ $requirement != \#* ]]; then
        pip install "$requirement" || true
    fi
done < requirements.txt

# version=$(python3 -c "from src.Assets.version import version; print(version)")

pyinstaller --onefile \
--add-data "src/Images/*:src/Images" \
--add-data "src/Assets/*:src/Assets" \
--name "Linux_Stemlight" \
Main_Menu.py

# --name "Stemlight$version" \