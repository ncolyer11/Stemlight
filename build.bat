@echo off

:: Activate the Anaconda environment
CALL conda activate Stemlight

:: Build with PyInstaller
pyinstaller ^
--add-data "src/images/*;src/images" ^
--add-data "src/assets/*;src/assets" ^
--icon="src/assets/icon.ico" ^
--name "Stemlight for Windows" ^
--windowed ^
Main_Menu.py

:: Compress the output folder
powershell Compress-Archive -Path 'dist\\Stemlight for Windows\\*' -Force -DestinationPath 'Stemlight for Windows.zip'

:: Deactivate the environment
CALL conda deactivate
