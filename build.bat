@echo off

pyinstaller ^
--add-data "src/images/*;src/images" ^
--add-data "src/assets/*;src/assets" ^
--icon="src/assets/icon.ico" ^
--name "Stemlight for Windows" ^
--windowed ^
Main_Menu.py

powershell Compress-Archive -Path 'dist\\Stemlight for Windows\\*' -Force -DestinationPath 'Stemlight for Windows.zip'