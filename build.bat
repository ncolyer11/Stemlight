@echo off

:: Check if conda is available
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo "Conda is not installed or not in the PATH. Please install Conda and try again."
    exit /b 1
)

:: Activate the Anaconda environment
CALL conda activate stemlight

:: Check if the environment activation was successful
if %errorlevel% neq 0 (
    echo "Failed to activate the Conda environment 'stemlight'. Please ensure it exists and try again."
    exit /b 1
)

:: Build with PyInstaller
pyinstaller ^
--add-data "src/images/*;src/images" ^
--add-data "src/assets/*;src/assets" ^
--icon="src/assets/icon.ico" ^
--name "Stemlight for Windows" ^
--windowed ^
Main_Menu.py

:: Check if PyInstaller was successful
if %errorlevel% neq 0 (
    echo "PyInstaller build failed. Exiting."
    exit /b 1
)

:: Compress the output folder
powershell Compress-Archive -Path 'dist\\Stemlight for Windows\\*' -Force -DestinationPath 'Stemlight for Windows.zip'

:: Check if compression was successful
if %errorlevel% neq 0 (
    echo "Compression failed. Exiting."
    exit /b 1
)

echo "Build and compression completed successfully."