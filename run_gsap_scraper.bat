@echo off
setlocal enabledelayedexpansion
:: ============================================================================
:: GSAP Documentation Scraper - Automated Setup & Execution Script
:: ============================================================================
:: This script will:
:: 1. Create a virtual environment named 'taret'
:: 2. Install required dependencies (auto-discovers requirements.txt)
:: 3. Navigate to the extraction directory (auto-discovers script location)
:: 4. Run the GSAP batch scraper
:: ============================================================================

echo.
echo ========================================================================
echo    🚀 GSAP Documentation Scraper - Automated Setup
echo ========================================================================
echo.

:: Set variables
set VENV_NAME=taret
set PROJECT_DIR=%~dp0
set EXTRACTION_DIR=
set REQUIREMENTS_FILE=
set SCRIPT_TO_RUN=gsap_batch_scraper_sequential.py

:: Change to project directory
cd /d "%PROJECT_DIR%"
echo 📁 Working directory: %PROJECT_DIR%

:: Auto-discover requirements.txt file
echo 🔍 Searching for requirements.txt file...
if exist "%PROJECT_DIR%requirements.txt" (
    set REQUIREMENTS_FILE=%PROJECT_DIR%requirements.txt
    echo ✅ Found: %REQUIREMENTS_FILE%
) else (
    for /f "delims=" %%i in ('dir /s /b "%PROJECT_DIR%requirements.txt" 2^>nul') do (
        set REQUIREMENTS_FILE=%%i
        echo ✅ Found: %%i
        goto :found_req
    )
    echo ⚠️  No requirements.txt found anywhere
)
:found_req

:: Auto-discover extraction directory (look for the Python script)
echo 🔍 Searching for %SCRIPT_TO_RUN%...
for /f "delims=" %%i in ('dir /s /b "%PROJECT_DIR%%SCRIPT_TO_RUN%" 2^>nul') do (
    for %%j in ("%%i") do set EXTRACTION_DIR=%%~dpj
    echo ✅ Found script in: !EXTRACTION_DIR!
    goto :found_script
)
echo ❌ Could not find %SCRIPT_TO_RUN% anywhere in the project
pause
exit /b 1
:found_script

echo.

:: Check if virtual environment already exists
if exist "%VENV_NAME%" (
    echo ✅ Virtual environment '%VENV_NAME%' already exists
    echo 🔄 Activating existing environment...
) else (
    echo 🏗️  Creating virtual environment '%VENV_NAME%'...
    python -m venv %VENV_NAME%
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        echo 💡 Make sure Python is installed and added to PATH
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created successfully
)

:: Activate virtual environment
echo 🔌 Activating virtual environment...
call "%VENV_NAME%\Scripts\activate.bat"
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

:: Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip

:: Install requirements
echo 📋 Installing requirements...

:: Install from discovered requirements file or fallback to manual installation
if defined REQUIREMENTS_FILE (
    if exist "%REQUIREMENTS_FILE%" (
        echo 📋 Installing from: %REQUIREMENTS_FILE%
        pip install -r "%REQUIREMENTS_FILE%"
    ) else (
        echo ⚠️  Requirements file path invalid, installing core dependencies...
        pip install crawl4ai>=0.7.2 openai>=1.0.0 google-generativeai>=0.8.0
    )
) else (
    echo 📦 Installing core dependencies manually...
    pip install crawl4ai>=0.7.2 openai>=1.0.0 google-generativeai>=0.8.0
)

if errorlevel 1 (
    echo ❌ Failed to install requirements
    pause
    exit /b 1
)
echo ✅ Requirements installed successfully

:: Navigate to extraction directory
echo 📂 Navigating to extraction directory...
cd /d "!EXTRACTION_DIR!"
if errorlevel 1 (
    echo ❌ Failed to navigate to extraction directory: !EXTRACTION_DIR!
    pause
    exit /b 1
)
echo ✅ Current directory: !EXTRACTION_DIR!

:: Check if script exists
if not exist "%SCRIPT_TO_RUN%" (
    echo ❌ Script not found: %SCRIPT_TO_RUN%
    echo 📁 Available files in current directory:
    dir /b *.py
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo    🎯 Starting GSAP Documentation Scraping Process
echo ========================================================================
echo.
echo 📍 Script: %SCRIPT_TO_RUN%
echo 📁 Output: Will be saved in Gsap_Docs/ directory
echo ⏱️  Estimated time: 2-5 minutes depending on network speed
echo.

:: Ask user confirmation
set /p confirm="🤔 Ready to start scraping? (y/n): "
if /i not "%confirm%"=="y" (
    echo ⏹️  Operation cancelled by user
    pause
    exit /b 0
)

echo.
echo 🚀 Starting scraper...
echo ⏳ Please wait while we extract GSAP documentation...
echo.

:: Run the script
python "%SCRIPT_TO_RUN%"

:: Check if script ran successfully
if errorlevel 1 (
    echo.
    echo ❌ Script execution failed
    echo 💡 Check the error messages above for details
) else (
    echo.
    echo ========================================================================
    echo    🎉 SCRAPING COMPLETED SUCCESSFULLY!
    echo ========================================================================
    echo.
    echo ✅ GSAP documentation has been scraped
    echo 📁 Files saved in: !EXTRACTION_DIR!\Gsap_Docs\
    echo 📋 Check the summary report for detailed results
    echo 💡 Next step: Use the refined processing scripts for LLM cleanup
    echo.
    
    :: List generated files
    if exist "Gsap_Docs" (
        echo 📄 Generated files:
        dir "Gsap_Docs\*.txt" /b 2>nul
        echo.
    )
)

echo.
echo ========================================================================
echo    📝 AUTOMATION COMPLETE
echo ========================================================================
echo.
echo 🔧 Virtual environment: %VENV_NAME% (stays activated)
echo 📂 Working directory: !EXTRACTION_DIR!
echo 💡 You can now run other scripts in this environment
echo.
echo Press any key to exit...
pause >nul
