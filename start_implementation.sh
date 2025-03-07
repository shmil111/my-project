#!/bin/bash
# Bash script to start the implementation of the 10-step security plan
# Script: start_implementation.sh

# Display header
echo "===================================================="
echo "   MyProject Security Implementation Starter"
echo "===================================================="
echo ""

# Check Python installation
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Python detected: $PYTHON_VERSION"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
    PYTHON_VERSION=$(python --version)
    echo "✓ Python detected: $PYTHON_VERSION"
else
    echo "✗ Python not found. Please install Python before continuing."
    exit 1
fi

# Check if pip is installed
if command -v pip3 &>/dev/null; then
    PIP_CMD="pip3"
    PIP_VERSION=$(pip3 --version)
    echo "✓ pip detected: $PIP_VERSION"
elif command -v pip &>/dev/null; then
    PIP_CMD="pip"
    PIP_VERSION=$(pip --version)
    echo "✓ pip detected: $PIP_VERSION"
else
    echo "✗ pip not found. Please install pip before continuing."
    exit 1
fi

# Install required packages
echo -e "\nInstalling required packages..."
$PIP_CMD install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "✗ Failed to install required packages. Please check the error message above."
    exit 1
fi
echo "✓ Required packages installed successfully."

# Check for .env file in the project directory
if [ -f "./.env" ]; then
    echo "✓ .env file found in the project directory."
else
    echo "Creating .env file from example template..."
    if [ -f "./.env.example" ]; then
        cp ./.env.example ./.env
        echo "✓ .env file created. Please update it with your actual credentials."
    else
        echo "✗ .env.example file not found. Creating minimal .env file..."
        echo "API_KEY=your_api_key_here" > ./.env
        echo "SECRET_KEY=your_secret_key_here" >> ./.env
        echo "✓ Minimal .env file created. Please update it with your actual credentials."
    fi
fi

# Create directories for step 1
echo -e "\nSetting up directories for Step 1: Core Infrastructure Setup..."
directories=("./logs" "./data" "./config" "./secrets")

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "✓ Created directory: $dir"
    else
        echo "✓ Directory already exists: $dir"
    fi
done

# Create a sample logging config file
LOGGING_CONFIG_FILE="./config/logging_config.json"
if [ ! -f "$LOGGING_CONFIG_FILE" ]; then
    cat > "$LOGGING_CONFIG_FILE" << 'EOL'
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
EOL
    echo "✓ Created logging configuration file: $LOGGING_CONFIG_FILE"
else
    echo "✓ Logging configuration file already exists: $LOGGING_CONFIG_FILE"
fi

# Set execution permissions for the scripts
chmod +x ./manage_implementation.py

# Initialize the implementation management script
echo -e "\nInitializing implementation management..."
$PYTHON_CMD ./manage_implementation.py show

# Display next steps
echo -e "\n===================================================="
echo "   Next Steps"
echo "===================================================="
echo "1. Update your .env file with actual credentials"
echo "2. Start working on Step 1: Core Infrastructure Setup"
echo "3. Track your progress with the management script:"
echo "   - $PYTHON_CMD ./manage_implementation.py show"
echo "   - $PYTHON_CMD ./manage_implementation.py step 1"
echo "   - $PYTHON_CMD ./manage_implementation.py update 1 in_progress"
echo "   - $PYTHON_CMD ./manage_implementation.py note 1 'Started working on API authentication'"
echo "   - $PYTHON_CMD ./manage_implementation.py report"
echo -e "\nGood luck with your implementation!" 