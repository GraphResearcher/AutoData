#!/bin/bash

# AutoData Setup Script
# Automated installation and configuration

set -e  # Exit on error

echo "======================================"
echo "AutoData - Setup Script"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $python_version"

if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
    echo -e "${RED}❌ Python 3.9+ is required${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python version OK${NC}"
echo ""

# Check if Ollama is installed
echo "🔍 Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✅ Ollama is installed${NC}"

    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${GREEN}✅ Ollama is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Ollama is not running. Starting Ollama...${NC}"
        ollama serve &
        sleep 5
    fi
else
    echo -e "${RED}❌ Ollama is not installed${NC}"
    echo "   Please install Ollama from: https://ollama.com/download"
    exit 1
fi
echo ""

# Pull required models
echo "📥 Pulling required Ollama models..."
echo "   This may take a while..."

if ollama list | grep -q "llama3.1:8b"; then
    echo -e "${GREEN}✅ llama3.1:8b already exists${NC}"
else
    echo "   Pulling llama3.1:8b..."
    ollama pull llama3.1:8b
fi

if ollama list | grep -q "nomic-embed-text"; then
    echo -e "${GREEN}✅ nomic-embed-text already exists${NC}"
else
    echo "   Pulling nomic-embed-text..."
    ollama pull nomic-embed-text
fi
echo ""

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo ""

# Install requirements
echo "📚 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi
echo ""

# Create .env file
echo "⚙️  Setting up configuration..."
if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file already exists, skipping...${NC}"
else
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created${NC}"
    echo -e "${YELLOW}   Please edit .env file to customize settings${NC}"
fi
echo ""

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/pdfs data/csv data/vector_db logs
echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Check Chrome/Chromium for Selenium
echo "🌐 Checking Chrome/Chromium for Selenium..."
if command -v google-chrome &> /dev/null || command -v chromium-browser &> /dev/null || command -v chromium &> /dev/null; then
    echo -e "${GREEN}✅ Chrome/Chromium found${NC}"
else
    echo -e "${YELLOW}⚠️  Chrome/Chromium not found${NC}"
    echo "   Selenium features may not work. Install with:"
    echo "   Ubuntu/Debian: sudo apt-get install chromium-browser chromium-chromedriver"
    echo "   Mac: brew install chromium"
fi
echo ""

# Test configuration
echo "🧪 Testing configuration..."
python3 -c "from core.config import config; config.validate_config()" && \
    echo -e "${GREEN}✅ Configuration valid${NC}" || \
    echo -e "${RED}❌ Configuration validation failed${NC}"
echo ""

# Summary
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. (Optional) Edit .env file to customize settings:"
echo "   nano .env"
echo ""
echo "3. Run the system:"
echo "   python main.py"
echo ""
echo "4. For help:"
echo "   python main.py --help"
echo ""
echo "======================================"
echo "Happy crawling! 🚀"
echo "======================================"