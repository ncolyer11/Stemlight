@echo off

for /f "delims=" %%i in ('python -c "from src.Assets.version import version; print(version)"') do (
    set version=%%i
)

pyinstaller --onefile ^
--add-data "src/images/*;src/images" ^
--add-data "src/assets/*;src/assets" ^
--icon="src/assets/icon.ico" ^
--name "Stemlight%version%" ^
Main_Menu.py