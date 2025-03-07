#!/usr/bin/env python3
"""
Cross-platform script for common platform-specific operations.
This script is designed to replace multiple platform-specific scripts
(.sh, .bat, .ps1) with a single Python script that works on all platforms.
"""
import os
import sys
import json
import argparse
import logging
import platform
import subprocess
import shutil
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Detect platform
PLATFORM = platform.system().lower()
IS_WINDOWS = PLATFORM == 'windows'
IS_LINUX = PLATFORM == 'linux'
IS_MACOS = PLATFORM == 'darwin'

# Script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Project root directory
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
# Data directory
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
# Configuration directory
CONFIG_DIR = os.path.join(PROJECT_ROOT, 'config')

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

def load_config(config_name: str = 'default') -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_name: Name of the configuration file (without extension)
        
    Returns:
        Configuration dictionary
    """
    config_path = os.path.join(CONFIG_DIR, f"{config_name}.json")
    
    # Create default config if it doesn't exist
    if not os.path.exists(config_path):
        default_config = {
            'platform_specific': {
                'windows': {
                    'commands': {
                        'setup': 'setup.bat',
                        'update': 'update.bat',
                        'run': 'run.bat'
                    },
                    'paths': {
                        'python': 'python',
                        'npm': 'npm'
                    }
                },
                'linux': {
                    'commands': {
                        'setup': './setup.sh',
                        'update': './update.sh',
                        'run': './run.sh'
                    },
                    'paths': {
                        'python': 'python3',
                        'npm': 'npm'
                    }
                },
                'darwin': {
                    'commands': {
                        'setup': './setup.sh',
                        'update': './update.sh',
                        'run': './run.sh'
                    },
                    'paths': {
                        'python': 'python3',
                        'npm': 'npm'
                    }
                }
            },
            'common': {
                'environment': {
                    'DEBUG': 'false',
                    'LOG_LEVEL': 'info'
                },
                'paths': {
                    'data': 'data',
                    'logs': 'logs'
                }
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"Created default configuration at {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        logger.debug(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

def get_platform_config() -> Dict[str, Any]:
    """
    Get platform-specific configuration.
    
    Returns:
        Platform-specific configuration dictionary
    """
    config = load_config()
    
    platform_config = config.get('platform_specific', {}).get(PLATFORM, {})
    if not platform_config:
        logger.warning(f"No configuration found for platform {PLATFORM}, using defaults")
        platform_config = {}
    
    common_config = config.get('common', {})
    
    # Merge platform-specific and common config
    merged_config = {**common_config, **platform_config}
    
    return merged_config

def run_command(command: str, cwd: str = None, env: Dict[str, str] = None) -> int:
    """
    Run a command in a subprocess.
    
    Args:
        command: Command to run
        cwd: Working directory (or None for current directory)
        env: Environment variables (or None for current environment)
        
    Returns:
        Exit code of the command
    """
    if not cwd:
        cwd = os.getcwd()
    
    if not env:
        env = os.environ.copy()
    
    logger.info(f"Running command: {command}")
    
    try:
        # On Windows, use shell=True to run batch files
        process = subprocess.Popen(
            command,
            shell=IS_WINDOWS,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Stream output
        for line in process.stdout:
            print(line.strip())
        
        # Wait for process to complete
        process.wait()
        
        # Check for errors
        if process.returncode != 0:
            stderr = process.stderr.read()
            logger.error(f"Command failed with exit code {process.returncode}: {stderr}")
        
        return process.returncode
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return 1

def setup(args: argparse.Namespace) -> int:
    """
    Set up the project.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code
    """
    logger.info("Setting up project...")
    
    config = get_platform_config()
    env = os.environ.copy()
    
    # Add common environment variables
    if 'environment' in config:
        for key, value in config['environment'].items():
            env[key] = value
    
    # Python setup
    if args.with_python:
        logger.info("Setting up Python environment...")
        
        python_cmd = config.get('paths', {}).get('python', 'python3')
        
        # Install requirements
        requirements_path = os.path.join(PROJECT_ROOT, 'requirements.txt')
        if os.path.exists(requirements_path):
            cmd = f"{python_cmd} -m pip install -r {requirements_path}"
            if run_command(cmd, cwd=PROJECT_ROOT, env=env) != 0:
                return 1
    
    # Node.js setup
    if args.with_node:
        logger.info("Setting up Node.js environment...")
        
        npm_cmd = config.get('paths', {}).get('npm', 'npm')
        
        # Install dependencies
        package_json_path = os.path.join(PROJECT_ROOT, 'package.json')
        if os.path.exists(package_json_path):
            cmd = f"{npm_cmd} install"
            if run_command(cmd, cwd=PROJECT_ROOT, env=env) != 0:
                return 1
    
    # Create directories
    for dir_name in ['data', 'logs']:
        dir_path = os.path.join(PROJECT_ROOT, config.get('paths', {}).get(dir_name, dir_name))
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
    
    # Initialize security module
    if args.with_security:
        logger.info("Initializing security module...")
        
        try:
            sys.path.append(PROJECT_ROOT)
            import security
            security.initialize()
        except ImportError:
            logger.error("Security module not found")
        except Exception as e:
            logger.error(f"Error initializing security module: {e}")
            return 1
    
    # Run platform-specific setup
    if args.platform_specific:
        logger.info("Running platform-specific setup...")
        
        setup_cmd = config.get('commands', {}).get('setup')
        if setup_cmd:
            if run_command(setup_cmd, cwd=PROJECT_ROOT, env=env) != 0:
                return 1
    
    logger.info("Setup completed successfully")
    return 0

def update(args: argparse.Namespace) -> int:
    """
    Update the project.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code
    """
    logger.info("Updating project...")
    
    config = get_platform_config()
    env = os.environ.copy()
    
    # Add common environment variables
    if 'environment' in config:
        for key, value in config['environment'].items():
            env[key] = value
    
    # Python update
    if args.with_python:
        logger.info("Updating Python environment...")
        
        python_cmd = config.get('paths', {}).get('python', 'python3')
        
        # Update requirements
        requirements_path = os.path.join(PROJECT_ROOT, 'requirements.txt')
        if os.path.exists(requirements_path):
            cmd = f"{python_cmd} -m pip install -r {requirements_path} --upgrade"
            if run_command(cmd, cwd=PROJECT_ROOT, env=env) != 0:
                return 1
    
    # Node.js update
    if args.with_node:
        logger.info("Updating Node.js environment...")
        
        npm_cmd = config.get('paths', {}).get('npm', 'npm')
        
        # Update dependencies
        package_json_path = os.path.join(PROJECT_ROOT, 'package.json')
        if os.path.exists(package_json_path):
            cmd = f"{npm_cmd} update"
            if run_command(cmd, cwd=PROJECT_ROOT, env=env) != 0:
                return 1
    
    # Run platform-specific update
    if args.platform_specific:
        logger.info("Running platform-specific update...")
        
        update_cmd = config.get('commands', {}).get('update')
        if update_cmd:
            if run_command(update_cmd, cwd=PROJECT_ROOT, env=env) != 0:
                return 1
    
    logger.info("Update completed successfully")
    return 0

def run(args: argparse.Namespace) -> int:
    """
    Run the project.
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code
    """
    logger.info("Running project...")
    
    config = get_platform_config()
    env = os.environ.copy()
    
    # Add common environment variables
    if 'environment' in config:
        for key, value in config['environment'].items():
            env[key] = value
    
    # Use run command from config or default to Python app.py
    run_cmd = config.get('commands', {}).get('run')
    if not run_cmd:
        python_cmd = config.get('paths', {}).get('python', 'python3')
        run_cmd = f"{python_cmd} app.py"
    
    # Run the command
    return run_command(run_cmd, cwd=PROJECT_ROOT, env=env)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Cross-platform script for common operations')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Set up the project')
    setup_parser.add_argument('--with-python', action='store_true', help='Set up Python environment')
    setup_parser.add_argument('--with-node', action='store_true', help='Set up Node.js environment')
    setup_parser.add_argument('--with-security', action='store_true', help='Initialize security module')
    setup_parser.add_argument('--platform-specific', action='store_true', help='Run platform-specific setup')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update the project')
    update_parser.add_argument('--with-python', action='store_true', help='Update Python environment')
    update_parser.add_argument('--with-node', action='store_true', help='Update Node.js environment')
    update_parser.add_argument('--platform-specific', action='store_true', help='Run platform-specific update')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run the project')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run command
    if args.command == 'setup':
        return setup(args)
    elif args.command == 'update':
        return update(args)
    elif args.command == 'run':
        return run(args)
    else:
        parser.print_help()
        return 1

if __name__ == '__main__':
    sys.exit(main()) 