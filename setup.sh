#!/bin/bash

# Claude Code Monitoring Setup Script
# Sets up proper virtual environment and dependencies

set -e  # Exit on any error

echo "🚀 Setting up Claude Code Monitoring environment..."

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed"  
    exit 1
fi

echo "✅ All prerequisites found"

# Create Python virtual environment
if [[ ! -d "venv" ]]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Node.js dependencies  
echo "📦 Installing Node.js dependencies..."
npm install

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/*.sh
chmod +x hooks/*.sh
chmod +x tools/*.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Start monitoring: just setup"  
echo "3. Deploy hooks: just deploy hooks"
echo "4. Test Linear sync: ./scripts/linear-sync.sh"
echo ""
echo "📚 Documentation: docs/INDEX.md"