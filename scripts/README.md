# Cross-Platform Scripts

This directory contains scripts to simplify operations across different platforms.

## Overview

The `cross_platform.py` script replaces multiple platform-specific scripts (`.sh`, `.bat`, `.ps1`) with a single Python script that works on all platforms. This approach has several benefits:

- **Unified codebase**: Maintain a single script instead of separate scripts for each platform
- **Configuration-driven**: Use JSON configuration files to customize behavior
- **Extensible**: Easy to add new operations or modify existing ones
- **Cross-platform**: Works on Windows, macOS, and Linux

## Usage

### Basic Commands

```bash
# Setup the project
python scripts/cross_platform.py setup --with-python --with-node --with-security

# Update the project
python scripts/cross_platform.py update --with-python --with-node

# Run the project
python scripts/cross_platform.py run
```

### Setup Options

- `--with-python`: Set up Python environment (install dependencies)
- `--with-node`: Set up Node.js environment (install dependencies)
- `--with-security`: Initialize security module
- `--platform-specific`: Run platform-specific setup scripts

### Update Options

- `--with-python`: Update Python environment (upgrade dependencies)
- `--with-node`: Update Node.js environment (upgrade dependencies)
- `--platform-specific`: Run platform-specific update scripts

## Configuration

The script uses JSON configuration files to customize its behavior. The configuration files are stored in the `config` directory.

### Default Configuration

```json
{
  "platform_specific": {
    "windows": {
      "commands": {
        "setup": "setup.bat",
        "update": "update.bat",
        "run": "run.bat"
      },
      "paths": {
        "python": "python",
        "npm": "npm"
      }
    },
    "linux": {
      "commands": {
        "setup": "./setup.sh",
        "update": "./update.sh",
        "run": "./run.sh"
      },
      "paths": {
        "python": "python3",
        "npm": "npm"
      }
    },
    "darwin": {
      "commands": {
        "setup": "./setup.sh",
        "update": "./update.sh",
        "run": "./run.sh"
      },
      "paths": {
        "python": "python3",
        "npm": "npm"
      }
    }
  },
  "common": {
    "environment": {
      "DEBUG": "false",
      "LOG_LEVEL": "info"
    },
    "paths": {
      "data": "data",
      "logs": "logs"
    }
  }
}
```

You can customize this configuration by editing the `config/default.json` file.

## How It Works

The script works by:

1. **Detecting the platform**: Windows, macOS, or Linux
2. **Loading configuration**: From `config/default.json` or creating it if it doesn't exist
3. **Executing commands**: Based on the command line arguments and configuration

### Platform-Specific Commands

For advanced operations that still require platform-specific scripts, the script can delegate to platform-specific scripts specified in the configuration. For example, if you run:

```bash
python scripts/cross_platform.py setup --platform-specific
```

On Windows, it will execute `setup.bat`, and on Linux/macOS, it will execute `setup.sh`.

## Benefits Over Separate Scripts

- **Avoid Duplication**: No need to duplicate logic across multiple platform-specific scripts
- **Centralized Configuration**: All configuration in one place
- **Consistent Interface**: Same command line interface across all platforms
- **Easier Maintenance**: Update one script instead of multiple scripts
- **Better Error Handling**: Consistent error handling and logging across all platforms

## Future Improvements

- Add more commands for common operations
- Add support for environment-specific configurations (development, testing, production)
- Add support for container environments
- Add support for cloud environments 