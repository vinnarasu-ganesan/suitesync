#!/usr/bin/env python3
"""
Setup script for SuiteSync application.
This script helps set up the development environment.
"""

import os
import sys
import subprocess


def run_command(command, description):
    """Run a shell command and print status."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print('='*60)

    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, check=True, capture_output=True, text=True)

        if result.stdout:
            print(result.stdout)

        print(f"✓ {description} completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {e}")
        if e.stderr:
            print(e.stderr)
        return False


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("✗ Python 3.9 or higher is required")
        return False

    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def check_git_installed():
    """Check if Git is installed."""
    try:
        subprocess.run(['git', '--version'], check=True, capture_output=True)
        print("✓ Git is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Git is not installed. Please install Git first.")
        return False


def create_directories():
    """Create necessary directories."""
    dirs = ['repos', 'logs', 'static/css', 'static/js', 'templates']

    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

    print("✓ Created necessary directories")
    return True


def setup():
    """Main setup function."""
    print("\n" + "="*60)
    print("  SuiteSync - Setup Script")
    print("="*60)

    # Check prerequisites
    if not check_python_version():
        return False

    if not check_git_installed():
        return False

    # Create directories
    if not create_directories():
        return False

    # Install requirements
    if not run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python dependencies"
    ):
        return False

    # Check if .env exists
    if not os.path.exists('.env'):
        print("\n⚠ .env file not found. Please create one from .env.example")
        print("  cp .env.example .env")
        print("  Then edit .env with your configuration")
    else:
        print("✓ .env file exists")

    print("\n" + "="*60)
    print("  Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Edit .env file with your configuration (TestRail credentials, etc.)")
    print("2. Run the application: python app.py")
    print("3. Open browser to: http://localhost:5000")
    print("\nFor more information, see README.md")

    return True


if __name__ == '__main__':
    try:
        success = setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)

