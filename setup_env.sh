#!/bin/bash
# HyperTrail Virtual Environment Setup Script
# This script creates an isolated Python environment using your pyenv installation

set -e

echo "=== HyperTrail Setup Script ==="
echo ""

# Check if pyenv is available
if ! command -v pyenv &> /dev/null; then
    echo "❌ Error: pyenv not found. Please install pyenv first."
    exit 1
fi

# Check for Python version we need (3.12.9)
echo "🔍 Checking Python installation..."

PYENV_ROOT=$(command -v pyenv | sed 's|/bin/pyenv||' | xargs readlink -f)
INSTALLED_VERSIONS=$(${PYENV_ROOT}/versions 2>/dev/null || echo "")

if [[ "$INSTALLED_VERSIONS" == *"3.12.9"* ]] || [[ "$INSTALLED_VERSIONS" == *"3.12.8"* ]]; then
    echo "✅ Python version found!"
else
    echo "⚠️  Recommended Python versions: 3.12.8 or 3.12.9"
    echo "Your installed:"
    echo "$INSTALLED_VERSIONS"
    echo ""
    read -p "Continue with current Python? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Install required version first: pyenv install 3.12.9"
        exit 1
    fi
fi

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python -m venv .venv
echo "✅ Virtual environment created at .venv/"

# Activate and upgrade pip
echo ""
echo "🔧 Upgrading pip, setuptools, wheel..."
source .venv/bin/activate
pip install --upgrade pip setuptools wheel

# Install project dependencies
echo ""
echo "📦 Installing project dependencies..."
pip install -r requirements.txt

# Configure pyenv for this project
echo ""
echo "⚙️  Configuring pyenv Python version..."
pyenv local 3.12.9

# Set up .env file from template
if [ ! -f .env ]; then
    echo ""
    echo "📝 Setting up .env configuration..."
    cp .env.example .env
    echo "   Created .env from .env.example"
else
    echo "   ℹ️  .env already exists, skipping"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your Hyperliquid API credentials"
echo "2. Activate the environment: source .venv/bin/activate"
echo "3. Run the application: python app.py"
echo ""
