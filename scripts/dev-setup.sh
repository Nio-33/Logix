#!/bin/bash

# Logix Platform - Development Setup Script

set -e

echo "🚚 Setting up Logix Platform for development..."

# Check if Python 3.13 is available
if ! command -v python3.13 &> /dev/null; then
    echo "❌ Python 3.13 is required but not installed."
    echo "Please install Python 3.13 and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.13 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your actual configuration values"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p tests/fixtures
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/frontend

# Set up pre-commit hooks (if available)
if command -v pre-commit &> /dev/null; then
    echo "🔗 Setting up pre-commit hooks..."
    pre-commit install
fi

# Run tests to verify setup
echo "🧪 Running tests to verify setup..."
python -m pytest tests/ -v --tb=short

echo "✅ Development setup complete!"
echo ""
echo "To start the development server:"
echo "  source venv/bin/activate"
echo "  python backend/app.py"
echo ""
echo "To run tests:"
echo "  python -m pytest"
echo ""
echo "To run linting:"
echo "  flake8 backend/"
echo "  black backend/"