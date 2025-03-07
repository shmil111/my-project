# PowerShell script to start the implementation of the 10-step security plan
# Script: start_implementation.ps1

# Display header
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   MyProject Security Implementation Starter" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
try {
    $pythonVersion = (python --version 2>&1).ToString()
    Write-Host "✓ Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python before continuing." -ForegroundColor Red
    exit 1
}

# Check if pip is installed
try {
    $pipVersion = (pip --version 2>&1).ToString()
    Write-Host "✓ pip detected: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ pip not found. Please install pip before continuing." -ForegroundColor Red
    exit 1
}

# Function to check if a package is installed
function Check-PythonPackage {
    param (
        [string]$PackageName
    )
    
    $installed = pip list | Select-String -Pattern "^$PackageName "
    return $installed -ne $null
}

# Install required packages
Write-Host "`nInstalling required packages..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install required packages. Please check the error message above." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Required packages installed successfully." -ForegroundColor Green

# Check for .env file in the project directory
$envExists = Test-Path ".\.env"
if ($envExists) {
    Write-Host "✓ .env file found in the project directory." -ForegroundColor Green
} else {
    Write-Host "Creating .env file from example template..." -ForegroundColor Yellow
    if (Test-Path ".\.env.example") {
        Copy-Item ".\.env.example" -Destination ".\.env"
        Write-Host "✓ .env file created. Please update it with your actual credentials." -ForegroundColor Green
    } else {
        Write-Host "✗ .env.example file not found. Creating minimal .env file..." -ForegroundColor Yellow
        "API_KEY=your_api_key_here" | Out-File -FilePath ".\.env" -Encoding utf8
        "SECRET_KEY=your_secret_key_here" | Out-File -FilePath ".\.env" -Encoding utf8 -Append
        Write-Host "✓ Minimal .env file created. Please update it with your actual credentials." -ForegroundColor Green
    }
}

# Create directories for step 1
Write-Host "`nSetting up directories for Step 1: Core Infrastructure Setup..." -ForegroundColor Yellow
$directories = @(
    ".\logs",
    ".\data",
    ".\config",
    ".\secrets"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "✓ Created directory: $dir" -ForegroundColor Green
    } else {
        Write-Host "✓ Directory already exists: $dir" -ForegroundColor Green
    }
}

# Create a sample logging config file
$loggingConfigContent = @"
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": {
    "standard": {
      "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    }
  },
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "level": "INFO",
      "formatter": "standard",
      "stream": "ext://sys.stdout"
    },
    "file": {
      "class": "logging.handlers.RotatingFileHandler",
      "level": "DEBUG",
      "formatter": "standard",
      "filename": "./logs/security.log",
      "maxBytes": 10485760,
      "backupCount": 10,
      "encoding": "utf8"
    }
  },
  "loggers": {
    "": {
      "handlers": ["console", "file"],
      "level": "DEBUG",
      "propagate": true
    }
  }
}
"@

$loggingConfigFile = ".\config\logging_config.json"
if (-not (Test-Path $loggingConfigFile)) {
    $loggingConfigContent | Out-File -FilePath $loggingConfigFile -Encoding utf8
    Write-Host "✓ Created logging configuration file: $loggingConfigFile" -ForegroundColor Green
} else {
    Write-Host "✓ Logging configuration file already exists: $loggingConfigFile" -ForegroundColor Green
}

# Initialize the implementation management script
Write-Host "`nInitializing implementation management..." -ForegroundColor Yellow
python manage_implementation.py show

# Display next steps
Write-Host "`n====================================================" -ForegroundColor Cyan
Write-Host "   Next Steps" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "1. Update your .env file with actual credentials"
Write-Host "2. Start working on Step 1: Core Infrastructure Setup"
Write-Host "3. Track your progress with the management script:"
Write-Host "   - python manage_implementation.py show"
Write-Host "   - python manage_implementation.py step 1"
Write-Host "   - python manage_implementation.py update 1 in_progress"
Write-Host "   - python manage_implementation.py note 1 'Started working on API authentication'"
Write-Host "   - python manage_implementation.py report"
Write-Host "`nGood luck with your implementation!" -ForegroundColor Green 