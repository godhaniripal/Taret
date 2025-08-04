# ============================================================================
# GSAP Documentation Scraper - Automated Setup & Execution Script (PowerShell)
# ============================================================================
# This script will:
# 1. Create a virtual environment named 'taret'
# 2. Install required dependencies
# 3. Navigate to the extraction directory
# 4. Run the GSAP batch scraper
# ============================================================================

Write-Host ""
Write-Host "========================================================================"
Write-Host "   🚀 GSAP Documentation Scraper - Automated Setup" -ForegroundColor Cyan
Write-Host "========================================================================"
Write-Host ""

# Set variables
$VenvName = "taret"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExtractionDir = Join-Path $ProjectDir "extraction"
$RequirementsFile = Join-Path $ProjectDir "requirements.txt"
$ScriptToRun = "gsap_batch_scraper_sequential.py"

# Change to project directory
Set-Location $ProjectDir
Write-Host "📁 Working directory: $ProjectDir" -ForegroundColor Green
Write-Host ""

# Check if virtual environment already exists
if (Test-Path $VenvName) {
    Write-Host "✅ Virtual environment '$VenvName' already exists" -ForegroundColor Green
    Write-Host "🔄 Activating existing environment..." -ForegroundColor Yellow
} else {
    Write-Host "🏗️  Creating virtual environment '$VenvName'..." -ForegroundColor Yellow
    try {
        python -m venv $VenvName
        Write-Host "✅ Virtual environment created successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        Write-Host "💡 Make sure Python is installed and added to PATH" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Activate virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Yellow
$ActivateScript = Join-Path $VenvName "Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    & $ActivateScript
} else {
    Write-Host "❌ Failed to find activation script" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Upgrade pip
Write-Host "📦 Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
Write-Host "📋 Installing requirements..." -ForegroundColor Yellow
if (Test-Path $RequirementsFile) {
    pip install -r $RequirementsFile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install requirements" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "✅ Requirements installed successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Requirements file not found, installing core dependencies..." -ForegroundColor Yellow
    pip install "crawl4ai>=0.7.2" "openai>=1.0.0" "google-generativeai>=0.8.0"
}

# Navigate to extraction directory
Write-Host "📂 Navigating to extraction directory..." -ForegroundColor Yellow
if (Test-Path $ExtractionDir) {
    Set-Location $ExtractionDir
    Write-Host "✅ Current directory: $ExtractionDir" -ForegroundColor Green
} else {
    Write-Host "❌ Extraction directory not found: $ExtractionDir" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if script exists
$ScriptPath = Join-Path $ExtractionDir $ScriptToRun
if (-not (Test-Path $ScriptPath)) {
    Write-Host "❌ Script not found: $ScriptToRun" -ForegroundColor Red
    Write-Host "📁 Available Python files in current directory:" -ForegroundColor Yellow
    Get-ChildItem -Filter "*.py" | ForEach-Object { Write-Host "   - $($_.Name)" }
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================================================"
Write-Host "   🎯 Starting GSAP Documentation Scraping Process" -ForegroundColor Cyan
Write-Host "========================================================================"
Write-Host ""
Write-Host "📍 Script: $ScriptToRun" -ForegroundColor White
Write-Host "📁 Output: Will be saved in Gsap_Docs/ directory" -ForegroundColor White
Write-Host "⏱️  Estimated time: 2-5 minutes depending on network speed" -ForegroundColor White
Write-Host ""

# Ask user confirmation
$confirm = Read-Host "🤔 Ready to start scraping? (y/n)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "⏹️  Operation cancelled by user" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 0
}

Write-Host ""
Write-Host "🚀 Starting scraper..." -ForegroundColor Green
Write-Host "⏳ Please wait while we extract GSAP documentation..." -ForegroundColor Yellow
Write-Host ""

# Run the script
python $ScriptToRun

# Check if script ran successfully
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================================================"
    Write-Host "   🎉 SCRAPING COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "========================================================================"
    Write-Host ""
    Write-Host "✅ GSAP documentation has been scraped" -ForegroundColor Green
    Write-Host "📁 Files saved in: $(Join-Path $ExtractionDir 'Gsap_Docs')" -ForegroundColor White
    Write-Host "📋 Check the summary report for detailed results" -ForegroundColor White
    Write-Host "💡 Next step: Use the refined processing scripts for LLM cleanup" -ForegroundColor Yellow
    Write-Host ""
    
    # List generated files
    $DocsDir = Join-Path $ExtractionDir "Gsap_Docs"
    if (Test-Path $DocsDir) {
        Write-Host "📄 Generated files:" -ForegroundColor White
        Get-ChildItem -Path $DocsDir -Filter "*.txt" | ForEach-Object { 
            Write-Host "   - $($_.Name)" -ForegroundColor Gray
        }
        Write-Host ""
    }
} else {
    Write-Host ""
    Write-Host "❌ Script execution failed" -ForegroundColor Red
    Write-Host "💡 Check the error messages above for details" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================================================"
Write-Host "   📝 AUTOMATION COMPLETE" -ForegroundColor Cyan
Write-Host "========================================================================"
Write-Host ""
Write-Host "🔧 Virtual environment: $VenvName (stays activated)" -ForegroundColor White
Write-Host "📂 Working directory: $ExtractionDir" -ForegroundColor White
Write-Host "💡 You can now run other scripts in this environment" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"
