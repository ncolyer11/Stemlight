@echo off

:: Loop through each line in requirements.txt
for /F "tokens=*" %%A in (requirements.txt) do (
    :: Check if line starts with #
    echo %%A | findstr /b "#" >nul
    if errorlevel 1 (
        pip install %%A
        :: Check if pip install was successful
        IF ERRORLEVEL 1 (
            echo "Error: Failed to install %%A."
        )
    )
)

:: for /f "delims=" %%i in ('python -c "from src.Assets.version import version; print(version)"') do (
::    set version=%%i
:: )

pyinstaller --onefile ^
--add-data "src/images/*;src/images" ^
--add-data "src/assets/*;src/assets" ^
--icon="src/assets/icon.ico" ^
--name "Windows_Stemlight" ^
Main_Menu.py

::--name "Stemlight%version%" ^